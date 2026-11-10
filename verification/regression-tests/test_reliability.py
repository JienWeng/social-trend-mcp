from datetime import datetime,timedelta
import os,pytest


def test_freshness_detects_stale_and_failed_snapshots():
    from app.services.trend_service import freshness
    from app.models import ScrapeSnapshot,ScrapeStatus
    snapshot=ScrapeSnapshot(status=ScrapeStatus.SUCCESS,started_at=datetime.now()-timedelta(days=3),finished_at=datetime.now()-timedelta(days=3))
    assert freshness(snapshot)['state']=='stale'
    snapshot.status=ScrapeStatus.FAILED
    assert freshness(snapshot)['state']=='unavailable'
    assert freshness(None)['state']=='missing'

@pytest.mark.asyncio
async def test_database_migration_is_idempotent_on_legacy_schema():
    if not os.getenv('TEST_DATABASE_URL'):pytest.skip('Postgres required')
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.engine import make_url
    from app.database import initialize_database
    from app.models import Base
    url=os.environ['TEST_DATABASE_URL'];assert make_url(url).database=='social_trends_regression'
    engine=create_async_engine(url)
    try:
        async with engine.begin() as c:
            await c.run_sync(Base.metadata.create_all)
            await c.execute(text('ALTER TABLE scrape_snapshots DROP COLUMN IF EXISTS region CASCADE'))
        await initialize_database(engine);await initialize_database(engine)
        async with engine.connect() as c:
            result=await c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='scrape_snapshots' AND column_name='region'"))
            assert result.scalar()=='region'
            await c.execute(text("INSERT INTO scrape_snapshots (platform,region,status,started_at) VALUES ('DOUYIN','cn','SUCCESS',now())"))
    finally:await engine.dispose()

@pytest.mark.asyncio
async def test_duplicate_refresh_is_skipped_while_running(monkeypatch):
    import asyncio,importlib
    from app.services.trend_service import TrendService
    from app.models import Platform
    module=importlib.import_module('app.services.trend_service')
    service=TrendService();entered=asyncio.Event();release=asyncio.Event()
    async def inner(platform,region):entered.set();await release.wait();return {'success':True}
    monkeypatch.setattr(service,'_scrape_and_save',inner)
    first=asyncio.create_task(service.scrape_single_platform(Platform.TWITTER,'jp'))
    await entered.wait()
    try:
        second=await asyncio.wait_for(service.scrape_single_platform(Platform.TWITTER,'jp'),1)
        assert second['skipped'] and second['reason']=='already_running'
    finally:
        release.set()
        assert (await first)['success']

@pytest.mark.asyncio
async def test_scheduler_runs_initial_and_interval_jobs_and_stops(monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    import app.scheduler as module
    scheduler=AsyncIOScheduler()
    monkeypatch.setattr(module,'scheduler',scheduler)
    monkeypatch.setattr(module,'get_settings',lambda:SimpleNamespace(scrape_interval_hours=.08/3600))
    calls=[];twice=asyncio.Event()
    async def scrape():
        calls.append(1)
        if len(calls)>=2:twice.set()
        return {}
    monkeypatch.setattr(module.trend_service,'run_full_scrape',scrape)
    module.setup_scheduler()
    try:await asyncio.wait_for(twice.wait(),2)
    finally:
        module.shutdown_scheduler()
        await asyncio.sleep(0)
    assert len(calls)>=2 and not scheduler.running

@pytest.mark.asyncio
async def test_upgrade_seeds_douyin_preserving_existing_disabled_config():
    if not os.getenv('TEST_DATABASE_URL'):pytest.skip('Postgres required')
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.engine import make_url
    from app.database import initialize_database
    url=os.environ['TEST_DATABASE_URL'];assert make_url(url).database=='social_trends_regression'
    engine=create_async_engine(url)
    try:
        async with engine.begin() as c:
            await c.execute(text('DELETE FROM platform_configs'))
            await c.execute(text("INSERT INTO platform_configs(platform,enabled,max_topics,region) VALUES ('TWITTER',0,12,'jp'),('TIKTOK',1,20,'global'),('YOUTUBE',1,30,'global'),('INSTAGRAM',1,8,'global')"))
        await initialize_database(engine)
        async with engine.connect() as c:
            rows=(await c.execute(text('SELECT platform,enabled,region FROM platform_configs'))).all()
            data={str(p):(enabled,region) for p,enabled,region in rows}
            assert data['DOUYIN']==(1,'global')
            assert data['TWITTER']==(0,'jp')
    finally:
        async with engine.begin() as c:await c.execute(text('DELETE FROM platform_configs'))
        await engine.dispose()

@pytest.mark.asyncio
async def test_tiktok_regional_failure_does_not_relabel_global_listing(monkeypatch):
    from app.scrapers.tiktok_scraper import TikTokScraper
    from app.scrapers.base import TrendItem
    scraper=TikTokScraper(region='jp');scraper.max_retries=1
    async def blocked():raise RuntimeError('denied')
    async def global_listing():return [TrendItem(1,'global only')]
    monkeypatch.setattr(scraper,'_scrape_knowledge_api',blocked)
    monkeypatch.setattr(scraper,'_scrape_creative_center',blocked)
    monkeypatch.setattr(scraper,'_scrape_discover',global_listing)
    monkeypatch.setattr(scraper,'_scrape_countik',global_listing)
    result=await scraper.execute()
    assert not result.success


def test_compose_only_env_variables_do_not_break_settings(tmp_path):
    from app.config import Settings
    path=tmp_path/'local.env'
    path.write_text('DB_PASSWORD=fixture-only\nSCRAPE_INTERVAL_HOURS=6\n')
    assert Settings(_env_file=path).scrape_interval_hours==6

@pytest.mark.asyncio
@pytest.mark.parametrize('name',['youtube','twitter','tiktok'])
async def test_exhausted_source_chain_is_not_repeated(name,monkeypatch):
    from app.scrapers import get_scraper
    from app.models import Platform
    scraper=get_scraper(Platform(name));calls=[]
    async def failed():calls.append(1);raise RuntimeError('all sources exhausted')
    monkeypatch.setattr(scraper,'scrape',failed)
    result=await scraper.execute()
    assert not result.success and len(calls)==1
