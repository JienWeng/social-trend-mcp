"""Save an original draft authored after actual inspection of real test-video frames.
Re-running replays this example; it does not invoke a fresh generation model.
"""
import asyncio,json
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    path=Path('verification/real-reference-test.json');test=json.loads(path.read_text())
    id=test['reference_id'];frames=test['analysis']['frames'];first=frames[0];middle=frames[3];last=frames[-1]
    annotations={'reference_id':id,'annotations':[
        {'kind':'observed','basis':'frame','start':0,'end':1,'frame_ids':[first['id']],
         'statement':'Portrait close framing shows a metal pitcher, a tilted white cup, brown coffee and a visible pale milk stream.'},
        {'kind':'observed','basis':'frame','start':middle['timestamp']-.1,'end':middle['timestamp']+.5,'frame_ids':[middle['id']],
         'statement':'The sampled frame shows hands and the pitcher/cup against white clothing; no reliable designed subtitle overlay is visible.'},
        {'kind':'observed','basis':'frame','start':17.4,'end':17.7,'frame_ids':[last['id']],
         'statement':'The final sampled frame is wider and shows the person holding the filled cup, with a wooden counter and shelves in view.'},
        {'kind':'inferred','basis':'frame','start':0,'end':17.7,'frame_ids':[first['id'],last['id']],
         'statement':'A process-detail-to-result-reveal structure is a possible creative interpretation; exact camera movement and viewer response are not established by these samples.'}]}
    brief={**test['target'],'generator':'client_model','title':'Make the pour the story',
        'concept':'An original20-second vertical coffee video using close process details, a restrained white/brown/metal palette and a final result reveal. Shoot new footage with your own cup, hands and setting.',
        'hook':'Watch this cup come together.',
        'storyboard':[
            {'start':0,'end':3,'visual':'Original tight shot of coffee surface as a plain metal pitcher enters.',
             'spoken_text':'Watch this cup come together.','on_screen_text':'START CLOSE','editing':'Open immediately on the action; original caption is a new choice, not extracted source text.'},
            {'start':3,'end':8,'visual':'Own side-angle footage of a controlled milk pour into a plain white cup.',
             'spoken_text':'','on_screen_text':'','editing':'Hold the detail shot; preserve room for the action rather than adding unnecessary transitions.'},
            {'start':8,'end':13,'visual':'New overhead shot showing the changing coffee surface.',
             'spoken_text':'','on_screen_text':'LET IT UNFOLD','editing':'One intentional cut to a distinct angle; no claim that this is the reference camera movement.'},
            {'start':13,'end':17,'visual':'Own macro shot of the finished surface and cup rim.',
             'spoken_text':'','on_screen_text':'THE REVEAL','editing':'Give the finished detail a short hold.'},
            {'start':17,'end':20,'visual':'Wider original shot placing the cup on a wooden table, without copying source identity, logos or setting.',
             'spoken_text':'Your next cup, your own little ritual.','on_screen_text':'YOUR NEXT CUP','editing':'Simple closing reveal; retain vertical composition.'}],
        'editing_notes':['Broad inspiration: close-up process details, neutral coffee/ceramic/metal tones and wider result reveal.',
            'Use entirely new footage, plain clothing and your own setting; do not reuse original media, logos, identity or soundtrack.',
            'On-screen labels and voiceover are new creative suggestions. The reference transcript and audio meaning are unknown.',
            'No thresholded scene changes were detected; that does not prove that the source contains no edits.'],
        'reference_evidence':[
            {'reference_id':id,'frame_ids':[first['id']],'start':0,'end':1,'kind':'observed',
             'statement':'Tight composition centers the pitcher, cup and milk stream.'},
            {'reference_id':id,'frame_ids':[last['id']],'start':17.4,'end':17.7,'kind':'observed',
             'statement':'A wider final sample presents the filled cup, supporting a result-reveal motif.'}],
        'unknowns':['Speech transcription is not configured; no source words or music genre were inferred.',
            'OCR generated spurious characters on these sampled frames; its text was not used as caption evidence.',
            'Frame samples do not establish exact continuous camera motion or exclude every cut.',
            'Target MY/en is a requested output market/language, not verified audience geography.',
            'There are no verified engagement metrics or evidence that this source is trending.',
            'This draft is unreviewed; originality and likely performance are not certified.']}
    params=StdioServerParameters(command=str(Path('start-mcp.sh').resolve()))
    async with stdio_client(params) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            result=await session.call_tool('annotate_reference',annotations)
            value=json.loads(result.content[0].text);assert not value.get('error'),value
            result=await session.call_tool('save_creative_brief',brief)
            saved=json.loads(result.content[0].text);assert saved.get('id'),saved
    test['saved_brief']=saved
    test['manual_visual_checks']=[{'frame_id':f['id'],'source_timestamp':f['timestamp']} for f in [first,middle,last]]
    test['quality_findings']={'workflow':'passed','media_integrity':'matched_published_sha1',
        'metadata':'17.7s and360x640 match Commons structured metadata',
        'ocr':'spurious_characters_observed_not_used_as_caption_evidence',
        'speech':'not_configured','scene_detection':'zero_thresholded_changes_not_proof_of_no_edits',
        'semantic_check':'Three actual keyframes inspected; no continuous-motion/audio interpretation claimed',
        'trend_performance':'unknown_no_verified_engagement_data'}
    path.write_text(json.dumps(test,ensure_ascii=False,indent=2))
    print(json.dumps({'reference_id':id,'brief_id':saved['id'],'title':saved['title'],'review_status':saved['review_status'],
                     'quality_findings':test['quality_findings']},indent=2))
asyncio.run(main())
