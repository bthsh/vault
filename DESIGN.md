# DESIGN.md — Architecture & Data Flow

## System Overview

Two parallel systems, same underlying LLM, different security posture:

```
                     ┌─────────────────────────────┐
                     │        User / Client         │
                     └──────────────┬───────────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                      │
       [Track 1: No TEE]                    [Track 2: With TEE]
                 │                                      │
        plaintext prompt                      encrypted prompt
                 │                                      │
                 ▼                                      ▼
     ┌───────────────────────┐          ┌───────────────────────────┐
     │   Host OS (full access)│          │  Host OS (sees ciphertext) │
     │  ┌──────────────────┐ │          │ ┌────────────────────────┐│
     │  │   FastAPI server  │ │          │ │  Docker container       ││
     │  │  (plaintext RAM)  │ │          │ │ ┌──────────────────┐   ││
     │  └────────┬──────────┘ │          │ │ │ Decrypt prompt    │   ││
     │           │            │          │ │ ├──────────────────┤   ││
     │  ┌────────▼──────────┐ │          │ │ │ llama.cpp infer   │   ││
     │  │  llama.cpp inference│ │          │ │ ├──────────────────┤   ││
     │  └────────┬──────────┘ │          │ │ │ Encrypt + wipe    │   ││
     │           │            │          │ │ └──────────────────┘   ││
     │  plaintext response    │          │ └────────────────────────┘│
     └───────────┬─────────────┘          └────────────┬───────────┘
                 │                                      │
                 ▼                                      ▼
       Any admin/malware with              Host OS/admin sees only
       root can read RAM directly          ciphertext in transit;
       at every stage (proven by           plaintext still briefly
       our mem_scraper.py demo)            exists in-process during
                                            inference (Docker limit —
                                            see LIMITATIONS.md)
```

## Data Flow — Track 1 (No TEE)

1. Client sends `POST /chat` with `{"prompt": "<plaintext>"}`
2. FastAPI receives it — plaintext, in regular process RAM
3. `llama-cpp-python` runs inference — plaintext the entire time
4. Response returned as plaintext
5. **Vulnerability point:** at every step above, `/proc/[pid]/mem` can
   read the live value directly from RAM

## Data Flow — Track 2 (With TEE, simulated)

1. Client encrypts the prompt locally using a shared Fernet key
2. Client sends `POST /chat` with `{"prompt": "<ciphertext>"}`
3. FastAPI (running inside Docker) receives ciphertext
4. Server decrypts it — this is the moment plaintext exists in RAM
5. `llama-cpp-python` runs inference on the plaintext
6. Server encrypts the response before returning it
7. Server explicitly deletes plaintext variables and calls `gc.collect()`
8. **What this protects:** anything traveling over the network, and
   anything sitting in memory before decryption or after encryption
9. **What this does NOT yet protect (see LIMITATIONS.md):** the brief
   window during step 4-6 where plaintext exists in-process — because
   Docker provides process isolation, not hardware memory encryption

## Production Path (documented, not built this weekend)

Replace the Docker container with a real Trusted Execution Environment:
- **Gramine** (Library OS) running the same FastAPI + llama.cpp code
  unmodified inside the enclave
- **Intel TDX** or **AMD SEV-SNP** providing hardware-level memory
  encryption for the entire enclave, including the decrypt → infer →
  encrypt window that Docker currently cannot protect
- **Remote attestation** — the enclave proves its own integrity
  cryptographically to the client before any data is sent, replacing the
  mocked handshake in this prototype

This is a swap of the isolation layer, not a rewrite of the encryption
logic or the inference code — which is the core architectural claim of
this project.

## Interactive Dashboard Live Integration Note (2026-09-06)

`demo/dashboard.html` executes live HTTP requests against the real backend
(`POST /chat` on port 8000 for Track 1, `POST /chat` on port 8001 for Track 2)
for stages 1, 2, 3, and 5 in both panels. Real Fernet symmetric encryption and
decryption are executed matching `shared/crypto_utils.py`. Stage 4 in the
"With TEE" panel ("Decrypted in enclave") remains an explicitly labeled
simulation ("SIMULATED — ENCLAVE BOUNDARY") because hardware-enforced
memory encryption during inference requires a physical TEE (Intel TDX / AMD SEV-SNP)
rather than the simulated Docker boundary.
