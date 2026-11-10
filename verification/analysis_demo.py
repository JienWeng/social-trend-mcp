"""Controlled demonstration only. Never writes synthetic observations to the service DB."""
import json
from datetime import datetime,timedelta
from pathlib import Path
from app.services.trend_analysis import analyze_history
now=datetime(2026,11,10,12)
scenarios=[('Rising robotics',[20,12,3],[1000,1300,2200]),('Established popular',[1,1,1],[10**8]*3),('Falling topic',[3,8,15],[100]*3),('Counter reset',[10,10,10],[1000,0,2000])]
history=[]
for i in range(3):
    at=now-timedelta(hours=2-i)
    topics=[{'title':name,'url':'https://example.test/'+name.replace(' ','-'),'rank':ranks[i],'volume':values[i],'volume_label':f'{values[i]} posts','region':'global','extra_data':{'data_kind':'third_party_trend_ranking','source':'synthetic://controlled-demo'}} for name,ranks,values in scenarios]
    if i==2:topics.append({'title':'First sample appearance','url':'https://example.test/new','rank':4,'volume':0,'volume_label':'','region':'global','extra_data':{'data_kind':'third_party_trend_ranking','source':'synthetic://controlled-demo'}})
    history.append({'snapshot':{'id':10000+i,'platform':'twitter','region':'global','status':'success','started_at':at.isoformat(),'finished_at':at.isoformat()},'topics':topics})
result=analyze_history(history,now=now)
result['dataset']='SYNTHETIC CONTROLLED DEMONSTRATION — not live trends'
items={topic['title']:topic for topic in result['platforms']['twitter']['topics']}
assert items['Rising robotics']['signal']=='rising_candidate'
assert items['Established popular']['signal']=='stable'
assert items['Falling topic']['signal']=='falling'
assert items['Counter reset']['signal']=='insufficient_evidence'
assert items['First sample appearance']['signal']=='new_to_sample'
Path('verification/analysis-demo.json').write_text(json.dumps(result,indent=2))
for topic in items.values():print(topic['title'],'->',topic['signal'],topic['metric']['change_percent'])
print('PASS: controlled rise, stable popularity, decline, counter reset and first appearance classified as intended; no synthetic DB writes.')
