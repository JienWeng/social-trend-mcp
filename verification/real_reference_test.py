"""Real openly licensed video + fresh source tests; no login or challenge bypass."""
import asyncio,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

SOURCE='https://commons.wikimedia.org/wiki/File:Latte_Coffee_making.webm'
MEDIA='https://upload.wikimedia.org/wikipedia/commons/7/7e/Latte_Coffee_making.webm'
EXPECTED_SHA1='a0ffaf34da0e4e6b76aa0d180f55eb681e2660c6'
async def main():
    directory=Path('.run/reference-inbox');directory.mkdir(parents=True,exist_ok=True)
    video=directory/'real-latte-coffee.webm'
    async with httpx.AsyncClient(timeout=45,headers={'User-Agent':'SocialTrendsMCP-Verification/1.0 (+https://github.com/JienWeng/social-trend-mcp)'}) as client:
        async with client.stream('GET',MEDIA) as response:
            response.raise_for_status()
            size=0
            with video.open('wb') as output:
                async for chunk in response.aiter_bytes():
                    size+=len(chunk)
                    if size>5*1024*1024:raise ValueError('Reference exceeded expected test fixture size')
                    output.write(chunk)
    assert hashlib.sha1(video.read_bytes()).hexdigest()==EXPECTED_SHA1,'Downloaded file differs from published Commons SHA1'
    output={'tested_at':datetime.now(timezone.utc).isoformat(),'dataset':'REAL OPENLY LICENSED VIDEO; not a social-trend/viral-performance claim',
        'source':SOURCE,'download':MEDIA,'credit':'Stevenndori289','license':'CC BY-SA 4.0',
        'license_url':'https://creativecommons.org/licenses/by-sa/4.0/','file_unmodified':True,
        'published_sha1_matches':True,'download_bytes':size,'stages':{},'live_sources':{}}
    params=StdioServerParameters(command=str(Path('start-mcp.sh').resolve()))
    async with stdio_client(params) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            output['mcp_tool_count']=len((await session.list_tools()).tools)
            async def call(name,args):
                started=time.monotonic()
                response=await session.call_tool(name,args)
                value=json.loads(response.content[0].text)
                assert not value.get('error'),value
                output['stages'][name]={'seconds':round(time.monotonic()-started,3),'passed':True}
                return value,response
            reference,_=await call('add_reference',{'title':'Real test — Latte Coffee making (Stevenndori289, CC BY-SA 4.0)',
                'platform':'uploaded','source_url':SOURCE,'niche':'coffee preparation','language':'en','target_country':'MY',
                'audience':'Requested English-speaking coffee audience; location not inferred',
                'notes':'Real, unmodified Wikimedia Commons video by Stevenndori289, CC BY-SA 4.0. License: https://creativecommons.org/licenses/by-sa/4.0/ . Original SHA1 independently matched published Commons value for this test. MY/en are requested output labels, not verified source audience. No organic engagement metrics claimed.'})
            id=reference['id'];output['reference_id']=id
            attached,_=await call('attach_reference_media',{'reference_id':id,'path':video.name})
            assert attached['media_bytes']==size
            analyzed,_=await call('analyze_reference',{'reference_id':id})
            assert analyzed['status']=='ready'
            output['analysis']=analyzed['analysis']
            inspected,images=await call('inspect_reference',{'reference_id':id,'max_frames':7})
            output['inspection_image_count']=sum(c.type=='image' for c in images.content)
            assert output['inspection_image_count']>=4
            target={'reference_ids':[id],'goal':'An original short coffee-preparation concept using broad visual techniques observed in this reference',
                'niche':'coffee preparation','language':'en','target_country':'MY','duration_seconds':20,
                'audience':'English-speaking coffee enthusiasts','target_aspect_ratio':'9:16'}
            context,images=await call('get_creation_context',target)
            output['context_image_count']=sum(c.type=='image' for c in images.content)
            assert output['context_image_count']>=4 and context['generation_performed'] is False
            output['target']=target
            # One ordinary attempt per source. Deferrals/restrictions are recorded, never bypassed.
            for platform in ['twitter','tiktok','youtube','instagram','douyin']:
                started=time.monotonic()
                result=await session.call_tool('capture_trends',{'platform':platform})
                value=json.loads(result.content[0].text)
                output['live_sources'][platform]={'state':value.get('state'),'persisted':value.get('persisted'),
                    'count':len(value.get('topics',[])),'snapshot':value.get('snapshot'),
                    'reason':value.get('reason') or value.get('error_message'),
                    'seconds':round(time.monotonic()-started,3)}
    Path('verification/real-reference-test.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
    print(json.dumps({'reference_id':id,'source':SOURCE,'duration_seconds':output['analysis']['duration_seconds'],
        'frames':output['inspection_image_count'],'context_images':output['context_image_count'],
        'scene_changes':output['analysis']['scene_changes'],'audio':output['analysis']['audio'],
        'speech':output['analysis']['speech']['status'],'stages':output['stages'],
        'sources':{p:{k:v for k,v in data.items() if k!='snapshot'} for p,data in output['live_sources'].items()}},ensure_ascii=False,indent=2))
asyncio.run(main())
