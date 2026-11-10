import json
from pathlib import Path

import httpx
import pytest

from app.scrapers.douyin_scraper import DouyinScraper

FIXTURES = Path(__file__).parent / 'fixtures'


def serve(monkeypatch, scraper, responses):
    def handler(request):
        value = responses[str(request.url)]
        if isinstance(value, Exception):
            raise value
        return httpx.Response(200, json=value)
    monkeypatch.setattr(scraper, '_get_client', lambda **kw: httpx.AsyncClient(
        transport=httpx.MockTransport(handler)))


@pytest.mark.asyncio
@pytest.mark.parametrize('region', ['global', 'cn'])
async def test_official_billboard_preserves_heat_source_and_china_scope(monkeypatch, region):
    scraper = DouyinScraper(region=region, max_topics=3)
    data = json.loads((FIXTURES / 'douyin_billboard.json').read_text())
    serve(monkeypatch, scraper, {scraper.BILLBOARD_URL: data})
    items = await scraper.scrape()
    assert len(items) == 3
    assert items[0].title == '勇士51分大胜鹈鹕豪取8连胜'
    assert items[0].rank == 1
    assert items[0].volume == 11117566
    assert items[0].volume_label == '11117566 heat score'
    assert items[0].region == 'cn'
    assert items[0].extra_data['source'] == scraper.BILLBOARD_URL
    assert items[0].extra_data['source_timestamp'] == '2026-11-10T16:12:28+08:00'
    assert items[0].extra_data['requested_region'] == region
    assert items[0].extra_data['data_kind'] == 'official_public_hot_list'
    assert items[0].url.startswith('https://www.douyin.com/search/%E5')


@pytest.mark.asyncio
@pytest.mark.parametrize('region', ['us', 'hk', 'tw', 'jp', 'CN', ''])
async def test_wrong_region_rejected_before_network(region):
    with pytest.raises(ValueError, match='global.*cn'):
        DouyinScraper(region=region)


@pytest.mark.asyncio
async def test_fallback_uses_official_hot_search_when_billboard_fails(monkeypatch):
    scraper = DouyinScraper(max_topics=50)
    data = json.loads((FIXTURES / 'douyin_hot_search.json').read_text())
    serve(monkeypatch, scraper, {
        scraper.BILLBOARD_URL: {'status_code': 1}, scraper.HOT_SEARCH_URL: data})
    items = await scraper.scrape()
    assert len(items) == len(data['data']['word_list'])
    assert items[0].extra_data['source'] == scraper.HOT_SEARCH_URL
    assert items[0].title == data['data']['word_list'][0]['word']


@pytest.mark.asyncio
async def test_invalid_rows_skipped_and_duplicates_removed(monkeypatch):
    scraper = DouyinScraper()
    rows = [None, {}, {'word': ' ', 'hot_value': 1}, {'word': 42, 'hot_value': 1}]
    rows += [{'word': '有效话题', 'hot_value': v} for v in [-1, 'NaN', 'inf', True, None]]
    rows += [{'word': '有效话题', 'hot_value': 123}, {'word': '有效话题', 'hot_value': 124},
             {'word': '下一条', 'hot_value': 0}]
    serve(monkeypatch, scraper, {scraper.BILLBOARD_URL: {
        'status_code': 0, 'active_time': '2026-11-10 16:12:28', 'word_list': rows}})
    items = await scraper.scrape()
    assert [(x.rank, x.title, x.volume) for x in items] == [(1, '有效话题', 123), (2, '下一条', 0)]


@pytest.mark.asyncio
@pytest.mark.parametrize('body', [[], {'status_code': 0, 'word_list': []},
    {'status_code': 0, 'active_time': 'bad', 'word_list': [{'word': 'x', 'hot_value': 1}]},
    {'status_code': 0, 'active_time': '2026-11-10 16:12:28', 'word_list': {}}])
async def test_invalid_sources_return_failed_result_without_static_data(monkeypatch, body):
    scraper = DouyinScraper()
    serve(monkeypatch, scraper, {scraper.BILLBOARD_URL: body, scraper.HOT_SEARCH_URL: body})
    result = await scraper.execute()
    assert not result.success
    assert result.items == []
    assert 'Douyin' in result.error_message


@pytest.mark.asyncio
async def test_timeout_and_non_json_sources_fail_gracefully(monkeypatch):
    scraper = DouyinScraper()
    requests = []
    def handler(request):
        requests.append(request)
        if len(requests) == 1:
            raise httpx.ReadTimeout('source timed out', request=request)
        return httpx.Response(200, text='<html>challenge</html>')
    monkeypatch.setattr(scraper, '_get_client', lambda **kw: httpx.AsyncClient(
        transport=httpx.MockTransport(handler)))
    result = await scraper.execute()
    assert not result.success
    assert len(requests) == 2
    assert all(request.extensions['timeout']['read'] <= 10 for request in requests)
