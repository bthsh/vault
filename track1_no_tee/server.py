"""Track 1 Server — Vulnerable Baseline (No TEE)

Architecture:
  Unprotected host FastAPI server running llama.cpp in plain process RAM.
  Both incoming prompts and outgoing responses are transmitted and processed
  in plaintext, exposing data-in-use to local memory inspection.

Honesty Note (RULES.md):
  This track represents standard local AI deployments where data is vulnerable
  to in-memory reading via standard OS interfaces such as /proc/[pid]/mem.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama

# Locate the quantized GGUF model
DEFAULT_MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    str(Path(__file__).resolve().parent.parent / "models" / "model.gguf")
)

app = FastAPI(title="VaultLLM Track 1 — No TEE")

# Enable CORS for browser-based demo dashboard (including Chrome Private Network Access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_private_network=True,
)

# Global LLM instance
llm_instance = None


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


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
        # Initialize llama.cpp model
        llm_instance = Llama(
            model_path=model_path,
            n_ctx=2048,
            verbose=False
        )
    return llm_instance


@app.on_event("startup")
def startup_event():
    # Pre-load model on startup so /health accurately reports status and latency is minimized
    try:
        get_llm()
        print(f"[Track 1] Model loaded successfully from {DEFAULT_MODEL_PATH}")
    except Exception as e:
        print(f"[Track 1] Warning: Failed to load model at startup: {e}", file=sys.stderr)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Returns service health, model loading state, and process PID.
    
    PID is required by the attack demonstration tool to target this process in /proc.
    """
    is_loaded = llm_instance is not None
    return HealthResponse(
        status="ok",
        model_loaded=is_loaded,
        pid=os.getpid()
    )


import threading

model_lock = threading.Lock()

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Plaintext chat endpoint.
    
    Accepts plaintext prompt and returns plaintext response.
    Both reside in plain process RAM with no isolation or encryption.
    """
    try:
        model = get_llm()
        # Handle empty prompt gracefully per TESTING.md
        prompt_text = request.prompt
        if not prompt_text.strip():
            return ChatResponse(response="")

        with model_lock:
            output = model(prompt_text, max_tokens=128, stop=["\nUser:", "<|eot_id|>"])
        text = output["choices"][0]["text"].strip()
        return ChatResponse(response=text)
    except Exception as e:
        print(f"[Track 1 Error] Inference error: {e}", file=sys.stderr)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model inference failure"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
