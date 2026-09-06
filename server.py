"""VaultLLM Unified Server Launcher

Runs Track 1 (port 8000) and Track 2 (port 8001) servers for live demo & testing.
Uses separate subprocesses to ensure independent memory and GGML runtimes.
"""

import sys
import subprocess
import signal
from pathlib import Path

DIR = Path(__file__).resolve().parent


def main():
    print("[VaultLLM] Starting Track 1 (port 8000) and Track 2 (port 8001)...")
    python_bin = sys.executable

    p1 = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "track1_no_tee.server:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(DIR)
    )
    p2 = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "track2_with_tee.server:app", "--host", "0.0.0.0", "--port", "8001"],
        cwd=str(DIR)
    )

    def handle_shutdown(signum, frame):
        print("\n[VaultLLM] Stopping servers...")
        p1.terminate()
        p2.terminate()
        p1.wait()
        p2.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        p1.wait()
        p2.wait()
    except KeyboardInterrupt:
        handle_shutdown(None, None)


if __name__ == "__main__":
    main()
