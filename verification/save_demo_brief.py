"""Replay an original example draft authored after inspecting the extracted demo frames.
This script saves that draft; it does not invoke a fresh generation model.
"""
import asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    path=Path('verification/creative-reference-demo.json')
    demo=json.loads(path.read_text());id=demo['reference_id']
    first=demo['analysis']['frames'][0]
    blue=next(frame for frame in demo['analysis']['frames'] if frame['timestamp']>=2)
    annotations={'reference_id':id,'annotations':[
        {'kind':'observed','basis':'frame','start':0,'end':1,'frame_ids':[first['id']],
         'statement':'White uppercase text is left aligned near the top of a solid red background.'},
        {'kind':'observed','basis':'frame','start':2,'end':2.5,'frame_ids':[blue['id']],
         'statement':'The sampled frame shows white uppercase text over a solid blue background.'},
        {'kind':'inferred','basis':'frame','start':0,'end':3.9,'frame_ids':[first['id'],blue['id']],
         'statement':'High-contrast title cards may help emphasize a concise message; this is an interpretation, not measured viewer behavior.'}]}
    brief={**demo['target'],'generator':'client_model','title':'One clear space, one next action',
        'concept':'An original vertical desk-reset routine for office workers, using broad high-contrast caption and section-cut techniques.',
        'hook':'Before your next meeting, reset this one thing.',
        'storyboard':[
            {'start':0,'end':3,'visual':'Original close-up of a cluttered desk; hand pauses above it.',
             'spoken_text':'Before your next meeting, reset this one thing.','on_screen_text':'RESET YOUR NEXT STEP','editing':'Immediate opening shot; high-contrast caption.'},
            {'start':3,'end':6,'visual':'Overhead original footage clearing a small working area.',
             'spoken_text':'You only need one clear space.','on_screen_text':'ONE CLEAR SPACE','editing':'Hard cut to an overhead angle.'},
            {'start':6,'end':11,'visual':'Place water beside a notebook; keep the composition simple.',
             'spoken_text':'Put the essentials within reach.','on_screen_text':'KEEP WHAT YOU NEED','editing':'Two short original detail shots; no reference footage reused.'},
            {'start':11,'end':16,'visual':'Write one next action on a new note and place it in the clear area.',
             'spoken_text':'Write the next action, not the whole to-do list.','on_screen_text':'ONE NEXT ACTION','editing':'Cut to close-up; hold long enough for the words to be read.'},
            {'start':16,'end':20,'visual':'Wider original shot of the clean working area as the person starts.',
             'spoken_text':'Try this before your next call.','on_screen_text':'START SMALL','editing':'A simple closing shot; avoid claiming measured productivity benefits.'}],
        'editing_notes':['Use broad high-contrast typography and clear section cuts as inspiration.',
            'Shoot entirely original desk footage; do not copy source text, footage, branding or assets.',
            'Voiceover is a new suggestion, not a description of the reference audio.'],
        'reference_evidence':[
            {'reference_id':id,'frame_ids':[first['id']],'start':0,'end':1,'kind':'observed',
             'statement':'White uppercase text over a solid red field supports using broad high-contrast caption techniques.'},
            {'reference_id':id,'frame_ids':[blue['id']],'start':2,'end':2.5,'kind':'observed',
             'statement':'The blue sampled title card contrasts with the red opening frame.'}],
        'unknowns':['Reference audio meaning/music style was not analyzed; no ASR model was configured.',
            'Target country MY is a requested market, not verified audience geography.',
            'This example uses a synthetic reference, not organic social-trend evidence.',
            'Originality and likely audience performance have not been independently evaluated.']}
    params=StdioServerParameters(command=str(Path('start-mcp.sh').resolve()))
    async with stdio_client(params) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            result=await session.call_tool('annotate_reference',annotations)
            value=json.loads(result.content[0].text);assert not value.get('error'),value
            result=await session.call_tool('save_creative_brief',brief)
            saved=json.loads(result.content[0].text);assert saved.get('id'),saved
            result=await session.call_tool('list_creative_briefs',{'limit':20})
            assert saved['id'] in [value['id'] for value in json.loads(result.content[0].text)['briefs']]
    demo['saved_brief']=saved;demo['frame_inspection']='Connected assistant inspected red and blue extracted JPEG frames before authoring this example.'
    path.write_text(json.dumps(demo,ensure_ascii=False,indent=2))
    print(json.dumps({'reference_id':id,'brief_id':saved['id'],'title':saved['title'],
        'status':saved['review_status'],'note':'Original example script/storyboard saved; no final video was rendered.'},indent=2))
asyncio.run(main())
