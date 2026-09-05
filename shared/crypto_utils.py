"""VaultLLM Shared Cryptographic Utilities

Implements authenticated symmetric encryption for Track 2 (client <-> server).
Scheme: Fernet (AES-128-CBC encryption + HMAC-SHA256 authentication).

Honesty Notes (RULES.md & LIMITATIONS.md):
  - In this prototype, client and server share a static Fernet key out-of-band
    (via .env or environment variable).
  - In a production implementation with real hardware TEEs (Intel TDX / AMD SEV-SNP),
    keys would be negotiated dynamically using ephemeral session keys (e.g. AES-256-GCM)
    released only after cryptographic remote attestation succeeds.
"""

import os
from typing import Union
from cryptography.fernet import Fernet, InvalidToken


class CryptoError(Exception):
    """Base exception for crypto utilities."""
    pass


class DecryptionError(CryptoError):
    """Raised when decryption fails due to invalid key, tampered data, or corruption."""
    pass


def generate_key() -> str:
    """Generate a fresh 32-byte URL-safe base64-encoded Fernet key."""
    return Fernet.generate_key().decode("utf-8")


def get_default_key() -> str:
    """Load the default key from environment variable FERNET_KEY."""
    key = os.environ.get("FERNET_KEY", "").strip()
    if not key:
        # Fall back to reading from local .env if present
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r") as f:
                    for line in f:
                        if line.startswith("FERNET_KEY="):
                            key = line.strip().split("=", 1)[1].strip()
                            break
            except Exception:
                pass
    if not key:
        raise CryptoError("FERNET_KEY not found in environment or .env file.")
    return key


def get_fernet(key: Union[str, bytes] = None) -> Fernet:
    """Create a Fernet cipher instance using the given key or default environment key."""
    if key is None:
        key = get_default_key()
    if isinstance(key, str):
        key = key.encode("utf-8")
    try:
        return Fernet(key)
    except Exception as e:
        raise CryptoError(f"Invalid Fernet key: {e}") from e


def encrypt(plaintext: str, key: Union[str, bytes] = None) -> str:
    """Encrypt a plaintext string.
    
    Returns:
        A base64-encoded URL-safe ciphertext string suitable for JSON payloads.
    """
    f = get_fernet(key)
    plaintext_bytes = plaintext.encode("utf-8")
    ciphertext_bytes = f.encrypt(plaintext_bytes)
    return ciphertext_bytes.decode("utf-8")


def decrypt(ciphertext: Union[str, bytes], key: Union[str, bytes] = None) -> str:
    """Decrypt an authenticated ciphertext string or bytes.
    
    Raises:
        DecryptionError if key is wrong or ciphertext has been tampered with.
    """
    f = get_fernet(key)
    if isinstance(ciphertext, str):
        ciphertext = ciphertext.encode("utf-8")

    try:
        decrypted_bytes = f.decrypt(ciphertext)
        return decrypted_bytes.decode("utf-8")
    except InvalidToken as e:
        raise DecryptionError("Decryption failed: invalid key, signature mismatch, or corrupted data.") from e
    except Exception as e:
        raise DecryptionError(f"Decryption failed: {e}") from e
