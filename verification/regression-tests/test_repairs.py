import json
import httpx
import pytest
from app.scrapers.tiktok_scraper import TikTokScraper
from app.scrapers.instagram_scraper import InstagramScraper
from app.scrapers.base import BaseScraper


def serve(monkeypatch, scraper, body, json_body=False):
    def handler(request):
        return httpx.Response(200, json=body) if json_body else httpx.Response(200,text=body)
    monkeypatch.setattr(scraper,'_get_client',lambda **kw:httpx.AsyncClient(transport=httpx.MockTransport(handler)))

@pytest.mark.asyncio
async def test_tiktok_rejects_language_metadata(monkeypatch):
    scraper=TikTokScraper()
    serve(monkeypatch,scraper,'<script>{"discover":{"name":"en","language":{"name":"English"}}}</script>')
    assert await scraper._scrape_discover()==[]

@pytest.mark.asyncio
async def test_tiktok_accepts_actual_hashtag(monkeypatch):
    scraper=TikTokScraper()
    serve(monkeypatch,scraper,'<a href="/tag/robotics">#robotics</a><h2><a href="/login">Sign in</a></h2>')
    items=await scraper._scrape_discover()
    assert [x.title for x in items]==['robotics']
    assert items[0].extra_data['source']=='https://www.tiktok.com/discover'

@pytest.mark.asyncio
async def test_tiktok_checks_application_error(monkeypatch):
    scraper=TikTokScraper()
    serve(monkeypatch,scraper,{'code':40101,'msg':'no permission'},True)
    with pytest.raises(RuntimeError,match='40101.*no permission'):
        await scraper._scrape_creative_center()

@pytest.mark.asyncio
async def test_tiktok_search_does_not_invent_matches(monkeypatch):
    scraper=TikTokScraper()
    serve(monkeypatch,scraper,{'code':40101,'msg':'no permission'},True)
    assert await scraper.search('invented-no-results')==[]

@pytest.mark.asyncio
async def test_instagram_parses_only_trending_section(monkeypatch):
    scraper=InstagramScraper()
    serve(monkeypatch,scraper,'<nav><a href="/hashtag/new/">New Hashtags</a></nav><article><h3>Top Hashtags</h3><a href="/hashtag/love/">love</a></article><article><h3>Trending Hashtags</h3><a href="hashtag/robotics/">robotics</a><a href="/hashtag/robotics/">robotics</a><a href="/hashtag/bad/">Bad Label</a></article>')
    items=await scraper._scrape_best_hashtags()
    assert [x.title for x in items]==['robotics']
    assert items[0].extra_data['data_kind']=='third_party_hashtag_suggestions'
    assert 'not verified' in items[0].description.lower()

@pytest.mark.asyncio
async def test_instagram_does_not_return_static_data(monkeypatch):
    scraper=InstagramScraper()
    scraper.settings=scraper.settings.model_copy(update={'instagram_source':'suggestions'})
    async def empty():return []
    for name in ['_scrape_best_hashtags']:
        monkeypatch.setattr(scraper,name,empty)
    with pytest.raises(RuntimeError,match='Instagram'):
        await scraper.scrape()

@pytest.mark.asyncio
async def test_empty_scrape_is_failure(monkeypatch):
    scraper=TikTokScraper();scraper.max_retries=1
    async def empty():return []
    monkeypatch.setattr(scraper,'scrape',empty)
    result=await scraper.execute()
    assert not result.success
    assert 'No valid' in result.error_message

@pytest.mark.asyncio
async def test_persisted_scrape_broadcasts_and_latest_failure_hides_old_data(monkeypatch):
    import os
    if not os.getenv('TEST_DATABASE_URL'):
        pytest.skip('TEST_DATABASE_URL required for PostgreSQL integration test')
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from app.models import Base,Platform,ScrapeStatus,ScrapeSnapshot
    from app.scrapers.base import TrendItem,ScrapeResult
    from app.services import trend_service
    from app.routers.websocket import active_connections
    from sqlalchemy import select
    from sqlalchemy.engine import make_url
    assert make_url(os.environ['TEST_DATABASE_URL']).database == 'social_trends_regression', 'Use the dedicated regression database'
    engine=create_async_engine(os.environ['TEST_DATABASE_URL'])
    factory=async_sessionmaker(engine,expire_on_commit=False)
    async with engine.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
        await c.run_sync(Base.metadata.create_all)
    import importlib
    module=importlib.import_module('app.services.trend_service')
    monkeypatch.setattr(module,'async_session_factory',factory)
    class Scraper:
        async def execute(self):
            return ScrapeResult(Platform.INSTAGRAM,[TrendItem(1,'robotics')])
    monkeypatch.setattr(module,'get_scraper',lambda p,**kw:Scraper())
    messages=[]
    class Socket:
        async def send_text(self,message):
            data=json.loads(message)
            async with factory() as session:
                snap=await session.get(ScrapeSnapshot,data['snapshot']['id'])
                assert snap is not None, 'Broadcast must happen after commit'
            messages.append(data)
    sock=Socket();active_connections.add(sock)
    try:
        await trend_service.scrape_single_platform(Platform.INSTAGRAM)
        assert len(messages)==1
        assert messages[0]['type']=='trends_updated'
        assert messages[0]['topics'][0]['title']=='robotics'
        class Failed:
            async def execute(self):return ScrapeResult(Platform.INSTAGRAM,[],False,'blocked')
        monkeypatch.setattr(module,'get_scraper',lambda p,**kw:Failed())
        await trend_service.scrape_single_platform(Platform.INSTAGRAM)
        assert messages[-1]['snapshot']['status']=='failed'
        async with factory() as session:
            data=await trend_service.get_latest_trends(session,Platform.INSTAGRAM)
        assert data['instagram']['topics']==[]
        assert data['instagram']['snapshot']['error_message']=='blocked'
        from app.routers.trends import health_check
        async with factory() as session:
            health = await health_check(session)
        assert health['status'] == 'degraded'
    finally:
        active_connections.discard(sock)
        await engine.dispose()

@pytest.mark.asyncio
async def test_current_tiktok_endpoint_returns_real_metrics(monkeypatch):
    scraper=TikTokScraper(region='jp')
    requests=[]
    def handler(request):
        requests.append(request)
        assert request.method=='POST'
        assert request.url.path=='/CreativeOne/KnowledgeAPI/GetHashtagList'
        assert json.loads(request.content)['countryCode']=='JP'
        return httpx.Response(200,json={'BaseResp':{'StatusCode':0},'items':[
            {'hashtagID':'123','hashtagName':'ロボット','rankIndex':1,'publishCnt':'42','vv':'2500','popularityCurve':[{'timestamp':'1794096000','value':100}]}
        ],'pagination':{'limit':3,'totalCount':3,'hasMore':False}})
    monkeypatch.setattr(scraper,'_get_client',lambda **kw:httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    result=await scraper.scrape()
    assert result[0].title=='ロボット'
    assert result[0].volume==2500
    assert result[0].region=='jp'
    assert result[0].extra_data['post_count']==42
    assert result[0].extra_data['period_days']==7
    assert result[0].extra_data['public_preview_limited'] is True
    assert len(requests)==1

@pytest.mark.asyncio
async def test_current_tiktok_global_records_actual_us_region(monkeypatch):
    scraper=TikTokScraper()
    def handler(request):
        assert request.method=='POST'
        assert json.loads(request.content)['countryCode']=='US'
        return httpx.Response(200,json={'BaseResp':{'StatusCode':0},'items':[
            {'hashtagID':'123','hashtagName':'robotics','publishCnt':42,'vv':2500}
        ],'pagination':{'limit':3,'totalCount':3,'hasMore':False}})
    monkeypatch.setattr(scraper,'_get_client',lambda **kw:httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    items=await scraper.scrape()
    assert items[0].region=='us'
    assert items[0].extra_data['requested_region']=='global'
    assert 'US' in items[0].description

@pytest.mark.asyncio
async def test_current_tiktok_permission_error_is_not_success(monkeypatch):
    scraper=TikTokScraper()
    serve(monkeypatch,scraper,{'BaseResp':{'StatusCode':401,'StatusMessage':'login required'},'items':[]},True)
    with pytest.raises(RuntimeError,match='401.*login required'):
        await scraper._scrape_knowledge_api()

@pytest.mark.asyncio
async def test_current_tiktok_rejects_malformed_metrics(monkeypatch):
    scraper=TikTokScraper()
    serve(monkeypatch,scraper,{'BaseResp':{'StatusCode':0},'items':[{'hashtagID':'1','hashtagName':'robotics','vv':-5,'publishCnt':4}]},True)
    assert await scraper._scrape_knowledge_api()==[]


def test_packaged_mcp_entrypoint_is_synchronous():
    import inspect,mcp_server
    assert not inspect.iscoroutinefunction(mcp_server.main)

@pytest.mark.asyncio
async def test_instagram_suggestions_require_explicit_opt_in(monkeypatch):
    scraper=InstagramScraper()
    scraper.settings=scraper.settings.model_copy(update={'instagram_allow_suggestions':True})
    serve(monkeypatch,scraper,'<article><h3>Trending Hashtags</h3><a href="/hashtag/robotics/">robotics</a></article>')
    result=await scraper.scrape()
    assert result[0].extra_data['data_kind']=='third_party_hashtag_suggestions'

@pytest.mark.asyncio
async def test_tiktok_search_uses_current_preview(monkeypatch):
    scraper=TikTokScraper(region='us')
    serve(monkeypatch,scraper,{'BaseResp':{'StatusCode':0},'items':[
        {'hashtagID':'1','hashtagName':'robotics','vv':500,'publishCnt':4},
        {'hashtagID':'2','hashtagName':'music','vv':400,'publishCnt':3}]},True)
    items=await scraper.search('robot')
    assert [x.title for x in items]==['robotics']
    assert items[0].volume==500
