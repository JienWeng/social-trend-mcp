import json,os,signal,subprocess,time,urllib.request
from pathlib import Path

def get():
    with urllib.request.urlopen('http://127.0.0.1:8000/',timeout=3) as response:return json.load(response)
old_supervisor=int(Path('.run/supervisor.pid').read_text());old_api=int(Path('.run/api.pid').read_text())
assert b'operations/service.py' in Path(f'/proc/{old_supervisor}/cmdline').read_bytes()
os.kill(old_supervisor,signal.SIGKILL)
assert get()['service']=='Social Trends Service'
started=time.monotonic()
subprocess.run(['./manage-service.sh','start'],check=True,timeout=15)
for _ in range(100):
    try:
        new_api=int(Path('.run/api.pid').read_text())
        if new_api!=old_api and get()['service']=='Social Trends Service':break
    except (OSError,ValueError):pass
    time.sleep(.25)
else:raise AssertionError('Orphan recovery failed')
try:assert b'uvicorn' not in Path(f'/proc/{old_api}/cmdline').read_bytes()
except FileNotFoundError:pass
result={'old_supervisor':old_supervisor,'old_api':old_api,'new_supervisor':int(Path('.run/supervisor.pid').read_text()),'new_api':new_api,'seconds':round(time.monotonic()-started,2),'old_orphan_reconciled':True}
Path('verification/orphan-recovery.json').write_text(json.dumps(result,indent=2))
print('PASS:',result)
