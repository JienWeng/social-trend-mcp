"""Explicit synthetic local-video demo through the real MCP transport; no social download."""
import argparse,asyncio,json,subprocess
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    inbox=Path('.run/reference-inbox');inbox.mkdir(parents=True,exist_ok=True)
    video=inbox/'synthetic-reference-demo.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
        '-f','lavfi','-i','color=c=red:s=320x240:r=10:d=2',
        '-f','lavfi','-i','color=c=blue:s=320x240:r=10:d=2',
        '-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=4',
        '-filter_complex',"[0:v][1:v]concat=n=2:v=1:a=0,drawtext=text='SAVE TEN MINUTES':fontcolor=white:fontsize=20:x=10:y=50[v]",
        '-map','[v]','-map','2:a','-c:v','libx264','-threads','1','-pix_fmt','yuv420p','-c:a','aac','-shortest',str(video)],check=True)
    params=StdioServerParameters(command=str(Path('start-mcp.sh').resolve()))
    async with stdio_client(params) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            names=[t.name for t in (await session.list_tools()).tools]
            assert 'get_creation_context' in names and 'record_reference_metrics' in names
            async def call(name,args):
                response=await session.call_tool(name,args)
                value=json.loads(response.content[0].text)
                assert not value.get('error'),value
                return value,response
            reference,_=await call('add_reference',{'title':'Synthetic reference demo — not an Instagram video',
                'platform':'uploaded','target_country':'MY','language':'en','niche':'productivity',
                'audience':'English-speaking office workers',
                'notes':'Generated local red/blue test clip with synthetic tone and text. No real creator, audience or performance claims.'})
            id=reference['id']
            uploaded,_=await call('attach_reference_media',{'reference_id':id,'path':video.name})
            assert uploaded['status']=='uploaded'
            analyzed,_=await call('analyze_reference',{'reference_id':id})
            assert analyzed['status']=='ready',analyzed
            inspected,images=await call('inspect_reference',{'reference_id':id,'max_frames':3})
            assert sum(c.type=='image' for c in images.content)==3
            target={'reference_ids':[id],'goal':'An original short desk-reset routine, using broad caption/cut techniques as inspiration',
                'niche':'productivity','language':'en','target_country':'MY','audience':'English-speaking office workers',
                'duration_seconds':20,'target_aspect_ratio':'9:16'}
            context,context_images=await call('get_creation_context',target)
            assert context['generation_performed'] is False
            count=sum(c.type=='image' for c in context_images.content)
            assert count>=3
            result={'dataset':'EXPLICIT SYNTHETIC DEMONSTRATION — not organic social-trend evidence',
                'reference_id':id,'tool_count':len(names),'target':target,
                'analysis':analyzed['analysis'],'context_image_count':count,'mcp_protocol_passed':True,
                'reference_url':f'http://127.0.0.1:8000/api/v1/references/{id}',
                'media_source_match':reference['media_source_match'],
                'audience_geography_verified':reference['audience_geography_verified']}
            Path('verification/creative-reference-demo.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
            print(json.dumps({'reference_id':id,'tool_count':len(names),'duration':analyzed['analysis']['duration_seconds'],
                'frames':len(analyzed['analysis']['frames']),'scene_changes':analyzed['analysis']['scene_changes'],
                'speech_status':analyzed['analysis']['speech']['status'],'context_image_count':count},indent=2))
asyncio.run(main())
