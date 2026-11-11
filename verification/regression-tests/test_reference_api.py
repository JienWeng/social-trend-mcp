import json,os
from pathlib import Path
import httpx,pytest
from test_reference_media import sample_video

@pytest.mark.asyncio
async def test_reference_media_and_creative_brief_lifecycle(sample_video,tmp_path,monkeypatch):
    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from sqlalchemy.engine import make_url
    from app.database import initialize_database,get_db
    from app.config import Settings
    from app.routers.references import router
    import app.services.reference_media as media
    import app.services.reference_library as library
    import app.routers.references as routes
    if not os.getenv('TEST_DATABASE_URL'):pytest.skip('PostgreSQL required')
    url=os.environ['TEST_DATABASE_URL'];assert make_url(url).database=='social_trends_regression'
    engine=create_async_engine(url);factory=async_sessionmaker(engine,expire_on_commit=False)
    await initialize_database(engine)
    settings=Settings(_env_file=None,reference_storage_dir=str(tmp_path/'library'),reference_max_upload_bytes=1024*1024)
    for module in [media,library,routes]:monkeypatch.setattr(module,'get_settings',lambda:settings)
    app=FastAPI();app.include_router(router)
    async def db():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except BaseException:
                await session.rollback();raise
    app.dependency_overrides[get_db]=db
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test',timeout=120) as client:
            response=await client.post('/api/v1/references',json={'title':'Synthetic test','platform':'uploaded','target_country':'MY','language':'en','niche':'coffee'})
            assert response.status_code==201,response.text
            row=response.json();id=row['id']
            assert row['status']=='metadata_only' and row['audience_geography_verified'] is False
            assert (await client.post(f'/api/v1/references/{id}/analyze')).status_code==422
            response=await client.put(f'/api/v1/references/{id}/media',content=b'#EXTM3U\nhttp://localhost/private')
            assert response.status_code==422
            assert (await client.put(f'/api/v1/references/{id}/media',content=b'x'*(1024*1024+1))).status_code==413
            async def too_large():
                yield b'x'*600000
                yield b'x'*600000
            assert (await client.put(f'/api/v1/references/{id}/media',content=too_large())).status_code==413
            assert not list((tmp_path/'library'/id).glob('upload-*'))
            response=await client.put(f'/api/v1/references/{id}/media',content=sample_video.read_bytes())
            assert response.status_code==200,response.text
            assert (await client.put(f'/api/v1/references/{id}/media',content=sample_video.read_bytes())).status_code==409
            response=await client.post(f'/api/v1/references/{id}/analyze')
            assert response.status_code==200,response.text
            row=response.json();assert row['status']=='ready'
            frame=row['analysis']['frames'][0]
            image=await client.get(frame['url'])
            assert image.status_code==200 and image.headers['content-type']=='image/jpeg'
            invalid={'annotations':[{'kind':'observed','basis':'frame','start':0,'end':1,'statement':'Fake','frame_ids':['missing']}]}
            assert (await client.post(f'/api/v1/references/{id}/annotations',json=invalid)).status_code==422
            wrong_time={'annotations':[{'kind':'observed','basis':'frame','start':2,'end':3,'statement':'Wrong time','frame_ids':[frame['id']]}]}
            assert (await client.post(f'/api/v1/references/{id}/annotations',json=wrong_time)).status_code==422
            valid={'annotations':[{'kind':'observed','basis':'frame','start':0,'end':1,'statement':'High contrast text','frame_ids':[frame['id']]}]}
            assert (await client.post(f'/api/v1/references/{id}/annotations',json=valid)).status_code==200
            transcript={'segments':[{'start':0,'end':1,'text':'User supplied words'}]}
            assert (await client.put(f'/api/v1/references/{id}/transcript',json=transcript)).status_code==200
            request={'reference_ids':[id],'goal':'Original morning coffee video','niche':'coffee','language':'en','target_country':'MY','duration_seconds':15}
            context=await client.post('/api/v1/creation/context',json=request)
            assert context.status_code==200 and context.json()['generation_performed'] is False
            assert context.json()['references'][0]['annotations'][0]['validation']=='client_claim_unverified'
            brief={**request,'title':'Original coffee reset','concept':'A new coffee preparation routine','hook':'Reset before your next meeting',
                'storyboard':[{'start':0,'end':15,'visual':'Original shot of preparing coffee','spoken_text':'A brief reset for your next task'}],
                'reference_evidence':[{'reference_id':id,'frame_ids':[frame['id']],'start':0,'end':1,'statement':'High contrast captions','kind':'observed'}]}
            response=await client.post('/api/v1/creation/briefs',json=brief)
            assert response.status_code==201,response.text
            assert response.json()['review_status']=='unreviewed'
            assert len((await client.get('/api/v1/creation/briefs')).json()['briefs'])>=1
            assert (await client.post(f'/api/v1/references/{id}/metrics',json={'likes':100,'observed_at':'2026-11-10T00:00:00Z'})).status_code==201
            result=await client.post(f'/api/v1/references/{id}/metrics',json={'likes':150,'observed_at':'2026-11-10T02:00:00Z'})
            assert result.status_code==201 and result.json()['deltas']['likes']['change']==50
            assert result.json()['verification']=='user_supplied_unverified'
            assert (await client.get('/api/v1/references',params={'target_country':'MY','niche':'coffee'})).json()['references']
    finally:await engine.dispose()
