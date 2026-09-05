# STACK.md — Technology Stack & Reasoning

Do not substitute any of these without updating this file and confirming
the reasoning still holds.

| Layer | Choice | Why This, Not Alternatives |
|---|---|---|
| **LLM runtime** | `llama-cpp-python` | Runs on CPU only — no GPU dependency, critical for a portable hackathon laptop demo. Exposes a real OS process/PID that the attack tool needs. Ollama was considered but rejected: it abstracts away the process internals we need to expose for the memory-scraping demo. |
| **Model** | 3–4B parameter GGUF, Q4_K_M quantization (e.g. Phi-3-mini-4k-instruct or Llama-3.2-3B-Instruct) | Small enough to load in seconds and respond quickly on CPU during a live demo. Larger models (7B+) risk slow, awkward pauses on stage. Must be downloaded manually from Hugging Face ahead of time. |
| **Backend framework** | FastAPI + uvicorn | Minimal boilerplate, async-ready, easy to wrap encryption/decryption cleanly around a single endpoint. Flask was considered and rejected only because FastAPI's built-in request validation (Pydantic) reduces bugs under time pressure. |
| **Encryption** | Python `cryptography` library, Fernet scheme (AES-128-CBC + HMAC, authenticated) | Fastest way to get correct, authenticated symmetric encryption in a few lines. Rolling raw AES-GCM by hand was rejected — too easy to get wrong (e.g. nonce reuse) under hackathon time pressure. Document clearly: production should use AES-256-GCM with proper hardware-backed key management (e.g. keys released only after remote attestation succeeds), not a static shared key. |
| **Enclave boundary (simulated)** | Docker container | Gives a visible, demonstrable "boundary" (`docker ps`, `docker top`) to point to during a live pitch. Explicitly NOT a substitute for real hardware isolation — see RULES.md and LIMITATIONS.md. |
| **Attack tool** | Raw Python, `/proc/[pid]/mem` + `/proc/[pid]/maps` | Standard Linux introspection interface — not a novel exploit, not malware. Demonstrates the same *category* of vulnerability as CVE-2023-4969 (LeftoverLocals), just at CPU/RAM level instead of GPU/VRAM, since GPU-level memory extraction requires specialized research tooling out of scope for a weekend build. Linux/WSL2 only — `/proc` doesn't exist on native Windows/macOS. |
| **Frontend** | Streamlit, or plain CLI/curl clients | A polished chat UI adds no technical credibility here and consumes hours needed for the actual security demo. Explicitly reject React/Next.js/Electron for this project. |
| **Production path (documented only)** | Gramine (LibOS) on Intel TDX or AMD SEV-SNP | The real hardware equivalent of the Docker boundary used in this prototype. Not built this weekend — described in DESIGN.md as the swap-in production path. |

## Explicitly Rejected Options (and why)

- **Ollama** — too abstracted for the attack demo to target a specific process cleanly
- **vLLM** — requires GPU, breaks the "runs on any hackathon laptop" requirement
- **Raw AES-GCM (hand-rolled)** — higher risk of implementation mistakes under time pressure vs. Fernet
- **React/Next.js frontend** — time sink with no relevance to the security claim being demonstrated
- **Real hardware TEE (Gramine + SEV-SNP/TDX)** — requires specific cloud VM support and setup time not available in a 24–48 hour window; documented as the production path instead
