import os,json
from urllib.parse import urlparse,parse_qs
import httpx,pytest
from app.models import Platform
from app.scrapers.twitter_scraper import TwitterScraper
from app.regions import get_region

@pytest.mark.asyncio
async def test_twitter_search_matches_observed_topics_only(monkeypatch):
    from app.scrapers.base import TrendItem
    scraper=TwitterScraper()
    async def scrape():return [TrendItem(1,'#RealTopic')]
    monkeypatch.setattr(scraper,'scrape',scrape)
    assert await scraper.search('inventednoresult')==[]
    items=await scraper.search('realtopic')
    assert [x.title for x in items]==['#RealTopic']

@pytest.mark.asyncio
async def test_twitter_encodes_hashtag_and_preserves_source(monkeypatch):
    scraper=TwitterScraper(region='jp')
    def handler(request):
        assert request.url.path=='/japan/'
        return httpx.Response(200,text='<ol class="trend-card__list"><li><a>#日本 & test</a></li></ol>')
    monkeypatch.setattr(scraper,'_get_client',lambda **kw:httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    item=(await scraper._scrape_trends24())[0]
    assert parse_qs(urlparse(item.url).query)['q']==['#日本 & test']
    assert not urlparse(item.url).fragment
    assert item.extra_data['source']=='https://trends24.in/japan/'


def test_unknown_region_is_rejected():
    with pytest.raises(ValueError,match='region'):
        get_region('madeup')

@pytest.mark.asyncio
async def test_snapshot_regions_isolate_success_failure_and_history(monkeypatch):
    if not os.getenv('TEST_DATABASE_URL'):pytest.skip('Postgres integration')
    from sqlalchemy.engine import make_url
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from app.models import Base
    from app.scrapers.base import ScrapeResult,TrendItem
    import importlib
    module=importlib.import_module('app.services.trend_service')
    assert make_url(os.environ['TEST_DATABASE_URL']).database=='social_trends_regression'
    engine=create_async_engine(os.environ['TEST_DATABASE_URL'])
    factory=async_sessionmaker(engine,expire_on_commit=False)
    from app.database import initialize_database
    await initialize_database(engine)
    monkeypatch.setattr(module,'async_session_factory',factory)
    class Scraper:
        def __init__(self,region):self.region=region
        async def execute(self):return ScrapeResult(Platform.TWITTER,[TrendItem(1,'topic-'+self.region,region=self.region)])
    monkeypatch.setattr(module,'get_scraper',lambda p,**kw:Scraper(kw['region']))
    try:
        await module.trend_service.scrape_single_platform(Platform.TWITTER,region='global')
        await module.trend_service.scrape_single_platform(Platform.TWITTER,region='jp')
        async with factory() as session:
            jp=await module.trend_service.get_latest_trends(session,Platform.TWITTER,region='jp')
            glob=await module.trend_service.get_latest_trends(session,Platform.TWITTER,region='global')
            history=await module.trend_service.get_trend_history(session,Platform.TWITTER,region='jp')
        assert jp['twitter']['topics'][0]['title']=='topic-jp'
        assert glob['twitter']['topics'][0]['title']=='topic-global'
        assert all(x['snapshot']['region']=='jp' for x in history)
        class Failed:
            async def execute(self):return ScrapeResult(Platform.TWITTER,[],False,'blocked-jp')
        monkeypatch.setattr(module,'get_scraper',lambda p,**kw:Failed())
        await module.trend_service.scrape_single_platform(Platform.TWITTER,region='jp')
        async with factory() as session:
            jp=await module.trend_service.get_latest_trends(session,Platform.TWITTER,region='jp')
            glob=await module.trend_service.get_latest_trends(session,Platform.TWITTER,region='global')
        assert jp['twitter']['topics']==[] and jp['twitter']['snapshot']['error_message']=='blocked-jp'
        assert glob['twitter']['topics'][0]['title']=='topic-global'
    finally:await engine.dispose()

def test_popularity_does_not_make_unrelated_topic_relevant():
    from app.topic_intelligence import score_relevance
    score,reason=score_relevance('quantum','Football championship',volume=10**9)
    assert score==0


def test_matching_topic_on_two_platforms_is_not_dropped():
    from app.topic_intelligence import find_related_from_trends
    from app.scrapers.base import TrendItem
    results=find_related_from_trends('robotics',[('twitter',TrendItem(1,'robotics')),('tiktok',TrendItem(1,'robotics'))])
    assert len(results)==2
