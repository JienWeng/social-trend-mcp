import json
from types import SimpleNamespace
import httpx,pytest
from app.models import Platform
from app.scrapers.base import ScrapeResult

def test_quality_does_not_turn_provenance_into_truth_probability():
    from app.services.evidence_report import assess_quality
    item={'title':'Claim in a caption','url':'https://www.instagram.com/reel/abc123/',
        'region':'global','rank':1,'volume':0,'volume_label':'',
        'extra_data':{'source':'https://www.instagram.com/reels/','data_kind':'public_reels_recommendation_sample','views':None}}
    result=assess_quality('instagram',[item])
    assert result['provenance']['first_party']==1
    assert result['metrics']['known']==0 and result['metrics']['unknown']==1
    assert result['ranking']['usable'] is False
    assert result['factual_truth']['status']=='not_checked'
    assert result['factual_truth']['probability'] is None
    assert result['source_fidelity']['status']=='not_independently_verified'

def test_unknown_source_and_missing_metrics_are_visible():
    from app.services.evidence_report import assess_quality
    result=assess_quality('twitter',[{'title':'Unattributed','url':'','volume':0,'volume_label':'','extra_data':{}}])
    assert result['provenance']['unknown']==1
    assert 'missing_topic_links' in result['warnings']

@pytest.mark.asyncio
async def test_default_report_is_read_only_and_gives_action(monkeypatch):
    import app.services.evidence_report as module
    calls=[]
    async def latest(session,**kwargs):
        calls.append('stored');return {'twitter':{'snapshot':None,'topics':[],'freshness':{'state':'missing'}}}
    async def analysis(session,**kwargs):
        return {'platforms':{'twitter':{'status':'insufficient_history','topics':[],'rising_candidates':0}}}
    monkeypatch.setattr(module.trend_service,'get_latest_trends',latest)
    monkeypatch.setattr(module,'analyze_database',analysis)
    async def changes(*a,**kw):return {'platforms':{}}
    monkeypatch.setattr(module,'get_changes',changes)
    report=await module.build_report(object(),platform=Platform.TWITTER)
    assert calls==['stored']
    assert report['platforms']['twitter']['next_action']['tool']=='capture_trends'
    assert report['read_only'] is True and report['truth_probability'] is None

@pytest.mark.asyncio
async def test_get_report_mcp_supports_no_arguments(monkeypatch):
    import mcp_server as module
    calls=[]
    class Client:
        def __init__(self,*a,**k):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*a):pass
        async def request(self,method,url,**kw):
            calls.append((url,kw));return httpx.Response(200,json={'read_only':True,'platforms':{}},request=httpx.Request(method,url))
    monkeypatch.setattr(module.httpx,'AsyncClient',Client)
    assert 'get_report' in [t.name for t in await module.list_tools()]
    result=await module.call_tool('get_report',{})
    assert json.loads(result[0].text)['read_only']
    assert calls[0][0].endswith('/api/v1/analysis/report')

@pytest.mark.asyncio
async def test_deferred_capture_is_not_persisted_or_called_busy(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.database import get_db
    import app.routers.analysis as routes
    async def deferred(*a,**k):return {'success':False,'skipped':True,'reason':'rate_limited','retry_after_seconds':120}
    monkeypatch.setattr(routes.trend_service,'scrape_single_platform',deferred)
    app=FastAPI();app.include_router(routes.router)
    async def db():yield object()
    app.dependency_overrides[get_db]=db
    with TestClient(app) as client:
        response=client.post('/api/v1/analysis/capture/twitter')
    assert response.status_code==429 and response.headers['retry-after']=='120'
    assert response.json()['persisted'] is False and response.json()['state']=='collection_deferred'

@pytest.mark.asyncio
async def test_controller_deferral_does_not_open_persistence_session(monkeypatch):
    import importlib
    module=importlib.import_module('app.services.trend_service')
    class Session:
        async def __aenter__(self):return self
        async def __aexit__(self,*a):pass
        async def execute(self,*a):return SimpleNamespace(scalar_one_or_none=lambda:None)
    opened=[]
    def factory():opened.append(1);return Session()
    class Coordinator:
        async def fetch(self,*a,**k):return ScrapeResult(Platform.TWITTER,[],False,'paused',error_kind='rate_limited',retry_after_seconds=120,attempted=False)
    monkeypatch.setattr(module,'async_session_factory',factory)
    monkeypatch.setattr(module,'coordinator',Coordinator())
    result=await module.TrendService()._scrape_and_save(Platform.TWITTER)
    assert result['skipped'] and len(opened)==1
