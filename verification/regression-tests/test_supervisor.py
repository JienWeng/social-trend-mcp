import importlib.util,subprocess,sys,time
from pathlib import Path


def module():
    path=Path(__file__).resolve().parents[2]/'operations'/'service.py'
    spec=importlib.util.spec_from_file_location('local_service',path)
    service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)
    return service


def test_reconcile_only_terminates_verified_recorded_orphan(tmp_path,monkeypatch):
    service=module();pidfile=tmp_path/'api.pid'
    monkeypatch.setattr(service,'CHILD',pidfile)
    process=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)','uvicorn','app.main:app'],cwd=service.ROOT,start_new_session=True)
    try:
        pidfile.write_text(str(process.pid))
        service.reconcile_orphan()
        assert process.wait(timeout=3) is not None
        assert not pidfile.exists()
    finally:
        if process.poll() is None:process.terminate();process.wait(timeout=3)


def test_reconcile_does_not_kill_unrelated_recorded_process(tmp_path,monkeypatch):
    service=module();pidfile=tmp_path/'api.pid'
    monkeypatch.setattr(service,'CHILD',pidfile)
    process=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],cwd=service.ROOT,start_new_session=True)
    try:
        pidfile.write_text(str(process.pid))
        service.reconcile_orphan()
        assert process.poll() is None
    finally:process.terminate();process.wait(timeout=3)
