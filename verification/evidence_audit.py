"""Field-fidelity audit of recorded public source fixtures, never factual truth."""
import json
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import parse_qs,urlparse
from app.scrapers.douyin_scraper import DouyinScraper
from app.scrapers.instagram_scraper import InstagramScraper
from app.scrapers.youtube_scraper import YouTubeScraper

fixtures=Path('upstream/tests/fixtures')
datasets=[]
def checked(name,items,checks):
    assert items
    assert all(checks),name
    datasets.append({'dataset':name,'records_checked':len(items),'field_checks':len(checks),
                     'mismatches':0,'result':'matches_recorded_source_fields'})
for filename,key,source in [
    ('douyin_billboard.json',None,DouyinScraper.BILLBOARD_URL),
    ('douyin_hot_search.json','data',DouyinScraper.HOT_SEARCH_URL)]:
    raw=json.loads((fixtures/filename).read_text());data=raw[key] if key else raw
    items=DouyinScraper(max_topics=100)._parse_list(data,source)
    checks=[]
    for index,item in enumerate(items):
        record=data['word_list'][index]
        checks.extend([item.title==record['word'],item.rank==index+1,item.volume==record['hot_value'],
                       item.region=='cn','heat score' in item.volume_label,
                       item.extra_data['source_timestamp'].endswith('+08:00')])
    checked(filename,items,checks)
raw=json.loads((fixtures/'instagram-public-records.json').read_text())
html='<script type="application/json">'+json.dumps({'records':raw})+'</script>'
items=InstagramScraper(max_topics=100)._parse_public_page(html)
by_code={row['code']:row for row in raw}
checks=[]
for item in items:
    record=by_code[urlparse(item.url).path.strip('/').split('/')[-1]]
    checks.extend([item.title==record['caption']['text'].splitlines()[0][:160],
                   item.extra_data['author']==record['user']['username'],
                   item.extra_data['likes']==record['like_count'],
                   item.extra_data['comments']==record['comment_count'],
                   item.extra_data['views'] is None,
                   'likes' in item.volume_label])
checked('instagram-public-records.json',items,checks)
raw=json.loads((fixtures/'youtube_charts.json').read_text())
items=YouTubeScraper(max_topics=100)._parse_chart_data(raw)
content=raw['contents']['sectionListRenderer']['contents'][0]['musicAnalyticsSectionRenderer']['content']
by_id={video['id']:video for group in content['videos'] for video in group['videoViews']}
checks=[]
for item in items:
    record=by_id[parse_qs(urlparse(item.url).query)['v'][0]]
    checks.extend([item.title==record['title'],item.rank==record['chartEntryMetadata']['currentPosition'],
                   item.volume==int(record['viewCount']),item.region=='us',
                   item.extra_data['chart_end_date']=='2026-11-05',
                   'weekly views' in item.volume_label])
checked('youtube_charts.json',items,checks)
result={'audited_at':datetime.now(timezone.utc).isoformat(),'method':'Recorded raw-field comparison, not independent live verification',
    'datasets':datasets,'records_checked':sum(d['records_checked'] for d in datasets),
    'field_checks':sum(d['field_checks'] for d in datasets),'mismatches':0,
    'untested_platforms':['twitter','tiktok'],
    'factual_truth_checked':False,'truth_probability':None,
    'limits':['Recorded fixtures are a small selected historical sample.',
              'Checks do not establish current source availability, representativeness, or future trend accuracy.',
              'Checks do not verify factual claims in titles/captions.',
              'This is a deterministic field-mapping audit, not a calibrated accuracy estimate.']}
Path('verification/evidence-audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
