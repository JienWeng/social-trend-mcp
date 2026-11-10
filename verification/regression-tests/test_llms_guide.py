import httpx
import pytest
from app.main import app

@pytest.mark.asyncio
async def test_llms_guide_is_discoverable_plain_text():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        response=await client.get('/llms.txt')
    assert response.status_code==200
    assert response.headers['content-type'].startswith('text/plain')
    assert '# Social Trends MCP' in response.text
    assert 'capture_trends' in response.text
    assert 'not a platform-wide trends ranking' in response.text
