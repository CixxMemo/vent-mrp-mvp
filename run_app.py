#!/usr/bin/env python3
"""
Launcher for a one-click local experience:
- Starts FastAPI (if present) on 127.0.0.1:8000 via uvicorn.
- Starts Streamlit UI on 127.0.0.1:8501.
- Waits for Streamlit to become reachable, then opens the browser.
- Cleans up child processes on exit (best effort).
"""

from __future__ import annotations

import atexit
import os
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

import requests

IS_FROZEN = bool(getattr(sys, "frozen", False))
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
STREAMLIT_URL = "http://127.0.0.1:8501"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True

    try:
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        exit_code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return exit_code.value == 259  # STILL_ACTIVE
    except Exception:
        return False


def _lock_path() -> Path:
    if os.name == "nt":
        base = Path(
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or (Path.home() / "AppData" / "Local")
        )
        lock_dir = base / "VentMRP"
    else:
        base = Path(os.environ.get("XDG_RUNTIME_DIR") or os.environ.get("TMPDIR") or "/tmp")
        lock_dir = base / "ventmrp"
    lock_dir.mkdir(parents=True, exist_ok=True)
    return lock_dir / "launcher.lock"


def acquire_lock() -> Path | None:
    path = _lock_path()
    if path.exists():
        try:
            pid = int(path.read_text().strip() or "0")
        except Exception:
            pid = 0
        if _pid_alive(pid):
            print(f"Another instance is already running (PID {pid}); exiting.")
            return None
        try:
            path.unlink()
        except Exception:
            pass

    try:
        path.write_text(str(os.getpid()))
    except Exception as exc:
        print(f"Unable to create lock file: {exc}")
        return None
    atexit.register(release_lock, path)
    return path


def release_lock(path: Path) -> None:
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass


def _process_kwargs() -> dict:
    """Ensure children are in their own group so we can terminate them cleanly."""
    if os.name == "nt":
        # CREATE_NEW_PROCESS_GROUP
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"preexec_fn": os.setsid}


def start_backend() -> subprocess.Popen | dict | None:
    main_path = BASE_DIR / "main.py"
    if not main_path.exists():
        print("No FastAPI backend detected (main.py missing); skipping backend start.")
        return None

    if IS_FROZEN:
        return start_backend_in_process()

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    print("Starting FastAPI backend on http://127.0.0.1:8000 ...")
    try:
        return subprocess.Popen(cmd, cwd=BASE_DIR, **_process_kwargs())
    except FileNotFoundError:
        print("uvicorn is not available; skipping backend start.")
    except Exception as exc:  # pragma: no cover - best-effort logging
        print(f"Failed to start backend: {exc}")
    return None


def start_backend_in_process() -> dict | None:
    try:
        import uvicorn

        import main
    except Exception as exc:
        print(f"uvicorn backend not available; skipping backend start ({exc}).")
        return None

    config = uvicorn.Config(main.app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    print("Starting FastAPI backend (in-process) on http://127.0.0.1:8000 ...")
    thread.start()
    return {"server": server, "thread": thread}


def start_streamlit() -> subprocess.Popen:
    streamlit_env = os.environ.copy()
    streamlit_env.update(
        {
            "STREAMLIT_SERVER_HEADLESS": "true",
            "STREAMLIT_SERVER_RUN_ON_SAVE": "false",
            "STREAMLIT_SERVER_FILE_WATCHER_TYPE": "none",
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
        }
    )
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(BASE_DIR / "streamlit_app.py"),
        "--server.port",
        "8501",
        "--server.address",
        "127.0.0.1",
        "--server.headless",
        "true",
        "--server.runOnSave",
        "false",
        "--server.fileWatcherType",
        "none",
        "--browser.gatherUsageStats",
        "false",
    ]
    print("Starting Streamlit UI on http://127.0.0.1:8501 ...")
    return subprocess.Popen(cmd, cwd=BASE_DIR, env=streamlit_env, **_process_kwargs())


def run_streamlit_in_process() -> None:
    os.environ.update(
        {
            "STREAMLIT_SERVER_HEADLESS": "true",
            "STREAMLIT_SERVER_RUN_ON_SAVE": "false",
            "STREAMLIT_SERVER_FILE_WATCHER_TYPE": "none",
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
        }
    )
    argv = [
        "streamlit",
        "run",
        str(BASE_DIR / "streamlit_app.py"),
        "--server.headless=true",
        "--server.port=8501",
        "--server.address=127.0.0.1",
        "--server.fileWatcherType=none",
        "--server.runOnSave=false",
        "--browser.gatherUsageStats=false",
    ]
    original_argv = sys.argv[:]
    sys.argv = argv
    print("Starting Streamlit UI (in-process) on http://127.0.0.1:8501 ...")
    try:
        from streamlit.web import cli as stcli

        stcli.main()
    except SystemExit:
        pass
    finally:
        sys.argv = original_argv


def wait_for_streamlit(proc: subprocess.Popen | None = None, timeout: int = 60) -> bool:
    """Poll until Streamlit is reachable or times out."""
    start = time.time()
    while time.time() - start < timeout:
        if proc is not None and proc.poll() is not None:
            print("Streamlit process exited before becoming ready.")
            return False
        try:
            resp = requests.get(STREAMLIT_URL, timeout=1)
            if resp.status_code < 500:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    print("Timed out waiting for Streamlit to be ready.")
    return False


def terminate_process(proc: subprocess.Popen | None, name: str) -> None:
    if proc is None or proc.poll() is not None:
        return

    print(f"Stopping {name} ...")
    try:
        if os.name != "nt":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            if os.name != "nt":
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
        except Exception:
            pass


def terminate_backend(backend: subprocess.Popen | dict | None) -> None:
    if backend is None:
        return
    if isinstance(backend, subprocess.Popen):
        terminate_process(backend, "FastAPI backend")
        return
    server = backend.get("server")
    thread = backend.get("thread")
    if server is None or thread is None:
        return
    print("Stopping FastAPI backend ...")
    try:
        server.should_exit = True
        thread.join(timeout=5)
    except Exception:
        pass


def main() -> None:
    lock_path = acquire_lock()
    if lock_path is None:
        return

    backend_proc = None
    streamlit_proc = None
    try:
        backend_proc = start_backend()
        if IS_FROZEN:
            opened = False

            def open_browser_once() -> None:
                nonlocal opened
                if opened:
                    return
                if wait_for_streamlit():
                    print("Streamlit is ready; opening browser ...")
                    webbrowser.open_new_tab(STREAMLIT_URL)
                    opened = True
                else:
                    print("Streamlit not reachable; browser will not be opened.")

            threading.Thread(target=open_browser_once, daemon=True).start()
            run_streamlit_in_process()
        else:
            streamlit_proc = start_streamlit()

            opened = False

            def open_browser_once() -> None:
                nonlocal opened
                if opened:
                    return
                if wait_for_streamlit(streamlit_proc):
                    print("Streamlit is ready; opening browser ...")
                    webbrowser.open_new_tab(STREAMLIT_URL)
                    opened = True
                else:
                    print("Streamlit not reachable; browser will not be opened.")

            threading.Thread(target=open_browser_once, daemon=True).start()
            # Keep script alive while Streamlit runs.
            while True:
                if streamlit_proc.poll() is not None:
                    break
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupted; shutting down ...")
    finally:
        terminate_process(streamlit_proc, "Streamlit")
        terminate_backend(backend_proc)
        release_lock(lock_path)


if __name__ == "__main__":
    main()
