from datetime import datetime,timedelta
import pytest
from app.services.trend_analysis import analyze_history

NOW=datetime(2026,11,10,12)

def history(platform='twitter',ranks=(20,12,3),metrics=(1000,1300,2200),kind='third_party_trend_ranking',span=2,unit='posts'):
    rows=[]
    for i,(rank,metric) in enumerate(zip(ranks,metrics)):
        when=NOW-timedelta(hours=span*(len(ranks)-i-1)/(len(ranks)-1))
        rows.append({'snapshot':{'id':i+1,'platform':platform,'region':'global','status':'success','started_at':when.isoformat(),'finished_at':when.isoformat()},
                     'topics':[{'title':'Robotics','url':'https://example.test/topic/robotics','rank':rank,'volume':metric,'volume_label':f'{metric} {unit}',
                                'region':'global','extra_data':{'data_kind':kind,'source':'https://example.test'}}]})
    return rows


def topic(rows):return analyze_history(rows,now=NOW)['platforms']['twitter']['topics'][0]


def test_controlled_rise_requires_multiple_observations_and_time():
    result=topic(history())
    assert result['signal']=='rising_candidate'
    assert result['observations']==3 and result['span_hours']==2
    assert result['rank_change']==17
    assert result['metric']['change_percent']==120
    assert result['metric']['per_hour']==600
    assert result['confidence']=='moderate'
    assert 'not a prediction' in result['explanation'].lower()


def test_short_repeated_scrapes_do_not_create_emerging_signal():
    result=topic(history(span=.1))
    assert result['signal']=='insufficient_history'
    assert result['confidence']=='low'


def test_popular_but_flat_is_stable():
    result=topic(history(ranks=(1,1,1),metrics=(10**8,10**8,10**8)))
    assert result['signal']=='stable'


def test_metric_unit_changes_are_never_compared_as_growth():
    rows=history(ranks=(10,10,10))
    rows[-1]['topics'][0]['volume_label']='2200 likes'
    result=topic(rows)
    assert result['metric']['change_percent'] is None
    assert result['signal']!='rising_candidate'
    assert 'metric_context_changed' in result['warnings']


def test_counter_reset_is_flagged_instead_of_growing_from_zero():
    result=topic(history(ranks=(10,10,10),metrics=(1000,0,2000)))
    assert result['signal']=='insufficient_evidence'
    assert 'metric_decreased_or_reset' in result['warnings']


def test_new_to_sample_does_not_mean_new_on_platform():
    rows=history();rows[0]['topics']=[];rows[1]['topics']=[]
    result=topic(rows)
    assert result['signal']=='new_to_sample'
    assert result['first_seen_in_window'] is True
    assert 'new on' not in result['explanation'].lower()


def test_latest_failed_scrape_is_unavailable_not_an_old_positive():
    rows=history();rows[-1]['snapshot']['status']='failed';rows[-1]['topics']=[]
    result=analyze_history(rows,now=NOW)['platforms']['twitter']
    assert result['status']=='unavailable' and result['topics']==[]


def test_instagram_recommendation_order_is_not_rank_momentum():
    rows=history(platform='instagram',kind='public_reels_recommendation_sample',metrics=(500,500,500))
    result=analyze_history(rows,now=NOW)['platforms']['instagram']['topics'][0]
    assert result['rank_change'] is None
    assert result['signal']=='stable'
    assert 'recommendation_order_not_ranking' in result['warnings']


def test_weekly_chart_windows_are_not_comparable_metrics():
    rows=history(platform='youtube',kind='youtube_weekly_music_video_chart',ranks=(5,5,5),unit='weekly views')
    for row,end in zip(rows,['2026-10-29','2026-10-29','2026-11-05']):
        row['topics'][0]['extra_data']['chart_end_date']=end
    result=analyze_history(rows,now=NOW)['platforms']['youtube']['topics'][0]
    assert result['metric']['change_percent'] is None and result['signal']!='rising_candidate'


def test_regions_and_source_types_do_not_merge():
    rows=history();other=history()
    for row in other:
        row['snapshot']['region']='jp'
        row['topics'][0]['title']='Other country'
    result=analyze_history(rows+other,region='global',now=NOW)
    assert result['platforms']['twitter']['topics'][0]['title']=='Robotics'


def test_single_observation_is_not_a_trend_and_old_data_is_stale():
    result=topic(history()[-1:])
    assert result['signal']=='insufficient_history'
    result=analyze_history(history(),now=NOW+timedelta(days=2))['platforms']['twitter']
    assert result['status']=='stale' and all(x['signal']!='rising_candidate' for x in result['topics'])


def test_spacing_filter_cannot_hide_a_known_counter_reset():
    rows=history(ranks=(10,10,10,10),metrics=(100,150,0,200),span=1)
    for row,minutes in zip(rows,[60,30,5,0]):
        at=NOW-timedelta(minutes=minutes)
        row['snapshot'].update(started_at=at.isoformat(),finished_at=at.isoformat())
    result=topic(rows)
    assert result['signal']=='insufficient_evidence'
    assert result['metric']['change_percent'] is None
    assert 'metric_decreased_or_reset' in result['warnings']
    assert result['quality_events'][0]['to_value']==0


def test_inconsistent_rank_movement_is_not_called_stable():
    rows=history(ranks=(20,3,5),metrics=(0,0,0))
    for row in rows:row['topics'][0]['volume_label']=''
    assert topic(rows)['signal']=='mixed_movement'
