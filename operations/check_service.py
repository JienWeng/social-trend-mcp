"""Read-only local readiness check; never invokes source fetch/capture tools."""
import argparse,asyncio,json,os,sys,time
from pathlib import Path
import httpx
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def run(args):
    base=os.environ.get('API_BASE_URL','http://127.0.0.1:8000').rstrip('/')
    started=time.monotonic()
    async with httpx.AsyncClient(base_url=base,timeout=60) as client:
        health=await client.get('/api/v1/health');health.raise_for_status()
        params={'limit':1}
        if args.platform:params['platform']=args.platform
        response=await client.get('/api/v1/analysis/report',params=params);response.raise_for_status()
        report=response.json()
    names=[]
    server=StdioServerParameters(command=str(Path(__file__).resolve().parent.parent/'start-mcp.sh'))
    async with stdio_client(server) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            await session.initialize()
            names=[tool.name for tool in (await session.list_tools()).tools]
            assert 'get_report' in names
            result=await session.call_tool('get_report',params)
            mcp=json.loads(result.content[0].text)
            assert mcp['read_only'] and mcp['truth_probability'] is None
    result={'backend_status':health.json()['status'],'mcp_connected':True,'tool_count':len(names),
            'read_only':True,'elapsed_seconds':round(time.monotonic()-started,3),
            'platforms':{name:{'freshness':state['freshness'].get('state'),
                'sample_count':state['quality']['topic_count'],'headline':state['headline'],
                'next_action':state['next_action'],'factual_truth':state['quality']['factual_truth']['status']}
                for name,state in report['platforms'].items()}}
    if args.json:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print(f"Backend: {result['backend_status']} | MCP: connected | Tools: {len(names)}")
        for name,state in result['platforms'].items():
            print(f"{name}: {state['freshness']} | {state['sample_count']} sampled items | {state['headline']}")
            print(f"  Next: {state['next_action']['action']} | factual truth: {state['factual_truth']}")
        print("Read-only check; no collection triggered. Source claims are not fact-checked.")
    return 0 if result['backend_status']=='healthy' else 2

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true')
    parser.add_argument('--platform',choices=['twitter','tiktok','youtube','instagram','douyin'])
    args=parser.parse_args()
    try:return asyncio.run(run(args))
    except Exception as error:
        print(f"Check failed: {error}. Run ./setup.sh and ./manage-service.sh start; verify API_BASE_URL.",file=sys.stderr)
        return 1
if __name__=='__main__':sys.exit(main())
