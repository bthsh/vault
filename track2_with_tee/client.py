"""Track 2 Client — Encrypted Enclave Client

Client for the protected Track 2 server (port 8001).
Encrypts prompts locally with the shared Fernet key before transmitting over HTTP,
and decrypts the server's ciphertext response locally.
"""

import sys
import requests
from pathlib import Path

# Add project root to sys.path to access shared/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared import crypto_utils

SERVER_URL = "http://localhost:8001"
DEFAULT_PROMPT = (
    "CONFIDENTIAL ACQUISITION BRIEF: Project-Titan-Alpha acquisition finalized at $14.25M. "
    "Target closure date: Q4 2026. Summarize key risks."
)


def send_encrypted_chat(prompt: str, url: str = SERVER_URL):
    print(f"\n[Client] Local Plaintext Prompt:")
    print(f"  \"{prompt}\"")

    # 1. Encrypt prompt locally
    ciphertext_prompt = crypto_utils.encrypt(prompt)
    print(f"\n[Client -> Server (Track 2 / Enclave)] Transmitting Ciphertext:")
    print(f"  Prompt Ciphertext (Base64): {ciphertext_prompt[:50]}... ({len(ciphertext_prompt)} chars)")

    try:
        # 2. Transmit ciphertext to server
        resp = requests.post(
            f"{url}/chat",
            json={"prompt": ciphertext_prompt},
            timeout=60
        )
        
        if resp.status_code != 200:
            print(f"[Client Error] Server returned HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
            return None

        data = resp.json()
        ciphertext_response = data.get("response", "")
        print(f"\n[Server -> Client (Track 2 / Enclave)] Received Ciphertext:")
        print(f"  Response Ciphertext (Base64): {ciphertext_response[:50]}... ({len(ciphertext_response)} chars)")

        # 3. Decrypt response locally
        decrypted_response = crypto_utils.decrypt(ciphertext_response)
        print(f"\n[Client] Decrypted Plaintext Response:")
        print(f"  \"{decrypted_response}\"\n")
        return decrypted_response

    except requests.exceptions.RequestException as e:
        print(f"[Client Error] Network communication error: {e}", file=sys.stderr)
        sys.exit(1)
    except crypto_utils.DecryptionError as e:
        print(f"[Client Error] Failed to decrypt server response: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    send_encrypted_chat(prompt)
