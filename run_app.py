#!/usr/bin/env python3
"""
Launcher for a one-click local experience:
- Starts FastAPI (if present) on 127.0.0.1:8000 via uvicorn.
- Starts Streamlit UI on 127.0.0.1:8501.
- Waits for Streamlit to become reachable, then opens the browser.
- Cleans up child processes on exit (best effort).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent
STREAMLIT_URL = "http://127.0.0.1:8501"


def _process_kwargs() -> dict:
    """Ensure children are in their own group so we can terminate them cleanly."""
    if os.name == "nt":
        # CREATE_NEW_PROCESS_GROUP
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"preexec_fn": os.setsid}


def start_backend() -> subprocess.Popen | None:
    main_path = BASE_DIR / "main.py"
    if not main_path.exists():
        print("No FastAPI backend detected (main.py missing); skipping backend start.")
        return None

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


def start_streamlit() -> subprocess.Popen:
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
    ]
    print("Starting Streamlit UI on http://127.0.0.1:8501 ...")
    return subprocess.Popen(cmd, cwd=BASE_DIR, **_process_kwargs())


def wait_for_streamlit(proc: subprocess.Popen, timeout: int = 60) -> bool:
    """Poll until Streamlit is reachable or times out."""
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
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


def main() -> None:
    backend_proc = None
    streamlit_proc = None
    try:
        backend_proc = start_backend()
        streamlit_proc = start_streamlit()

        if wait_for_streamlit(streamlit_proc):
            print("Streamlit is ready; opening browser ...")
            webbrowser.open(STREAMLIT_URL)
        else:
            print("Streamlit not reachable; browser will not be opened.")

        # Keep script alive while Streamlit runs.
        while True:
            if streamlit_proc.poll() is not None:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupted; shutting down ...")
    finally:
        terminate_process(streamlit_proc, "Streamlit")
        terminate_process(backend_proc, "FastAPI backend")


if __name__ == "__main__":
    main()
