"""Live checks for five feeds, regional persistence, search and MCP."""
import asyncio,json,time
from pathlib import Path
import httpx,websockets
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def wait_event(ws,client,platform,region):
    deadline=time.monotonic()+70
    while time.monotonic()<deadline:
        event=json.loads(await asyncio.wait_for(ws.recv(),70))
        if event['platform']!=platform or event['snapshot']['region']!=region:continue
        response=await client.get(f'/api/v1/trends/{platform}',params={'region':region})
        data=response.json()['data']
        if data['snapshot']['id']!=event['snapshot']['id']:continue
        assert data['topics']==event['topics']
        assert data['snapshot']['status']=='success',data['snapshot']
        assert data['freshness']['state']=='fresh'
        return data
    raise AssertionError('No matching event')

async def main():
    out={}
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8000',timeout=70) as client:
        initial=(await client.get('/api/v1/trends')).json()['data']
        assert set(initial)=={'twitter','tiktok','youtube','instagram','douyin'}
        assert all(d['snapshot']['status']=='success' and d['topics'] for d in initial.values())
        out['initial']={p:{'snapshot':d['snapshot'],'count':len(d['topics'])} for p,d in initial.items()}
        for url in ['/api/v1/trends/twitter?region=invalid','/api/v1/trends/instagram?region=jp','/api/v1/trends/twitter?region=cn','/api/v1/search/exact?q=test&platforms=invalid']:
            assert (await client.get(url)).status_code==400
        assert (await client.get('/api/v1/trends/history/twitter?hours=-1')).status_code==422
        async with websockets.connect('ws://127.0.0.1:8000/ws/trends') as ws:
            await ws.send('ping');assert await ws.recv()=='pong'
            out['regional']={}
            for platform,region in [('twitter','jp'),('youtube','jp'),('tiktok','jp'),('douyin','cn')]:
                accepted=await client.post('/api/v1/refresh',params={'platform':platform,'region':region})
                assert accepted.status_code==202
                data=await wait_event(ws,client,platform,region)
                assert all(t['region']==region for t in data['topics'])
                out['regional'][platform]=data
                history=(await client.get(f'/api/v1/trends/history/{platform}',params={'region':region})).json()['data']
                assert history and all(d['snapshot']['region']==region for d in history)
            for platform in ['instagram']:
                assert (await client.post('/api/v1/refresh',params={'platform':platform})).status_code==202
                out[platform]=await wait_event(ws,client,platform,'global')
        global_twitter=(await client.get('/api/v1/trends/twitter')).json()['data']
        assert global_twitter['snapshot']['region']=='global'
        assert all(t['region']=='global' for t in global_twitter['topics'])
        exact=(await client.get('/api/v1/search/exact',params={'q':'zznotreal98765','platforms':'twitter'})).json()
        assert exact['total']==0 and exact['coverage']['twitter']['status']=='ok'
        out['negative_search']=exact
        title=out['regional']['douyin']['topics'][0]['title']
        positive=(await client.get('/api/v1/search/exact',params={'q':title,'platforms':'douyin','region':'cn'})).json()
        assert positive['total']>=1
        out['positive_search']=positive
        out['health']=(await client.get('/api/v1/health')).json()
        assert out['health']['status']=='healthy'
    params=StdioServerParameters(command=str(Path('.venv/bin/social-trends-mcp').resolve()))
    async with stdio_client(params) as (r,w):
        async with ClientSession(r,w) as session:
            await session.initialize()
            tools=await session.list_tools()
            out['mcp_tools']=[x.name for x in tools.tools]
            assert 'search_trends' in out['mcp_tools']
            result=await session.call_tool('get_all_trends',{'limit':1})
            text='\n'.join(x.text for x in result.content if hasattr(x,'text'))
            assert all(p.upper() in text for p in ['twitter','tiktok','youtube','instagram','douyin']),text
            assert 'weekly' in text.lower() and 'heat' in text.lower()
            out['mcp_all']=text
            result=await session.call_tool('search_trends',{'query':'zznotreal98765','platforms':['twitter']})
            text='\n'.join(x.text for x in result.content if hasattr(x,'text'))
            assert 'Found 0' in text
            out['mcp_negative']=text
    Path('verification/final-e2e.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
    print('PASS: five live feeds; JP/CN persisted regions and histories; valid/invalid search; committed WebSocket updates; MCP all-platform and alias; healthy status.')
asyncio.run(main())
