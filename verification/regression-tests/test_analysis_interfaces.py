import json
import pytest,httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.database import get_db


def test_analysis_rest_validates_and_reads_history(monkeypatch):
    import app.routers.analysis as routes
    calls=[]
    async def analyze(db,**kwargs):calls.append(kwargs);return {'summary':{'rising_candidates':0},'platforms':{}}
    monkeypatch.setattr(routes,'analyze_database',analyze)
    app=FastAPI();app.include_router(routes.router)
    async def db():yield object()
    app.dependency_overrides[get_db]=db
    with TestClient(app) as client:
        assert client.get('/api/v1/analysis/trends?platform=twitter&hours=48').status_code==200
        assert calls[-1]['platform'].value=='twitter'
        assert client.get('/api/v1/analysis/trends?hours=0').status_code==422
        assert client.get('/api/v1/analysis/trends?platform=instagram&region=jp').status_code==400
        assert client.get('/api/v1/analysis/trends?platform=madeup').status_code==400

@pytest.mark.asyncio
async def test_analysis_and_capture_mcp_use_shared_backend(monkeypatch):
    import mcp_server as module
    calls=[]
    class Client:
        def __init__(self,*a,**kw):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*a):pass
        async def request(self,method,url,**kwargs):
            calls.append((method,url,kwargs))
            return httpx.Response(200,json={'persisted':True,'summary':{'rising_candidates':0}},request=httpx.Request(method,url))
    monkeypatch.setattr(module.httpx,'AsyncClient',Client)
    tools=[tool.name for tool in await module.list_tools()]
    assert 'analyze_trends' in tools and 'capture_trends' in tools
    result=await module.call_tool('analyze_trends',{'platform':'twitter','hours':48})
    assert json.loads(result[0].text)['summary']['rising_candidates']==0
    assert calls[-1][0]=='GET' and calls[-1][1].endswith('/api/v1/analysis/trends')
    result=await module.call_tool('capture_trends',{'platform':'twitter'})
    assert json.loads(result[0].text)['persisted'] is True
    assert calls[-1][0]=='POST' and calls[-1][1].endswith('/api/v1/analysis/capture/twitter')

@pytest.mark.asyncio
async def test_analysis_mcp_offline_does_not_fabricate_result(monkeypatch):
    import mcp_server as module
    class Client:
        def __init__(self,*a,**kw):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*a):pass
        async def request(self,*args,**kwargs):raise httpx.ConnectError('backend unavailable')
    monkeypatch.setattr(module.httpx,'AsyncClient',Client)
    result=await module.call_tool('analyze_trends',{})
    assert 'unavailable' in result[0].text.lower()

@pytest.mark.asyncio
async def test_database_analysis_reads_regions_and_persisted_evidence():
    import os
    if not os.getenv('TEST_DATABASE_URL'):pytest.skip('PostgreSQL required')
    from datetime import timedelta
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from sqlalchemy.engine import make_url
    from app.database import initialize_database
    from app.models import Platform,ScrapeSnapshot,ScrapeStatus,TrendTopic
    from app.timeutils import utcnow
    from app.services.trend_analysis import analyze_database
    url=os.environ['TEST_DATABASE_URL'];assert make_url(url).database=='social_trends_regression'
    engine=create_async_engine(url);factory=async_sessionmaker(engine,expire_on_commit=False)
    try:
        await initialize_database(engine)
        async with factory() as session:
            for i,rank in enumerate([20,12,3]):
                when=utcnow()-timedelta(hours=2-i)
                snapshot=ScrapeSnapshot(platform=Platform.TWITTER,region='gb',status=ScrapeStatus.SUCCESS,topic_count=1,started_at=when,finished_at=when)
                session.add(snapshot);await session.flush()
                session.add(TrendTopic(snapshot_id=snapshot.id,platform=Platform.TWITTER,region='gb',rank=rank,title='Synthetic integration topic',url='https://example.test/integration',volume=0,volume_label='',extra_data=json.dumps({'data_kind':'third_party_trend_ranking','source':'https://example.test'})))
            await session.commit()
        async with factory() as session:
            result=await analyze_database(session,Platform.TWITTER,region='gb',hours=24)
            assert result['summary']['rising_candidates']==1
            topic=result['platforms']['twitter']['topics'][0]
            assert topic['rank_change']==17 and len(topic['evidence'])==3
            assert topic['metric']['change_percent'] is None
    finally:await engine.dispose()

@pytest.mark.asyncio
async def test_high_capture_volume_on_one_platform_cannot_erase_another_platform():
    import os
    if not os.getenv('TEST_DATABASE_URL'):pytest.skip('PostgreSQL required')
    from datetime import timedelta
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from sqlalchemy.engine import make_url
    from app.database import initialize_database
    from app.models import Platform,ScrapeSnapshot,ScrapeStatus,TrendTopic
    from app.timeutils import utcnow
    from app.services.trend_analysis import analyze_database
    url=os.environ['TEST_DATABASE_URL'];assert make_url(url).database=='social_trends_regression'
    engine=create_async_engine(url);factory=async_sessionmaker(engine,expire_on_commit=False)
    try:
        await initialize_database(engine)
        async with factory() as session:
            try:
                now=utcnow()
                session.add_all([ScrapeSnapshot(platform=Platform.TWITTER,region='ca',status=ScrapeStatus.SUCCESS,topic_count=0,started_at=now-timedelta(seconds=i),finished_at=now-timedelta(seconds=i)) for i in range(501)])
                for i in range(3):
                    at=now-timedelta(hours=3-i)
                    row=ScrapeSnapshot(platform=Platform.YOUTUBE,region='ca',status=ScrapeStatus.SUCCESS,topic_count=1,started_at=at,finished_at=at)
                    session.add(row);await session.flush()
                    session.add(TrendTopic(snapshot_id=row.id,platform=Platform.YOUTUBE,region='ca',title='Capture-cap fixture',rank=1,url='https://www.youtube.com/watch?v=abcdefghijk',volume=0,volume_label='',extra_data='{}'))
                await session.flush()
                combined=await analyze_database(session,region='ca',hours=24)
                selected=await analyze_database(session,platform=Platform.YOUTUBE,region='ca',hours=24)
                assert combined['platforms']['youtube']['snapshot_count']==selected['platforms']['youtube']['snapshot_count']
                assert combined['platforms']['youtube']['snapshot_count']>=3
                assert combined['platforms']['twitter']['history_truncated'] is True
            finally:await session.rollback()
    finally:await engine.dispose()
