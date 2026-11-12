import asyncio
from datetime import datetime,timezone,timedelta
from email.utils import format_datetime
import pytest,httpx
from app.models import Platform
from app.scrapers.base import ScrapeResult,TrendItem

def test_retry_after_and_restart_preserve_pause(tmp_path):
    from app.source_control import SourceControl,SourceRestricted,retry_after_seconds
    now=[1000.]
    path=tmp_path/'control.json'
    control=SourceControl(clock=lambda:now[0],path=path,min_interval=0)
    assert retry_after_seconds('120',now=1000)==120
    date=format_datetime(datetime.fromtimestamp(1120,timezone.utc),usegmt=True)
    assert retry_after_seconds(date,now=1000)==120
    assert retry_after_seconds('bad',now=1000) is None
    assert control.admit('twitter') is None
    control.finish('twitter',False,SourceRestricted('rate_limited',120))
    restarted=SourceControl(clock=lambda:now[0],path=path,min_interval=0)
    assert restarted.admit('twitter')['retry_after_seconds']==120
    now[0]+=121
    assert restarted.admit('twitter') is None

def test_budget_is_per_platform_not_region_or_limit():
    from app.source_control import SourceControl
    now=[1000.]
    control=SourceControl(clock=lambda:now[0],budget=2,min_interval=0)
    assert control.admit('twitter') is None
    assert control.admit('twitter') is None
    assert control.admit('twitter')['reason']=='budget_exhausted'
    assert control.admit('youtube') is None
    now[0]+=3601
    assert control.admit('twitter') is None

def test_generic_backoff_and_access_denial_are_explicit():
    from app.source_control import SourceControl,SourceRestricted
    now=[1000.];control=SourceControl(clock=lambda:now[0],min_interval=0)
    control.finish('instagram',False,SourceRestricted('access_denied',status=403))
    assert control.status()['instagram']['retry_after_seconds']>=86400
    control.finish('twitter',False)
    first=control.status()['twitter']['retry_after_seconds']
    now[0]+=first+1
    control.finish('twitter',False)
    assert control.status()['twitter']['retry_after_seconds']>first
    control.finish('twitter',True)
    assert control.status()['twitter']['consecutive_failures']==0

@pytest.mark.asyncio
async def test_restricted_source_stops_fallback_and_retries(monkeypatch):
    from app.scrapers.douyin_scraper import DouyinScraper
    calls=[]
    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(429,headers={'Retry-After':'180'})
    scraper=DouyinScraper()
    monkeypatch.setattr(scraper,'_get_client',lambda **kw:httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    result=await scraper.execute()
    assert not result.success and result.error_kind=='rate_limited'
    assert result.retry_after_seconds==180 and len(calls)==1

@pytest.mark.asyncio
async def test_coordinator_pause_blocks_other_region_and_limit_without_fake_attempt():
    from app.source_control import SourceControl
    from app.fetching import FetchCoordinator
    now=[1000.];control=SourceControl(clock=lambda:now[0],min_interval=0)
    coordinator=FetchCoordinator(ttl=0,guard=control);calls=[]
    class Scraper:
        async def execute(self):
            calls.append(1)
            return ScrapeResult(Platform.TWITTER,[],False,'limited',error_kind='rate_limited',retry_after_seconds=120)
    factory=lambda *a,**k:Scraper()
    await coordinator.fetch(Platform.TWITTER,'global',factory=factory)
    deferred=await coordinator.fetch(Platform.TWITTER,'jp',max_topics=8,factory=factory)
    assert len(calls)==1 and not deferred.attempted
    assert deferred.error_kind=='rate_limited'

def test_challenge_route_pauses_without_bypass():
    from app.source_control import check_browser,SourceRestricted
    with pytest.raises(SourceRestricted) as error:check_browser('https://www.instagram.com/accounts/login/',200,{})
    assert error.value.kind=='challenge'

@pytest.mark.parametrize("payload",["broken","[]",'{"version":1,"states":[]}'])
def test_corrupt_state_fails_closed(tmp_path,payload):
    from app.source_control import SourceControl
    path=tmp_path/'state.json';path.write_text(payload)
    control=SourceControl(path=path)
    assert control.admit('twitter')['reason']=='control_state_unavailable'


@pytest.mark.asyncio
async def test_normal_pacing_does_not_mark_fresh_service_unhealthy(monkeypatch):
    import app.routers.trends as routes
    reason=['minimum_interval']
    async def stats(session):
        return {'twitter':{'last_scrape':{'status':'success','topic_count':2},'stale':False,
            'collection_control':{'paused':True,'reason':reason[0]}}}
    monkeypatch.setattr(routes.trend_service,'get_stats',stats)
    assert (await routes.health_check(object()))['status']=='healthy'
    reason[0]='rate_limited'
    assert (await routes.health_check(object()))['status']=='degraded'

@pytest.mark.asyncio
async def test_expired_pause_does_not_erase_last_failure_from_health(monkeypatch):
    import app.routers.trends as routes
    async def stats(session):
        return {'twitter':{'last_scrape':{'status':'success','topic_count':2},'stale':False,
            'collection_control':{'paused':False,'reason':None,'consecutive_failures':1}}}
    monkeypatch.setattr(routes.trend_service,'get_stats',stats)
    assert (await routes.health_check(object()))['status']=='degraded'

def test_access_denial_honors_longer_retry_after():
    from app.source_control import SourceControl,SourceRestricted,check_browser
    with pytest.raises(SourceRestricted) as raised:
        check_browser('https://www.instagram.com/reels/',403,{'retry-after':'172800'})
    control=SourceControl(clock=lambda:1000,min_interval=0)
    control.finish('instagram',False,raised.value)
    assert control.status()['instagram']['retry_after_seconds']==172800

def test_failed_finish_write_does_not_lose_pause_after_restart(tmp_path,monkeypatch):
    from app.source_control import SourceControl,SourceRestricted
    from pathlib import Path
    now=[1000.];path=tmp_path/'state.json'
    control=SourceControl(path=path,clock=lambda:now[0])
    assert control.admit('instagram') is None
    def denied(*a,**k):raise OSError('simulated disk failure')
    with monkeypatch.context() as patch:
        patch.setattr(Path,'replace',denied)
        control.finish('instagram',False,SourceRestricted('access_denied',172800))
    now[0]+=100
    restarted=SourceControl(path=path,clock=lambda:now[0])
    limit=restarted.admit('instagram')
    assert limit is not None and limit['reason']=='unfinished_attempt'
    assert limit['retry_after_seconds'] is None
    assert restarted.admit('twitter') is None
