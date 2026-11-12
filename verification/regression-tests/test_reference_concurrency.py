import asyncio,json,os
import pytest
from app.reference_schemas import AnnotationInput

@pytest.mark.asyncio
async def test_concurrent_annotations_keep_both_accepted_additions(monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from sqlalchemy.engine import make_url
    from app.database import initialize_database
    from app.models import VideoReference
    import app.services.reference_library as library
    if not os.getenv('TEST_DATABASE_URL'):pytest.skip('PostgreSQL required')
    url=os.environ['TEST_DATABASE_URL'];assert make_url(url).database=='social_trends_regression'
    engine=create_async_engine(url);factory=async_sessionmaker(engine,expire_on_commit=False)
    await initialize_database(engine)
    try:
        async with factory() as db:
            row=VideoReference(title='Synthetic concurrency fixture',status='ready',media_sha256='0'*64,
                analysis_json=json.dumps({'duration_seconds':4,'frames':[{'id':'frame_00','timestamp':0}]}))
            db.add(row);await db.commit();id=row.id
        original=library.get_reference;read=[];both=asyncio.Event()
        async def synchronize_unlocked_read(db,id):
            row=await original(db,id);read.append(1)
            if len(read)==2:both.set()
            await asyncio.wait_for(both.wait(),3)
            return row
        monkeypatch.setattr(library,'get_reference',synchronize_unlocked_read)
        async def add(text):
            async with factory() as db:
                value=AnnotationInput(annotations=[{'kind':'observed','basis':'frame','start':0,'end':1,
                    'frame_ids':['frame_00'],'statement':text}])
                await library.annotate(db,id,value);await db.commit()
        await asyncio.wait_for(asyncio.gather(add('First accepted claim'),add('Second accepted claim')),6)
        async with factory() as db:
            row=await db.get(VideoReference,id)
            statements={a['statement'] for a in json.loads(row.annotations_json)}
            assert statements=={'First accepted claim','Second accepted claim'}
    finally:await engine.dispose()
