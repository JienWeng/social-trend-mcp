import shutil,subprocess
from pathlib import Path
import pytest

@pytest.fixture
def sample_video(tmp_path):
    if not shutil.which('ffmpeg'):pytest.skip('ffmpeg required')
    path=tmp_path/'sample.mp4'
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
        '-f','lavfi','-i','color=c=red:s=320x240:r=10:d=2',
        '-f','lavfi','-i','color=c=blue:s=320x240:r=10:d=2',
        '-f','lavfi','-i','sine=frequency=440:sample_rate=16000:duration=4',
        '-filter_complex',"[0:v][1:v]concat=n=2:v=1:a=0,drawtext=text='SAVE TEN MINUTES':fontcolor=white:fontsize=20:x=10:y=50[v]",
        '-map','[v]','-map','2:a','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',
        '-c:a','aac','-shortest',str(path)],check=True)
    return path

@pytest.mark.asyncio
async def test_actual_media_analysis_measures_instead_of_inventing_style(sample_video,tmp_path):
    from app.services.reference_media import analyze_media
    result=await analyze_media(sample_video,tmp_path/'analysis')
    assert 3.9<=result['duration_seconds']<=4.2
    assert result['width']==320 and result['height']==240
    assert len(result['frames'])>=4
    assert any(abs(t-2)<.2 for t in result['scene_changes']['timestamps'])
    assert result['audio']['present'] is True and result['audio']['rms_dbfs'] is not None
    assert result['speech']['status']=='not_configured'
    assert result['visual_interpretation']['status']=='requires_client_model'
    assert all(Path(tmp_path/'analysis'/frame['filename']).is_file() for frame in result['frames'])
    if shutil.which('tesseract'):
        assert 'SAVE' in ' '.join(frame['ocr'].get('text','') for frame in result['frames']).upper()

@pytest.mark.asyncio
async def test_untrusted_manifest_is_rejected_before_decoder(tmp_path):
    from app.services.reference_media import probe_media
    path=tmp_path/'fake.mp4';path.write_text('#EXTM3U\nhttps://127.0.0.1/private')
    with pytest.raises(ValueError,match='MP4|WebM'):await probe_media(path)

@pytest.mark.asyncio
async def test_process_output_limit_is_enforced_before_child_exit():
    import sys,time
    from app.services.reference_media import execute
    started=time.monotonic()
    with pytest.raises(ValueError,match='output exceeded'):
        await execute([sys.executable,'-c',"import sys,time;sys.stdout.buffer.write(b'x'*(3*1024*1024));sys.stdout.flush();time.sleep(30)"],timeout=3)
    assert time.monotonic()-started<2

@pytest.mark.asyncio
async def test_decoder_and_filter_threads_are_bounded_before_input(sample_video,tmp_path,monkeypatch):
    import app.services.reference_media as module
    original=module.execute;commands=[]
    async def track(args,**kwargs):
        commands.append(list(map(str,args)))
        return await original(args,**kwargs)
    monkeypatch.setattr(module,'execute',track)
    await module.analyze_media(sample_video,tmp_path/'threads')
    for args in commands:
        if args[0]=='ffmpeg':
            assert args.index('-threads')<args.index('-i')
            assert args[args.index('-filter_threads')+1]=='1'
            assert args[args.index('-filter_complex_threads')+1]=='1'
