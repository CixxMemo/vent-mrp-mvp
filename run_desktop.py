import sys
import subprocess
import time
import requests
import multiprocessing
import fastapi
import uvicorn
import pandas
import openpyxl
import main

def launch_ui():
    from main import FactoryCutApp
    app = FactoryCutApp()
    app.mainloop()

def main():
    print("Starting FastAPI backend...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "api_app:app", "--port", "8000"]
    backend_process = subprocess.Popen(backend_cmd)

    try:
        # Wait for backend to be ready
        print("Waiting for backend to become ready...")
        start_time = time.time()
        backend_ready = False
        while time.time() - start_time < 15:
            if backend_process.poll() is not None:
                print("Backend process exited prematurely.")
                break
            try:
                response = requests.get("http://127.0.0.1:8000/health", timeout=1)
                if response.status_code == 200:
                    backend_ready = True
                    break
            except requests.RequestException:
                pass
            time.sleep(1)

        if not backend_ready:
            print("Warning: Failed to connect to the backend. Proceeding to launch UI anyway.")
        else:
            print("Backend is ready.")

        print("Launching Desktop UI...")
        launch_ui()

    finally:
        print("Desktop UI closed. Terminating backend...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
