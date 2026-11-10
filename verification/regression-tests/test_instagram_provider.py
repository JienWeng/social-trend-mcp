import json
from pathlib import Path
import httpx
import pytest
from pydantic import SecretStr
from app.scrapers.instagram_scraper import InstagramScraper


def configured(monkeypatch,payload,status=200,region='global'):
    scraper=InstagramScraper(region=region)
    scraper.settings=scraper.settings.model_copy(update={'socialcrawl_api_key':SecretStr('fixture-key'),'instagram_source':'socialcrawl'})
    calls=[]
    def handler(request):
        calls.append(request)
        assert str(request.url)=='https://www.socialcrawl.dev/v1/instagram/reels/trending'
        assert request.headers['x-api-key']=='fixture-key'
        assert request.headers['Idempotency-Key']
        return httpx.Response(status,json=payload)
    monkeypatch.setattr(scraper,'_get_client',lambda **kw:httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    return scraper,calls


def feed():
    return {'success':True,'platform':'instagram','data':{'items':[
        {'post':{'id':'1','url':'https://www.instagram.com/reel/ABC123/',
         'content':{'text':'Robotics demo #robotics'},'author':{'username':'lab'},
         'engagement':{'views':None,'likes':50,'comments':3},
         'published_at':'2026-11-09T12:00:00Z','ext':{'hashtags':['robotics']}}}
    ]},'cached':False,'request_id':'fixture'}

@pytest.mark.asyncio
async def test_instagram_provider_accepts_posts_and_preserves_unknown_views(monkeypatch):
    scraper,calls=configured(monkeypatch,feed())
    result=await scraper.scrape()
    assert len(calls)==1 and len(result)==1
    assert result[0].url=='https://www.instagram.com/reel/ABC123/'
    assert result[0].volume==50
    assert result[0].volume_label=='50 likes'
    assert result[0].extra_data['views'] is None
    assert result[0].extra_data['likes']==50
    assert result[0].extra_data['published_at']=='2026-11-09T12:00:00Z'
    assert result[0].extra_data['data_kind']=='sampled_trending_reels'
    assert 'not a global ranking' in result[0].description

@pytest.mark.asyncio
async def test_instagram_provider_deduplicates_and_rejects_bad_rows(monkeypatch):
    data=feed();data['data']['items']*=2
    data['data']['items'] += [{'post':{'id':'2','url':'https://evil.example/reel/ABC/'}}, {'post':None}]
    scraper,_=configured(monkeypatch,data)
    assert len(await scraper.scrape())==1

@pytest.mark.asyncio
@pytest.mark.parametrize('status',[401,402,429,500])
async def test_instagram_provider_failure_does_not_fall_back_or_retry_billable_call(monkeypatch,status):
    scraper,calls=configured(monkeypatch,{'success':False,'error':{'message':'fixture-key'}},status)
    result=await scraper.execute()
    assert not result.success
    assert str(status) in result.error_message
    assert 'fixture-key' not in result.error_message
    assert len(calls)==1

@pytest.mark.asyncio
async def test_instagram_provider_rejects_regional_claim_before_billing(monkeypatch):
    with pytest.raises(ValueError,match='global sample'):
        configured(monkeypatch,feed(),region='jp')

@pytest.mark.asyncio
async def test_instagram_live_demo_fixture_parses(monkeypatch):
    payload=json.loads((Path(__file__).parent/'fixtures'/'instagram-demo.json').read_text())
    scraper,calls=configured(monkeypatch,payload)
    result=await scraper.scrape()
    assert len(result)==12
    assert all(x.url.startswith('https://www.instagram.com/reel/') for x in result)
    assert result[0].extra_data['views']==44135847

@pytest.mark.asyncio
async def test_instagram_demo_fixture_persists_and_broadcasts_source_metadata(monkeypatch):
    import os,importlib
    if not os.getenv('TEST_DATABASE_URL'):
        pytest.skip('TEST_DATABASE_URL required')
    from sqlalchemy.engine import make_url
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from app.models import Base,Platform
    from app.routers.websocket import active_connections
    assert make_url(os.environ['TEST_DATABASE_URL']).database=='social_trends_regression'
    engine=create_async_engine(os.environ['TEST_DATABASE_URL'])
    factory=async_sessionmaker(engine,expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    payload=json.loads((Path(__file__).parent/'fixtures'/'instagram-demo.json').read_text())
    scraper,calls=configured(monkeypatch,payload)
    module=importlib.import_module('app.services.trend_service')
    monkeypatch.setattr(module,'get_scraper',lambda platform,**kw:scraper)
    monkeypatch.setattr(module,'async_session_factory',factory)
    messages=[]
    class Socket:
        async def send_text(self,message):messages.append(json.loads(message))
    socket=Socket();active_connections.add(socket)
    try:
        result=await module.trend_service.scrape_single_platform(Platform.INSTAGRAM)
        assert result['success'] and result['count']==12
        assert len(calls)==1 and len(messages)==1
        async with factory() as session:
            latest=await module.trend_service.get_latest_trends(session,Platform.INSTAGRAM)
        topics=latest['instagram']['topics']
        assert topics==messages[0]['topics']
        assert topics[0]['extra_data']['data_kind']=='sampled_trending_reels'
        assert topics[0]['extra_data']['views']==44135847
        assert topics[0]['extra_data']['likes']==2050711
        assert 'fixture-key' not in json.dumps(messages)
    finally:
        active_connections.discard(socket)
        await engine.dispose()
