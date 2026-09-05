# VaultLLM: Closing the "Data-in-Use" Gap in Local AI

> **"Local" was never the same as "Safe."**  
> Network encryption (TLS) protects data in transit. Disk encryption protects data at rest. But nobody protects data while it is actively being computed on. VaultLLM demonstrates that this gap is real via a live memory-scraping attack against an offline LLM, and proves the encryption + isolation architecture needed to close it.

---

## ⚠️ Non-Negotiable Honesty & Scope Framing (Read First)

> [!IMPORTANT]
> **What this prototype is and what it is NOT:**
> - **Never Claimed as a Hardware TEE:** The Docker container in Track 2 provides **process and filesystem isolation only**. It does **not** provide hardware-level memory encryption.
> - **Data-in-Transit & At-Rest:** Truly protected via authenticated symmetric encryption (Fernet / AES-128-CBC + HMAC-SHA256).
> - **In-Process Data-in-Use:** Plaintext briefly exists in RAM during the decrypt $\rightarrow$ infer $\rightarrow$ encrypt window, and residual tokens persist in `llama.cpp`'s KV cache and allocator memory. Software isolation cannot stop root memory scraping.
> - **Production Path:** Swapping the Docker container for a real hardware Trusted Execution Environment (**Intel TDX** or **AMD SEV-SNP** running via **Gramine LibOS**) with cryptographic remote attestation.

### What's Real vs. What's Simulated (Slide 8 Table)

| Component | In this hackathon build | In a real production version |
|---|---|---|
| **Encryption (client ↔ server)** | **Real** — Fernet (AES-128-CBC + HMAC) working end-to-end | Upgraded to AES-256-GCM with hardware-backed key release |
| **Memory isolation** | **Simulated** via Docker container boundary (process/namespace isolation) | **Real hardware TEE** (Intel TDX / AMD SEV-SNP) via Gramine LibOS |
| **Protection during inference (CVE-2023-4969 class)** | **Not yet enforced** — tokens persist in `llama.cpp` KV cache & allocator memory | **Enforced at silicon level** — CPU memory controller encrypts all physical RAM lines |
| **Remote attestation** | **Not implemented** (static shared key in prototype) | Hardware-signed attestation quote verified before keys are released |
| **GPU-level protection** | **Out of scope** — CPU-only quantized inference | NVIDIA Confidential Computing (H100/B200) |

---

## Architecture Overview

```
                     ┌─────────────────────────────┐
                     │        User / Client        │
                     └──────────────┬──────────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                     │
       [Track 1: No TEE]                    [Track 2: With TEE]
                 │                                     │
        plaintext prompt                      encrypted prompt
                 │                                     │
                 ▼                                     ▼
     ┌───────────────────────┐          ┌───────────────────────────┐
     │  Host OS (full access)│          │  Host OS (sees ciphertext)│
     │ ┌──────────────────┐  │          │ ┌────────────────────────┐│
     │ │  FastAPI server  │  │          │ │  Docker container      ││
     │ │ (plaintext RAM)  │  │          │ │ ┌──────────────────┐   ││
     │ └────────┬─────────┘  │          │ │ │ Decrypt prompt   │   ││
     │          │            │          │ │ ├──────────────────┤   ││
     │ ┌────────▼──────────┐ │          │ │ │ llama.cpp infer  │   ││
     │ │ llama.cpp infer   │ │          │ │ ├──────────────────┤   ││
     │ └────────┬──────────┘ │          │ │ │ Encrypt + wipe   │   ││
     │          │            │          │ │ └──────────────────┘   ││
     │ plaintext response    │          │ └───────────┬────────────┘│
     └──────────┬────────────┘          └─────────────┼─────────────┘
                │                                     │
                ▼                                     ▼
       Rogue admin or root                   Traffic is encrypted on
       malware reads prompt &                wire; RAM exposure during
       response via /proc/[pid]/mem          inference remains (proven
       (Proven live in Phase 3)              empirically in Phase 7)
```

---

## Quickstart: Run Full Demo in < 10 Minutes

### 1. Prerequisites
- Linux OS (Ubuntu 20.04+ or WSL2 with Linux kernel for `/proc/[pid]/mem`).
- Docker installed and running (`docker run hello-world`).
- Python 3.10+ (tested on Python 3.12).

### 2. Setup (One-Time)
```bash
git clone <repo-url> vaultllm
cd vaultllm

# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Download the recommended model (~2GB)
mkdir -p models
curl -L -o models/model.gguf https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf

# 3. Generate shared Fernet encryption key
python3 -c "from cryptography.fernet import Fernet; print(f'FERNET_KEY={Fernet.generate_key().decode()}')" > .env

# 4. Build Track 2 Docker image
docker build -t vaultllm-track2 -f track2_with_tee/Dockerfile .
```

### 3. Run the Complete Live Demo
```bash
./demo/run_demo.sh
```
*(Optionally run `./demo/run_demo.sh --auto` for non-interactive automated presentation mode)*.

---

## Step-by-Step Manual Demo Walkthrough

### Step 1: Start Track 1 (Unprotected Baseline)
```bash
python3 -m uvicorn track1_no_tee.server:app --host 0.0.0.0 --port 8000
```
In a second terminal:
```bash
curl http://localhost:8000/health
# Returns: {"status":"ok","model_loaded":true,"pid":<PID>}
```

### Step 2: Send Confidential Data
```bash
python3 track1_no_tee/client.py
# Sends: "CONFIDENTIAL ACQUISITION BRIEF: Project-Titan-Alpha acquisition finalized at $14.25M..."
```

### Step 3: Run the Attack against Track 1
```bash
sudo python3 attack_tool/mem_scraper.py <TRACK1_PID> "Project-Titan-Alpha"
```
**Result:** 10 occurrences discovered immediately across `[heap]` and anonymous memory mappings. Plaintext prompt and LLM response are completely exposed.

### Step 4: Start Track 2 (Containerized Enclave)
```bash
docker run -d --name vaultllm-track2 -p 8001:8001 \
  -v $(pwd)/models:/app/models:ro \
  --env-file .env \
  vaultllm-track2
```
Find the container's host PID:
```bash
docker top vaultllm-track2
```

### Step 5: Send Encrypted Data
```bash
python3 track2_with_tee/client.py
# Client encrypts prompt -> sends ciphertext -> server decrypts & infers -> returns ciphertext -> client decrypts
```

### Step 6: Attack Track 2 & Observe the Real Finding
```bash
sudo python3 attack_tool/mem_scraper.py <CONTAINER_HOST_PID> "Project-Titan-Alpha"
```
**Result:** The attack still recovers tokens from host memory mappings. 

---

## Empirical Findings: The Real Security Lesson

During testing with `mem_scraper.py` against Track 2 running inside Docker:
1. **The In-Transit Win:** Network eavesdroppers capturing packets see only authenticated Fernet ciphertext (`gAAAAAB...`).
2. **The In-Process Reality:** 10 occurrences of `"Project-Titan-Alpha"` were recovered from the container process's anonymous host memory pages (`[anon]`).
3. **Why Python Cleanup Failed:** Even though `server.py` explicitly executes `del plaintext_prompt; del plaintext_response; gc.collect()`, tokens remained in:
   - **`llama.cpp`'s native KV cache and context buffers** in C++ memory.
   - **`glibc` malloc arena chunks** that are cached for reuse rather than zeroed.

> **Key Presentation Takeaway:**  
> *"Our encryption stops anyone from reading this over the network or in the request buffer — but during actual inference, the same category of RAM exposure remains, because Docker isn't a real hardware TEE. That's exactly the gap real hardware enclaves like Gramine on Intel TDX or AMD SEV-SNP are built to close, and that's our documented production path."*

---

## Document Index

- [SETUP.md](file:///home/bathisha/Documents/vantage/vaultllm/SETUP.md): Initial environment setup and system dependency verification.
- [RULES.md](file:///home/bathisha/Documents/vantage/vaultllm/RULES.md): Non-negotiable constraints and strict honesty guidelines.
- [DESIGN.md](file:///home/bathisha/Documents/vantage/vaultllm/DESIGN.md): System architecture, data flow diagrams, and production Gramine path.
- [LIMITATIONS.md](file:///home/bathisha/Documents/vantage/vaultllm/LIMITATIONS.md): The explicit Real vs. Simulated comparison table.
- [DEMO_SCRIPT.md](file:///home/bathisha/Documents/vantage/vaultllm/DEMO_SCRIPT.md): Exact live presentation sequence, timing, and talking points.
- [THREAT_MODEL.md](file:///home/bathisha/Documents/vantage/vaultllm/THREAT_MODEL.md): STRIDE threat analysis and attacker capabilities.
- [API_SPEC.md](file:///home/bathisha/Documents/vantage/vaultllm/API_SPEC.md): Formal JSON request/response schema specifications.
- [TESTING.md](file:///home/bathisha/Documents/vantage/vaultllm/TESTING.md): Verification test cases and pre-demo reliability checklists.
- [GLOSSARY.md](file:///home/bathisha/Documents/vantage/vaultllm/GLOSSARY.md): Definitions of key terms (TEE, Attestation, Data-in-use, Fernet, etc.).
