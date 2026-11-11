"""Real source-only capture, unchanged-content reuse and MCP checkpoint report."""
import asyncio,json
from datetime import datetime,timedelta,timezone
from pathlib import Path
import httpx
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000',timeout=90) as client:
        for _ in range(100):
            try:
                ready=await client.get('/openapi.json')
                if ready.status_code==200:break
            except httpx.HTTPError:pass
            await asyncio.sleep(.2)
        else:raise AssertionError('API did not become ready')
        async def capture():
            for _ in range(100):
                response=await client.post('/api/v1/analysis/capture/twitter')
                if response.status_code==202:
                    await asyncio.sleep(.2);continue
                response.raise_for_status();return response.json()
            raise AssertionError('Capture remained busy')
        first=await capture();second=await capture()
        a,b=first['snapshot'],second['snapshot']
        assert a['id']!=b['id']
        assert b['content_reused'] and b['content_snapshot_id']==(a['content_snapshot_id'] or a['id'])
        assert [t['id'] for t in first['topics']]==[t['id'] for t in second['topics']]
        assert a['fetched_at']==b['fetched_at'],'One cached fetch should retain its retrieval timestamp'
        since=a['finished_at']
        report=(await client.get('/api/v1/analysis/changes',params={'since':since,'platform':'twitter'})).json()
        state=report['platforms']['twitter']
        assert state['baseline']['id']==a['id'] and state['current']['id']==b['id']
        assert state['counts']['changed']==0 and state['counts']['added']==0 and state['counts']['removed']==0
        assert state['counts']['unchanged']==len(second['topics'])
        params=StdioServerParameters(command=str(Path('.venv/bin/social-trends-mcp').resolve()))
        async with stdio_client(params) as (reader,writer):
            async with ClientSession(reader,writer) as session:
                await session.initialize()
                tools=[t.name for t in (await session.list_tools()).tools]
                assert len(tools)==10 and {'get_changes','get_report'}<=set(tools)
                response=await session.call_tool('get_changes',{'since':since,'platform':'twitter'})
                mcp_report=json.loads(response.content[0].text)
                assert mcp_report['platforms']['twitter']['counts']==state['counts']
                direct=await session.call_tool('get_trends',{'platform':'twitter','limit':3})
                assert second['topics'][0]['title'] in direct.content[0].text
        history=(await client.get('/api/v1/trends/history/twitter')).json()['data']
        assert history[0]['snapshot']['id']==b['id'] and history[0]['topics']==second['topics']
        schema=(await client.get('/openapi.json')).json()
        assert '/api/v1/feeds/{platform}' in schema['paths']
        assert '/api/v1/analysis/changes' in schema['paths']
        guide=await client.get('/llms.txt')
        assert guide.text==Path('llms.txt').read_text()
        result={'verified_at':datetime.now(timezone.utc).isoformat(),'first':a,'second':b,
                'counts':state['counts'],'content_topic_ids_reused':True,'retrieval_timestamp_preserved':True,
                'mcp_tool_count':len(tools),'rest_mcp_report_agree':True,
                'application_http_paths':sorted(schema['paths']),
                'note':'Real public source data only. New captures persisted; no synthetic service-history writes.'}
        Path('verification/monitoring-live.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
        print(json.dumps(result,ensure_ascii=False,indent=2))
asyncio.run(main())
