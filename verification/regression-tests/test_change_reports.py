from datetime import timedelta
from copy import deepcopy
import json
import pytest
from app.timeutils import utcnow

def row(id,topics,status='success'):
    at=utcnow()-timedelta(hours=3-id)
    return {'snapshot':{'id':id,'platform':'twitter','region':'global','status':status,'started_at':at,'finished_at':at},'topics':topics}

def item(title,rank,volume=100):
    return {'title':title,'rank':rank,'url':'https://example.test/'+title,'volume':volume,'volume_label':'posts','region':'global','extra_data':{'source':'fixture'}}

def test_changes_explain_additions_removals_and_movement_without_forecasting():
    from app.services.change_report import compare_snapshots
    baseline=row(1,[item('up',12),item('gone',2),item('flat',1)])
    current=row(2,[item('up',3,150),item('added',2),item('flat',1)])
    report=compare_snapshots('twitter',baseline,current)
    assert report['status']=='ok'
    assert report['added'][0]['title']=='added' and report['removed'][0]['title']=='gone'
    assert report['changed'][0]['rank_change']==9
    assert report['changed'][0]['metric']['change_percent']==50
    assert report['counts']=={'added':1,'removed':1,'changed':1,'unchanged':1}
    assert report['changed'][0]['evidence']['baseline_snapshot_id']==1

def test_changes_failure_or_missing_baseline_does_not_invent_disappearance():
    from app.services.change_report import compare_snapshots
    baseline=row(1,[item('old',1)])
    failed=compare_snapshots('twitter',baseline,row(2,[],status='failed'))
    assert failed['status']=='unavailable' and failed['removed']==[]
    assert compare_snapshots('twitter',None,row(2,[item('new',1)]))['status']=='no_baseline'

def test_instagram_order_and_reset_are_not_called_growth():
    from app.services.change_report import compare_snapshots
    old=item('one',10,100);new=item('one',1,0)
    for t in [old,new]:t['extra_data']['data_kind']='public_reels_recommendation_sample'
    report=compare_snapshots('instagram',row(1,[old]),row(2,[new]))
    entry=report['changed'][0]
    assert entry['rank_change'] is None and entry['metric']['change_percent'] is None
    assert 'metric_decreased_or_reset' in entry['warnings']

@pytest.mark.asyncio
async def test_change_report_mcp_calls_shared_api(monkeypatch):
    import httpx,mcp_server as module
    calls=[]
    class Client:
        def __init__(self,*a,**k):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*a):pass
        async def request(self,method,url,**kwargs):
            calls.append((url,kwargs));return httpx.Response(200,json={'platforms':{}},request=httpx.Request(method,url))
    monkeypatch.setattr(module.httpx,'AsyncClient',Client)
    assert 'get_changes' in [t.name for t in await module.list_tools()]
    result=await module.call_tool('get_changes',{'since':'2026-11-10T00:00:00Z','platform':'twitter'})
    assert json.loads(result[0].text)=={'platforms':{}}
    assert calls[-1][0].endswith('/api/v1/analysis/changes')
    invalid=await module.call_tool('get_changes',{'since':'not-a-date'})
    assert 'Invalid request' in invalid[0].text

def test_identical_instagram_recommendations_are_unchanged():
    from app.services.change_report import compare_snapshots
    value=item('one',1)
    value['extra_data']['data_kind']='public_reels_recommendation_sample'
    report=compare_snapshots('instagram',row(1,[value]),row(2,[deepcopy(value)]))
    assert report['counts']['unchanged']==1 and report['changed']==[]

def test_changes_route_validates_checkpoint_and_region():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.routers.analysis import router
    from app.database import get_db
    app=FastAPI();app.include_router(router)
    async def db():yield object()
    app.dependency_overrides[get_db]=db
    with TestClient(app) as client:
        assert client.get('/api/v1/analysis/changes?since=invalid').status_code==422
        assert client.get('/api/v1/analysis/changes?since=2999-01-01T00:00:00Z').status_code==400
        assert client.get('/api/v1/analysis/changes?since=2000-01-01T00:00:00Z').status_code==400
        assert client.get('/api/v1/analysis/changes',params={'since':utcnow().isoformat(),'platform':'instagram','region':'jp'}).status_code==400

@pytest.mark.asyncio
@pytest.mark.parametrize("legacy",[False,True,"cached"])
async def test_checkpoint_excludes_capture_fetched_after_checkpoint(legacy):
    import os
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from sqlalchemy.engine import make_url
    from app.database import initialize_database
    from app.models import Platform,ScrapeSnapshot,ScrapeStatus,TrendTopic
    from app.services.change_report import get_changes
    if not os.getenv('TEST_DATABASE_URL'):pytest.skip('PostgreSQL required')
    url=os.environ['TEST_DATABASE_URL'];assert make_url(url).database=='social_trends_regression'
    engine=create_async_engine(url);factory=async_sessionmaker(engine,expire_on_commit=False)
    try:
        await initialize_database(engine)
        async with factory() as session:
            now=utcnow();checkpoint=now-timedelta(minutes=1)
            old=ScrapeSnapshot(platform=Platform.TWITTER,region='de',status=ScrapeStatus.SUCCESS,topic_count=1,
                started_at=now-timedelta(hours=2),finished_at=now-timedelta(hours=2),fetched_at=now-timedelta(hours=2))
            new=ScrapeSnapshot(platform=Platform.TWITTER,region='de',status=ScrapeStatus.SUCCESS,topic_count=1,
                started_at=now-timedelta(minutes=2),finished_at=now,fetched_at=(now-timedelta(minutes=3)) if legacy=="cached" else (None if legacy else now))
            session.add_all([old,new]);await session.flush()
            for snap,title in [(old,'before checkpoint'),(new,'after checkpoint')]:
                session.add(TrendTopic(snapshot_id=snap.id,platform=Platform.TWITTER,region='de',title=title,rank=1,url='https://example.test/'+title))
            await session.flush()
            report=(await get_changes(session,checkpoint,Platform.TWITTER,region='de'))['platforms']['twitter']
            assert report['baseline']['id']==old.id
            assert report['current']['id']==new.id
            assert report['counts']['added']==1 and report['counts']['removed']==1
            await session.rollback()
    finally:await engine.dispose()
