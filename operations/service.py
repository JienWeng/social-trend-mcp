#!/usr/bin/env python3
"""Single-instance local supervisor for the Social Trends API."""
import fcntl,json,os,signal,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
RUN=ROOT/'.run'
PID=RUN/'supervisor.pid'
CHILD=RUN/'api.pid'


def read_pid(path):
    try:
        pid=int(path.read_text().strip())
        if pid<=1:return None
        os.kill(pid,0)
        return pid
    except (OSError,ValueError):return None


def supervisor_pid():
    pid=read_pid(PID)
    if pid is None:return None
    try:
        args=Path(f'/proc/{pid}/cmdline').read_bytes()
        return pid if str(Path(__file__).resolve()).encode() in args and b'run' in args else None
    except OSError:return None


def verified_api_pid():
    pid=read_pid(CHILD)
    if pid is None:return None
    try:
        command=Path(f'/proc/{pid}/cmdline').read_bytes()
        cwd=Path(f'/proc/{pid}/cwd').resolve()
        if b'uvicorn' in command and b'app.main:app' in command and cwd==ROOT and os.getpgid(pid)==pid:
            return pid
    except OSError:pass
    return None


def reconcile_orphan():
    pid=verified_api_pid()
    if pid:
        print(f'Stopping recorded orphan API pid={pid}',flush=True)
        try:os.killpg(pid,signal.SIGTERM)
        except ProcessLookupError:pass
        for _ in range(80):
            if verified_api_pid() is None:break
            time.sleep(.1)
        else:
            try:os.killpg(pid,signal.SIGKILL)
            except ProcessLookupError:pass
    CHILD.unlink(missing_ok=True)


def stop_child(process):
    if process.poll() is not None:return
    os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL)
        process.wait(timeout=5)


def run():
    RUN.mkdir(exist_ok=True)
    with (RUN/'service.lock').open('w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        reconcile_orphan()
        PID.write_text(str(os.getpid()))
        stopping=False
        def terminate(*_):
            nonlocal stopping
            stopping=True
        signal.signal(signal.SIGTERM,terminate)
        signal.signal(signal.SIGINT,terminate)
        process=None
        try:
            with (RUN/'api.log').open('ab',buffering=0) as log:
                while not stopping:
                    process=subprocess.Popen([str(ROOT/'start-api.sh')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                    CHILD.write_text(str(process.pid))
                    print(f'API started pid={process.pid}',flush=True)
                    while not stopping and process.poll() is None:time.sleep(.25)
                    if stopping:break
                    print(f'API exited code={process.returncode}; restarting in 2 seconds',flush=True)
                    time.sleep(2)
        finally:
            if process is not None:stop_child(process)
            PID.unlink(missing_ok=True);CHILD.unlink(missing_ok=True)


def start():
    pid=supervisor_pid()
    if pid:print(f'Already running, supervisor pid={pid}');return
    RUN.mkdir(exist_ok=True)
    with (RUN/'supervisor.log').open('ab',buffering=0) as log:
        subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'run'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    for _ in range(120):
        pid=supervisor_pid()
        if pid:print(f'Started supervisor pid={pid}; logs: {RUN / "api.log"}');return
        time.sleep(.1)
    raise SystemExit('Supervisor did not start; inspect .run/supervisor.log')


def stop():
    pid=supervisor_pid()
    if not pid:
        reconcile_orphan()
        print('Already stopped');return
    os.kill(pid,signal.SIGTERM)
    for _ in range(120):
        if supervisor_pid() is None:print('Stopped');return
        time.sleep(.25)
    raise SystemExit('Shutdown did not complete; inspect .run/supervisor.log')


if __name__=='__main__':
    command=sys.argv[1] if len(sys.argv)>1 else 'status'
    if command=='run':run()
    elif command=='start':start()
    elif command=='stop':stop()
    elif command=='restart':stop();start()
    elif command=='status':print(json.dumps({'running':bool(supervisor_pid()),'supervisor_pid':supervisor_pid(),'api_pid':verified_api_pid(),'log':str(RUN/'api.log')}))
    else:raise SystemExit('Usage: manage-service.sh start|stop|restart|status')
