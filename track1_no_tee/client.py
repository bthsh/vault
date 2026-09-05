"""Track 1 Client — Plaintext Demo Client

Sends plaintext prompts to the unprotected Track 1 server (port 8000).
Default prompt contains the synthetic confidential token ("Project-Titan-Alpha")
per DEMO_SCRIPT.md for demonstrating the data-in-use memory exposure.
"""

import sys
import requests

SERVER_URL = "http://localhost:8000"
DEFAULT_PROMPT = (
    "CONFIDENTIAL ACQUISITION BRIEF: Project-Titan-Alpha acquisition finalized at $14.25M. "
    "Target closure date: Q4 2026. Summarize key risks."
)


def send_chat(prompt: str):
    print(f"\n[Client -> Server (Track 1)] Sending plaintext prompt:")
    print(f"  Prompt: {prompt}")

    try:
        resp = requests.post(
            f"{SERVER_URL}/chat",
            json={"prompt": prompt},
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        print(f"\n[Server -> Client (Track 1)] Received plaintext response:")
        print(f"  Response: {data.get('response')}\n")
        return data.get("response")
    except requests.exceptions.RequestException as e:
        print(f"[Client Error] Failed to communicate with server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    send_chat(prompt)
