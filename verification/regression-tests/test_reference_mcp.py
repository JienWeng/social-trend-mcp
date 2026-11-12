import base64,json
import httpx,pytest

@pytest.mark.asyncio
async def test_inspection_returns_timestamped_image_blocks(monkeypatch):
    import app.mcp_references as module
    id='a'*32;calls=[]
    class Client:
        def __init__(self,*a,**k):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*a):pass
        async def request(self,method,url,**kw):
            calls.append(url)
            return httpx.Response(200,json={'id':id,'status':'ready','analysis':{'frames':[
                {'id':'frame_00','timestamp':0,'ocr':{'text':'HELLO','words':[{'text':'HELLO'}]}}]}},request=httpx.Request(method,url))
        async def get(self,url):
            calls.append(url)
            return httpx.Response(200,content=b'jpeg-test',headers={'Content-Type':'image/jpeg'},request=httpx.Request('GET',url))
    monkeypatch.setattr(module.httpx,'AsyncClient',Client)
    content=await module.call_reference_tool('inspect_reference',{'reference_id':id,'max_frames':1})
    assert content[2].type=='image' and base64.b64decode(content[2].data)==b'jpeg-test'
    assert 'source timestamp 0' in content[1].text
    assert len(calls)==2
    assert 'words' not in json.loads(content[0].text)['analysis']['frames'][0]['ocr']

@pytest.mark.asyncio
async def test_inbox_import_rejects_external_path_without_http(tmp_path,monkeypatch):
    import app.mcp_references as module
    from app.config import Settings
    inbox=tmp_path/'inbox';inbox.mkdir()
    outside=tmp_path/'outside.mp4';outside.write_bytes(b'secret')
    monkeypatch.setattr(module,'get_settings',lambda:Settings(_env_file=None,reference_inbox_dir=str(inbox)))
    # inbox_file uses its own module settings alias.
    import app.services.reference_media as media
    monkeypatch.setattr(media,'get_settings',module.get_settings)
    with pytest.raises(ValueError,match='inbox'):
        await module.call_reference_tool('attach_reference_media',{'reference_id':'a'*32,'path':str(outside)})

def test_creation_context_compacts_long_transcripts_and_history_explicitly():
    from app.mcp_references import compact
    source={'id':'a'*32,'transcript':{'segments':[{'start':i,'end':i+1,'text':'x'*2000} for i in range(100)]},
        'annotations':[{'statement':'y'*2000} for _ in range(40)],
        'performance':{'observations':[{'views':i} for i in range(200)]},
        'analysis':{'frames':[]}}
    result=compact(source)
    assert sum(len(s['text']) for s in result['transcript']['segments'])<=12000
    assert result['transcript']['context_truncated'] is True
    assert len(result['performance']['observations'])<=10
    assert result['performance']['context_truncated'] is True
    assert len(source['transcript']['segments'])==100
    again=compact(result)
    assert again['transcript']['context_truncated'] is True
    assert again['performance']['context_truncated'] is True
    assert again['performance']['observation_count']==200
