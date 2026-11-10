import pytest
from app.models import Platform
from app.scrapers.base import ScrapeResult,TrendItem

@pytest.mark.asyncio
async def test_mcp_exact_has_no_manufactured_or_unrelated_matches(monkeypatch):
    import mcp_server as m
    async def fetch(platform,region='global'):
        return ScrapeResult(platform,[TrendItem(1,'Football',volume=1e9),TrendItem(2,'Robotics')])
    monkeypatch.setattr(m,'_fetch',fetch)
    result=await m.call_tool('exact_search',{'query':'madeup987','platforms':['twitter']})
    assert 'Found 0' in result[0].text
    result=await m.call_tool('search_trends',{'query':'Robotics','platforms':['twitter']})
    assert 'Robotics' in result[0].text and 'Football' not in result[0].text

@pytest.mark.asyncio
async def test_mcp_validates_limits_regions_and_filters():
    import mcp_server as m
    for name,args in [('get_trends',{'platform':'twitter','limit':-1}),('exact_search',{'query':'x','platforms':['bogus']}),('get_all_trends',{'region':'madeup'})]:
        result=await m.call_tool(name,args)
        assert 'Invalid' in result[0].text
    tools=await m.list_tools()
    schema=next(x for x in tools if x.name=='get_trends').inputSchema
    assert 'douyin' in schema['properties']['platform']['enum']

@pytest.mark.asyncio
async def test_failed_fetch_is_not_cached(monkeypatch):
    import mcp_server as m
    m._cache.clear();m._cache_time.clear()
    calls=[]
    class Scraper:
        async def execute(self):
            calls.append(1)
            return ScrapeResult(Platform.TWITTER,[],False,'temporary failure')
    monkeypatch.setattr(m,'get_scraper',lambda *a,**kw:Scraper())
    await m._fetch(Platform.TWITTER)
    await m._fetch(Platform.TWITTER)
    assert len(calls)==2
