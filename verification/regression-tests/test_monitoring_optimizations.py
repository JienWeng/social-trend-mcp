import asyncio
from datetime import timedelta
from types import SimpleNamespace
import pytest
from app.models import Platform
from app.scrapers.base import ScrapeResult,TrendItem
from app.timeutils import utcnow

@pytest.mark.asyncio
async def test_fetch_coalesces_concurrent_calls_and_reuses_success_only():
    from app.fetching import FetchCoordinator
    coordinator=FetchCoordinator(ttl=60,guard=False);calls=[]
    class Scraper:
        async def execute(self):
            calls.append(1);await asyncio.sleep(.01)
            return ScrapeResult(Platform.TWITTER,[TrendItem(1,'one')])
    factory=lambda *a,**kw:Scraper()
    a,b=await asyncio.gather(*(coordinator.fetch(Platform.TWITTER,'global',factory=factory) for _ in range(2)))
    await coordinator.fetch(Platform.TWITTER,'global',factory=factory)
    assert len(calls)==1
    a.items[0].title='mutated'
    assert b.items[0].title=='one'
    await coordinator.fetch(Platform.TWITTER,'jp',factory=factory)
    await coordinator.fetch(Platform.TWITTER,'global',max_topics=8,factory=factory)
    assert len(calls)==3
    class Failed:
        async def execute(self):calls.append(1);return ScrapeResult(Platform.TWITTER,[],False,'blocked')
    failed=lambda *a,**kw:Failed()
    for _ in range(2):await coordinator.fetch(Platform.TWITTER,'global',factory=failed)
    assert len(calls)==5

def test_source_policy_and_global_override_are_shared_with_analysis():
    from app.policy import interval_hours,max_age_seconds
    from app.config import Settings
    settings=Settings(_env_file=None)
    assert interval_hours(Platform.TWITTER,settings)==1
    assert interval_hours(Platform.YOUTUBE,settings)==24
    assert max_age_seconds(Platform.YOUTUBE,settings)==48*3600
    override=Settings(_env_file=None,scrape_interval_hours=3)
    assert interval_hours(Platform.YOUTUBE,override)==3
    specific=Settings(_env_file=None,source_intervals_hours={'youtube':12})
    assert interval_hours(Platform.YOUTUBE,specific)==12
    with pytest.raises(ValueError):Settings(_env_file=None,source_intervals_hours={'youtube':0})

@pytest.mark.asyncio
async def test_history_batch_loads_content_in_two_queries():
    from app.services.trend_service import TrendService
    class Rows:
        def __init__(self,rows):self.rows=rows
        def scalars(self):return self
        def all(self):return self.rows
    snapshots=[SimpleNamespace(id=i,content_snapshot_id=None,to_dict=lambda:{}) for i in range(1,13)]
    class Session:
        calls=0
        async def execute(self,q):
            self.calls+=1
            return Rows(snapshots if self.calls==1 else [])
    session=Session()
    result=await TrendService().get_trend_history(session,Platform.TWITTER)
    assert len(result)==12 and session.calls==2

@pytest.mark.asyncio
async def test_identical_capture_reuses_content_but_keeps_observation_and_config(monkeypatch):
    import os,importlib
    from sqlalchemy import select,func
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from sqlalchemy.engine import make_url
    from app.database import initialize_database
    from app.models import ScrapeSnapshot,TrendTopic,PlatformConfig
    from app.services.trend_service import TrendService
    if not os.getenv('TEST_DATABASE_URL'):pytest.skip('PostgreSQL required')
    url=os.environ['TEST_DATABASE_URL'];assert make_url(url).database=='social_trends_regression'
    engine=create_async_engine(url);factory=async_sessionmaker(engine,expire_on_commit=False)
    await initialize_database(engine)
    module=importlib.import_module('app.services.trend_service')
    monkeypatch.setattr(module,'async_session_factory',factory)
    calls=[];edition=['first']
    class Scraper:
        async def execute(self):
            return ScrapeResult(Platform.TWITTER,[TrendItem(1,'Content fixture',url='https://example.test/dedup',extra_data={'edition':edition[0]})])
    def build(*a,**kw):calls.append(kw);return Scraper()
    monkeypatch.setattr(module,'get_scraper',build)
    from app.fetching import FetchCoordinator
    monkeypatch.setattr(module,'coordinator',FetchCoordinator(ttl=0,guard=False))
    try:
        async with factory() as session:
            config=(await session.execute(select(PlatformConfig).where(PlatformConfig.platform==Platform.TWITTER))).scalar_one_or_none()
            if config is None:session.add(PlatformConfig(platform=Platform.TWITTER,max_topics=8,region='fr'))
            else:config.max_topics=8
            await session.commit()
        service=TrendService()
        first=await service.scrape_single_platform(Platform.TWITTER,'fr')
        second=await service.scrape_single_platform(Platform.TWITTER,'fr')
        async with factory() as session:
            a=await session.get(ScrapeSnapshot,first['snapshot_id']);b=await session.get(ScrapeSnapshot,second['snapshot_id'])
            assert a.id!=b.id and b.content_snapshot_id==a.id
            assert calls[-1]['max_topics']==8
            assert (await session.execute(select(func.count(TrendTopic.id)).where(TrendTopic.snapshot_id==b.id))).scalar()==0
            latest=await service.get_latest_trends(session,Platform.TWITTER,region='fr')
            assert latest['twitter']['topics'][0]['title']=='Content fixture'
            history=await service.get_trend_history(session,Platform.TWITTER,region='fr')
            assert len(history[0]['topics'])==1
            from app.services.trend_analysis import analyze_database
            analyzed=await analyze_database(session,Platform.TWITTER,region='fr')
            assert analyzed['platforms']['twitter']['topics'][0]['raw_observations']>=2
        edition[0]='second'
        third=await service.scrape_single_platform(Platform.TWITTER,'fr')
        async with factory() as session:
            c=await session.get(ScrapeSnapshot,third['snapshot_id'])
            assert c.content_snapshot_id is None
    finally:
        await engine.dispose()

@pytest.mark.asyncio
async def test_mcp_default_fetch_uses_shared_api_not_another_scraper(monkeypatch):
    import httpx,mcp_server as module
    from app.config import Settings
    calls=[]
    class Client:
        def __init__(self,*a,**kw):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*a):pass
        async def get(self,url,**kw):
            calls.append((url,kw))
            return httpx.Response(200,json={'platform':'twitter','items':[{'rank':1,'title':'shared'}],'success':True,'duration_ms':1,'fetched_at':'2026-11-10T10:00:00+00:00'},request=httpx.Request('GET',url))
    monkeypatch.setattr(module.httpx,'AsyncClient',Client)
    monkeypatch.setattr(module,'get_settings',lambda:Settings(_env_file=None))
    result=await module._fetch(Platform.TWITTER,'jp')
    assert result.items[0].title=='shared'
    assert calls[0][0].endswith('/api/v1/feeds/twitter')
    assert calls[0][1]['params']['region']=='jp'

@pytest.mark.asyncio
async def test_scheduler_uses_source_cadences(monkeypatch):
    import app.scheduler as module
    from app.config import Settings
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler=AsyncIOScheduler()
    monkeypatch.setattr(module,'scheduler',scheduler)
    monkeypatch.setattr(module,'get_settings',lambda:Settings(_env_file=None))
    async def startup(*args,**kw):return {}
    monkeypatch.setattr(module.trend_service,'run_full_scrape',startup)
    module.setup_scheduler()
    try:
        assert scheduler.get_job('scrape_twitter').trigger.interval.total_seconds()==3600
        assert scheduler.get_job('scrape_youtube').trigger.interval.total_seconds()==86400
        assert scheduler.get_job('scrape_instagram').trigger.interval.total_seconds()==21600
    finally:
        module.shutdown_scheduler()
        await asyncio.sleep(0)
