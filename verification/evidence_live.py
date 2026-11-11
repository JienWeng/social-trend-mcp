"""Read-only live report checks; no source fetch or capture is invoked."""
import asyncio,json,time
from pathlib import Path
from datetime import datetime,timezone
import httpx
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from app.source_control import SourceControl
from app.config import get_settings

async def main():
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000',timeout=60) as client:
        for _ in range(150):
            try:
                response=await client.get('/api/v1/collection/status')
                if response.status_code==200:
                    before=response.json()['platforms']
                    if not any(s['in_progress'] for s in before.values()):break
            except httpx.HTTPError:pass
            await asyncio.sleep(.2)
        else:raise AssertionError('Service/source attempts did not settle')
        started=time.monotonic()
        response=await client.get('/api/v1/analysis/report')
        response.raise_for_status();report=response.json()
        elapsed=time.monotonic()-started
        assert report['read_only'] and report['truth_probability'] is None
        for name,state in report['platforms'].items():
            assert state['quality']['factual_truth']['status']=='not_checked'
            assert state['quality']['source_fidelity']['status']=='not_independently_verified'
            assert state['next_action']['action']
        params=StdioServerParameters(command=str(Path('start-mcp.sh').resolve()))
        async with stdio_client(params) as (reader,writer):
            async with ClientSession(reader,writer) as session:
                await session.initialize()
                tools=[t.name for t in (await session.list_tools()).tools]
                assert len(tools)==22 and 'get_report' in tools
                response=await session.call_tool('get_report',{})
                mcp_report=json.loads(response.content[0].text)
                assert mcp_report['read_only'] and set(mcp_report['platforms'])==set(report['platforms'])
        after=(await client.get('/api/v1/collection/status')).json()['platforms']
        assert {p:s['attempts'] for p,s in before.items()}=={p:s['attempts'] for p,s in after.items()}
        disk=SourceControl(path=get_settings().collection_control_path).status()
        assert {p:s['attempts'] for p,s in disk.items()}=={p:s['attempts'] for p,s in after.items()}
        health=(await client.get('/api/v1/health')).json()
        schema=(await client.get('/openapi.json')).json()
        guide=(await client.get('/llms.txt')).text
        assert guide==Path('llms.txt').read_text()
        catalog=Path('docs/ENDPOINTS.md').read_text()
        for path in schema['paths']:assert ('`'+path+'`') in catalog,path
        output={'verified_at':datetime.now(timezone.utc).isoformat(),'health':health['status'],
            'read_only':True,'source_attempt_counters_unchanged':True,'saved_state_counters_match':True,
            'mcp_tool_count':len(tools),'http_report_seconds':round(elapsed,3),
            'documented_application_http_paths':len(schema['paths']),
            'platforms':{name:{'freshness':s['freshness'],'sample_count':s['quality']['topic_count'],
                'provenance':s['quality']['provenance'],'metric_coverage':s['quality']['metrics'],
                'headline':s['headline'],'truth':s['quality']['factual_truth'],'next_action':s['next_action']}
                for name,s in report['platforms'].items()},
            'limits':'Single local timing, not a throughput benchmark; source URLs are not independent corroboration.'}
        Path('verification/evidence-live.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
        print(json.dumps(output,ensure_ascii=False,indent=2))
asyncio.run(main())
