import json
from pathlib import Path
import pytest
from app.scrapers.instagram_scraper import InstagramScraper


def html(records):
    return '<script type="application/json">'+json.dumps({'require':[{'result':{'edges':[{'node':x} for x in records]}}]})+'</script>'


def captured():
    return json.loads((Path(__file__).parent/'fixtures'/'instagram-public-records.json').read_text())


def test_public_page_extracts_captured_reels_without_guessing_views():
    scraper=InstagramScraper()
    items=scraper._parse_public_page(html(captured()))
    assert len(items)==8
    assert items[0].url=='https://www.instagram.com/reel/DfZ3t4uo9NT/'
    assert items[0].volume_label=='6,370,719 likes'
    assert items[0].extra_data['views'] is None
    assert items[0].extra_data['comments']==22663
    assert items[0].extra_data['data_kind']=='public_reels_recommendation_sample'
    assert items[0].extra_data['published_at'].startswith('2026-11-06')
    assert 'not a global ranking' in items[0].description


def test_public_page_rejects_navigation_and_deduplicates():
    scraper=InstagramScraper()
    items=scraper._parse_public_page(html([captured()[0],captured()[0],{'code':'en','name':'English'},{'code':'../evil','user':{'username':'test'},'like_count':50}]))
    assert len(items)==1


def test_public_page_empty_and_login_are_not_success():
    scraper=InstagramScraper()
    for page in ['<h1>Log in</h1>','<script type="application/json">not JSON</script>']:
        assert scraper._parse_public_page(page)==[]

@pytest.mark.asyncio
async def test_browser_is_default_even_if_paid_key_exists(monkeypatch):
    scraper=InstagramScraper()
    from pydantic import SecretStr
    scraper.settings=scraper.settings.model_copy(update={'socialcrawl_api_key':SecretStr('fixture-key')})
    async def browser():return scraper._parse_public_page(html(captured()))
    async def paid():pytest.fail('Must not silently use a paid provider')
    monkeypatch.setattr(scraper,'_scrape_browser',browser,raising=False)
    monkeypatch.setattr(scraper,'_scrape_socialcrawl',paid)
    assert len(await scraper.scrape())==8

@pytest.mark.asyncio
async def test_browser_failure_never_falls_back_to_paid(monkeypatch):
    scraper=InstagramScraper()
    async def blocked():raise RuntimeError('Instagram public page requires login or returned no data')
    async def paid():pytest.fail('Must not silently use a paid provider')
    monkeypatch.setattr(scraper,'_scrape_browser',blocked,raising=False)
    monkeypatch.setattr(scraper,'_scrape_socialcrawl',paid)
    result=await scraper.execute()
    assert not result.success and 'requires login' in result.error_message

@pytest.mark.asyncio
async def test_browser_rejects_country_before_launch():
    with pytest.raises(ValueError,match='global sample'):
        InstagramScraper(region='jp')
