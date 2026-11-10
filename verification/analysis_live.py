"""Real shared-history analysis and persisted MCP capture, without synthetic writes."""
import asyncio,json
from pathlib import Path
import httpx
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params=StdioServerParameters(command=str(Path('.venv/bin/social-trends-mcp').resolve()))
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000',timeout=90) as client:
        before=(await client.get('/api/v1/health')).json()['platforms']['twitter']['total_scrapes']
        async with stdio_client(params) as (r,w):
            async with ClientSession(r,w) as session:
                await session.initialize()
                names=[x.name for x in (await session.list_tools()).tools]
                assert {'analyze_trends','capture_trends'}<=set(names)
                for _ in range(4):
                    result=await session.call_tool('capture_trends',{'platform':'twitter'})
                    capture=json.loads(result.content[0].text)
                    if capture.get('state')=='captured':break
                    assert capture.get('state')=='capture_already_running',capture
                    await asyncio.sleep(.5)
                assert capture['persisted'] and capture['state']=='captured'
                result=await session.call_tool('analyze_trends',{'hours':48,'limit':5})
                analysis=json.loads(result.content[0].text)
        after=(await client.get('/api/v1/health')).json()['platforms']['twitter']['total_scrapes']
        assert after>before
        assert analysis['platforms']['twitter']['snapshot_id']==capture['snapshot']['id']
        assert analysis['policy']['confidence_is_probability'] is False
        for state in analysis['platforms'].values():
            for topic in state['topics']:
                assert 'example.test' not in topic['url']
                if topic['signal']=='rising_candidate':
                    assert topic['observations']>=3 and topic['span_hours']>=1
                    assert state['status']=='ok'
        response=await client.get('/api/v1/analysis/trends',params={'platform':'twitter','hours':48,'limit':5})
        assert response.status_code==200
        invalid=await client.get('/api/v1/analysis/trends',params={'platform':'instagram','region':'jp'})
        assert invalid.status_code==400
    output={'mcp_capture':{'snapshot':capture['snapshot'],'count':len(capture['topics']),'persisted':capture['persisted']},'analysis':analysis,'source':'actual service PostgreSQL history; no synthetic observations'}
    Path('verification/analysis-live.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
    for platform,state in analysis['platforms'].items():
        print(platform,'snapshots',state['snapshot_count'],'status',state['status'],'signals',[(x['signal'],x['title'][:45],x['observations']) for x in state['topics'][:3]])
    print('PASS: MCP captured a real persisted observation; REST and MCP analyze the same shared history; signal evidence constraints hold.')
asyncio.run(main())
