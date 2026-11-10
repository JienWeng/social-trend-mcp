import copy
import json
from pathlib import Path
import httpx
import pytest
from app.scrapers.youtube_scraper import YouTubeScraper

FIXTURE = Path(__file__).parent / 'fixtures/youtube_charts.json'

def chart():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))

def content(data):
    return data['contents']['sectionListRenderer']['contents'][0]['musicAnalyticsSectionRenderer']['content']

def test_public_chart_preserves_real_rank_region_period_and_views():
    scraper = YouTubeScraper(region='global', max_topics=1)
    items = scraper._parse_chart_data(chart())
    assert len(items) == 1
    item = items[0]
    assert (item.title, item.rank, item.region, item.category) == ('Dai Dai', 1, 'us', 'music')
    assert item.volume == 2338755
    assert item.volume_label == '2,338,755 weekly views'
    assert item.extra_data['chart_end_date'] == '2026-11-05'
    assert item.extra_data['requested_region'] == 'global'
    assert item.extra_data['source'] == 'https://charts.youtube.com/charts/TopVideos/us/weekly'

@pytest.mark.parametrize('region', ['jp','gb'])
def test_rejects_chart_for_wrong_country(region):
    with pytest.raises(RuntimeError, match='region'):
        YouTubeScraper(region=region)._parse_chart_data(chart())

def test_missing_counts_are_unknown_and_unicode_is_preserved():
    data = chart()
    video = content(data)['videos'][0]['videoViews'][0]
    video.pop('viewCount')
    video['title'] = '日本語 é 🎵'
    item = YouTubeScraper()._parse_chart_data(data)[0]
    assert item.title == '日本語 é 🎵'
    assert item.volume == 0 and item.volume_label == ''
    assert item.extra_data['views_available'] is False

def test_ignores_wrong_chart_type_and_malformed_videos():
    data = chart()
    content(data)['perspectiveMetadata']['requestParams']['chartParams']['chartType'] = 'CHART_TYPE_ARTISTS'
    with pytest.raises(RuntimeError, match='chart'):
        YouTubeScraper()._parse_chart_data(data)

@pytest.mark.asyncio
async def test_api_credentials_not_in_error_or_request_url(monkeypatch):
    scraper = YouTubeScraper(region='us')
    urls=[]
    def handler(request):
        urls.append(str(request.url))
        return httpx.Response(403, json={'error': {'message':'denied'}})
    monkeypatch.setattr(scraper, '_get_client', lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    with pytest.raises(Exception) as error:
        await scraper._scrape_api('secret-test-key')
    assert 'secret-test-key' not in str(error.value)
    assert all('secret-test-key' not in url for url in urls)

@pytest.mark.asyncio
async def test_no_key_search_reports_limitation():
    scraper=YouTubeScraper()
    scraper.settings=scraper.settings.model_copy(update={'youtube_api_key':''})
    with pytest.raises(RuntimeError,match='API key'):
        await scraper.search('robotics')

@pytest.mark.parametrize('mutation', ['id', 'title', 'rank', 'hidden', 'unavailable', 'duplicate'])
def test_skips_invalid_or_duplicate_chart_entries(mutation):
    data=chart()
    videos=content(data)['videos'][0]['videoViews']
    if mutation == 'id': videos[0]['id']='bad'
    elif mutation == 'title': videos[0]['title']=''
    elif mutation == 'rank': videos[0]['chartEntryMetadata']['currentPosition']=0
    elif mutation == 'hidden': videos[0]['isVisible']=False
    elif mutation == 'unavailable': videos[0]['isAvailable']=False
    else: videos.append(copy.deepcopy(videos[0]))
    items=YouTubeScraper()._parse_chart_data(data)
    assert len(items) == (2 if mutation=='duplicate' else 1)
    assert len({item.url for item in items}) == len(items)

@pytest.mark.parametrize('data', [{}, {'contents': {'sectionListRenderer': {'contents': []}}}])
def test_empty_chart_is_explicit_failure(data):
    with pytest.raises(RuntimeError,match='chart'):
        YouTubeScraper()._parse_chart_data(data)

@pytest.mark.asyncio
async def test_unknown_region_rejected_even_for_keyless_search():
    with pytest.raises(ValueError,match='region'):
        scraper=YouTubeScraper(region='not-a-region')
        scraper.settings=scraper.settings.model_copy(update={'youtube_api_key':''})
        await scraper.search('robotics')

@pytest.mark.asyncio
async def test_api_still_returns_popular_videos(monkeypatch):
    scraper=YouTubeScraper(region='global')
    def handler(request):
        assert request.headers['X-Goog-Api-Key']=='secret-test-key'
        assert request.url.params['chart']=='mostPopular'
        assert request.url.params['regionCode']=='US'
        return httpx.Response(200,json={'items':[{'id':'fcnDmrtj6Sk','snippet':{'title':'Music','categoryId':'10'},'statistics':{'viewCount':'1234'}}]})
    monkeypatch.setattr(scraper,'_get_client',lambda:httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    item=(await scraper._scrape_api('secret-test-key'))[0]
    assert item.title=='Music' and item.volume==1234

@pytest.mark.asyncio
async def test_api_missing_views_are_not_labelled_zero_and_region_is_actual(monkeypatch):
    scraper=YouTubeScraper(region='global')
    monkeypatch.setattr(scraper,'_get_client',lambda:httpx.AsyncClient(transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'items':[{'id':'fcnDmrtj6Sk','snippet':{'title':'Music'}}]}))))
    item=(await scraper._scrape_api('secret-test-key'))[0]
    assert item.volume_label==''
    assert item.region=='us'
    assert item.extra_data['source']=='https://www.googleapis.com/youtube/v3/videos'
    assert item.extra_data['requested_region']=='global'
