"""Run from repository root: PYTHONPATH=upstream .venv/bin/python verification/youtube_live.py."""
import asyncio
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from app.scrapers.youtube_scraper import YouTubeScraper

async def main():
    evidence={'checked_at':datetime.now(timezone.utc).isoformat(), 'mode':'ordinary headless Playwright Chromium; no API key, login, or stealth', 'regions':{}}
    for region in ['global','jp','gb']:
        scraper=YouTubeScraper(region=region,max_topics=100)
        scraper.settings=scraper.settings.model_copy(update={'youtube_api_key':''})
        try:
            items=await scraper.scrape()
            evidence['regions'][region]={'count':len(items),'items':[asdict(item) for item in items]}
            print(region,len(items),items[0].title,items[0].extra_data['source'])
        except Exception as error:
            evidence['regions'][region]={'error':str(error)}
            print(region,type(error).__name__,str(error)[:180])
    try:
        await scraper.search('robotics')
    except RuntimeError as error:
        evidence['search_limitation']=str(error)
    Path('verification/youtube_live.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
asyncio.run(main())
