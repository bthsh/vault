"""Track 2 Server — Encrypted & Isolated Enclave (Simulated TEE)

Architecture:
  FastAPI server designed to run inside a containerized boundary (simulating an enclave).
  All incoming requests and outgoing responses are encrypted using authenticated
  symmetric encryption (Fernet / AES-128-CBC + HMAC-SHA256).

Security & Honesty Distinction (RULES.md & LIMITATIONS.md):
  - In this prototype, memory isolation is SIMULATED using a Docker container boundary.
  - This provides process/filesystem isolation, NOT hardware-level memory encryption.
  - Plaintext briefly exists in process RAM during the decrypt -> infer -> encrypt window.
  - While this design protects data in transit and reduces the memory window via explicit
    garbage collection (del + gc.collect()), a true hardware TEE (Intel TDX / AMD SEV-SNP
    running via Gramine LibOS) is required in production to achieve cryptographic silicon-level
    isolation during inference.
"""

import os
import sys
import gc
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from llama_cpp import Llama

# Add project root to sys.path to access shared/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shared import crypto_utils

# Model path resolution
DEFAULT_MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    str(Path(__file__).resolve().parent.parent / "models" / "model.gguf")
)

app = FastAPI(title="VaultLLM Track 2 — Enclave (Simulated TEE)")

# Enable CORS for browser-based demo dashboard (including Chrome Private Network Access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_private_network=True,
)

import threading

llm_instance = None
model_lock = threading.Lock()


class EncryptedChatRequest(BaseModel):
    prompt: str  # Base64-encoded Fernet ciphertext


class EncryptedChatResponse(BaseModel):
    response: str  # Base64-encoded Fernet ciphertext


class PlaintextRequest(BaseModel):
    text: str


@app.post("/encrypt")
def encrypt_endpoint(req: PlaintextRequest):
    """Lightweight local encrypt endpoint for client-side demo helper."""
    return {"ciphertext": crypto_utils.encrypt(req.text)}


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    pid: int


def get_llm():
    global llm_instance
    if llm_instance is None:
        model_path = os.environ.get("MODEL_PATH", DEFAULT_MODEL_PATH)
        if not os.path.exists(model_path):
            raise RuntimeError(f"Model file not found at: {model_path}")
        llm_instance = Llama(
            model_path=model_path,
            n_ctx=2048,
            verbose=False
        )
    return llm_instance


@app.on_event("startup")
def startup_event():
    try:
        get_llm()
        print(f"[Track 2] Model loaded successfully from {DEFAULT_MODEL_PATH}")
    except Exception as e:
        print(f"[Track 2] Warning: Failed to load model at startup: {e}", file=sys.stderr)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Returns service health, model loading state, and process PID."""
    return HealthResponse(
        status="ok",
        model_loaded=(llm_instance is not None),
        pid=os.getpid()
    )


@app.post("/chat", response_model=EncryptedChatResponse)
def chat(request: EncryptedChatRequest):
    """Encrypted chat endpoint.
    
    1. Receives authenticated Fernet ciphertext in request.prompt.
    2. Decrypts prompt into temporary memory.
    3. Runs model inference.
    4. Encrypts response before sending.
    5. Explicitly wipes plaintext variables and triggers garbage collection.
    """
    model = get_llm()
    plaintext_prompt = None
    plaintext_response = None

    # Step 1: Decrypt request
    try:
        plaintext_prompt = crypto_utils.decrypt(request.prompt)
    except crypto_utils.DecryptionError:
        # Per API_SPEC.md: Generic error without leaking key or format details
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "decryption failed"}
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "decryption failed"}
        )

    # Step 2: Inference & Response Encryption
    try:
        if not plaintext_prompt.strip():
            plaintext_response = ""
        else:
            with model_lock:
                output = model(plaintext_prompt, max_tokens=128, stop=["\nUser:", "<|eot_id|>"])
            plaintext_response = output["choices"][0]["text"].strip()

        # Step 3: Encrypt response
        encrypted_response = crypto_utils.encrypt(plaintext_response)
        return EncryptedChatResponse(response=encrypted_response)

    except Exception as e:
        print(f"[Track 2 Error] Inference failure: {e}", file=sys.stderr)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "inference failure"}
        )

    finally:
        # Step 4: Defense-in-depth memory cleanup
        # Explicitly delete references and invoke Python garbage collection
        # to minimize exposure window (see LIMITATIONS.md)
        del plaintext_prompt
        del plaintext_response
        gc.collect()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
