import pytest
from pydantic import ValidationError

def test_reference_labels_are_declared_not_inferred():
    from app.reference_schemas import ReferenceCreate
    value=ReferenceCreate(title='Example',platform='instagram',source_url='https://www.instagram.com/reel/example/',target_country='MY',language='en',niche='coffee')
    assert value.target_country=='MY'
    with pytest.raises(ValidationError):ReferenceCreate(title='x',source_url='file:///etc/passwd')
    with pytest.raises(ValidationError):ReferenceCreate(title='x',source_url='https://user:secret@example.com/video')

def test_reference_paths_cannot_escape_storage(tmp_path):
    from app.services.reference_media import storage_dir,inbox_file
    with pytest.raises(ValueError):storage_dir('../outside',root=tmp_path)
    outside=tmp_path/'outside.mp4';outside.write_bytes(b'private')
    inbox=tmp_path/'inbox';inbox.mkdir()
    (inbox/'link.mp4').symlink_to(outside)
    with pytest.raises(ValueError):inbox_file('link.mp4',root=inbox)

def test_segment_validation_rejects_reversed_or_infinite_timing():
    from app.reference_schemas import TranscriptSegment,Annotation
    with pytest.raises(ValidationError):TranscriptSegment(start=2,end=1,text='bad')
    with pytest.raises(ValidationError):TranscriptSegment(start=0,end=float('inf'),text='bad')
    with pytest.raises(ValidationError):Annotation(kind='observed',basis='frame',start=0,end=1,statement='Nothing cited')

@pytest.mark.asyncio
async def test_reference_tools_are_discoverable():
    import mcp_server as module
    names={tool.name for tool in await module.list_tools()}
    assert {'add_reference','list_references','attach_reference_media','analyze_reference',
            'inspect_reference','annotate_reference','get_creation_context','save_creative_brief','list_creative_briefs'}<=names

def test_reference_performance_does_not_hide_counter_resets():
    from app.services.reference_library import summarize_performance
    records=[{'observed_at':f'2026-11-11T0{i}:00:00+00:00','source_url':'https://example.test','views':value,'likes':None,'comments':None,'shares':None} for i,value in enumerate([100,0,200])]
    result=summarize_performance(records)
    assert result['deltas']['views'] is None
    assert 'views_decreased_or_reset' in result['warnings']
    assert result['verification']=='user_supplied_unverified'
