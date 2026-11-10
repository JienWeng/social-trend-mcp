"""Deliberate local API crash; verify supervisor restarts it and DB data survives."""
import json,os,signal,time,urllib.request
from pathlib import Path

def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000'+path,timeout=3) as response:return json.load(response)

before=get('/api/v1/health')
old=int(Path('.run/api.pid').read_text())
command=Path(f'/proc/{old}/cmdline').read_bytes()
assert b'uvicorn' in command and b'app.main:app' in command
os.kill(old,signal.SIGKILL)
started=time.monotonic();new=None
for _ in range(100):
    try:
        new=int(Path('.run/api.pid').read_text())
        if new!=old:
            after=get('/api/v1/health')
            assert all(after['platforms'][p]['total_scrapes']>=d['total_scrapes'] for p,d in before['platforms'].items())
            break
    except (OSError,ValueError):pass
    time.sleep(.25)
else:raise AssertionError('API did not recover within 25 seconds')
output={'old_api_pid':old,'new_api_pid':new,'recovery_seconds':round(time.monotonic()-started,2),'database_snapshots_preserved':True,'before':before,'after':after}
Path('verification/recovery.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
print(f'PASS: API pid {old} -> {new}; recovered in {output["recovery_seconds"]}s; stored snapshots preserved.')
