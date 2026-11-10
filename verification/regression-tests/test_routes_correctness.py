import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routers.trends import router
from app.database import get_db
from app.services import trend_service
from app.scrapers.base import TrendItem,ScrapeResult
from app.models import Platform


def client():
    app=FastAPI();app.include_router(router)
    async def db():yield object()
    app.dependency_overrides[get_db]=db
    return TestClient(app)


def test_region_routes_forward_region_and_reject_invalid(monkeypatch):
    calls=[]
    async def latest(db,**kwargs):
        calls.append(kwargs);return {'twitter':{'topics':[],'snapshot':None}}
    monkeypatch.setattr(trend_service,'get_latest_trends',latest)
    with client() as c:
        assert c.get('/api/v1/trends/twitter?region=jp').status_code==200
        assert calls[-1]['region']=='jp'
        assert c.get('/api/v1/trends/twitter?region=cn').status_code==400
        assert c.get('/api/v1/trends?region=invalid').status_code==400
        assert c.get('/api/v1/trends/history/twitter?hours=-2').status_code==422
        assert c.get('/api/v1/search/exact?q=AI&platforms=bogus').status_code==400
        assert c.get('/api/v1/search/exact?q=%20%20').status_code==422


def test_exact_search_includes_observed_trends_without_search_method(monkeypatch):
    import app.routers.trends as routes
    class Scraper:
        async def execute(self):return ScrapeResult(Platform.INSTAGRAM,[TrendItem(1,'Real robotics demo')])
    monkeypatch.setattr(routes,'get_scraper',lambda *args,**kwargs:Scraper())
    with client() as c:
        result=c.get('/api/v1/search/exact?q=robotics&platforms=instagram').json()
        assert result['total']==1
        assert result['results'][0]['title']=='Real robotics demo'
        assert result['coverage']['instagram']['status']=='ok'
