# LIMITATIONS.md — What's Real vs. What's Simulated

This file must stay consistent with Slide 8 of the pitch deck at all
times. If you change one, change the other.

| Component | In this hackathon build | In a real production version |
|---|---|---|
| Encryption (client ↔ server) | **Real** — Fernet (AES-128) actually implemented and working | Same approach, upgraded to AES-256-GCM with hardware-backed key management |
| Memory isolation | **Simulated** via Docker container boundary — process/filesystem isolation only, no hardware memory encryption | Real hardware TEE (Intel TDX / AMD SEV-SNP) via a LibOS runtime like Gramine |
| Protection against RAM-scraping during inference (the class of attack in CVE-2023-4969) | **Not yet enforced** — plaintext exists in-process during decrypt → infer → encrypt, and residual tokens persist in llama.cpp's KV cache and unscrubbed memory allocator chunks even after Python `del` and `gc.collect()` | Enforced at the silicon level — hardware-encrypted RAM (Intel TDX / AMD SEV-SNP) blinds host memory inspection completely, stopping this exact attack |
| Remote attestation | **Not implemented** in this prototype (optional stretch goal: a mocked handshake) | Real cryptographic hardware attestation, verified by the client before any data is sent |
| GPU-level protection | **Out of scope** — this prototype runs CPU-only inference | Would require NVIDIA Confidential Computing (Hopper/Blackwell) for GPU-accelerated inference |

## Why This Is Stated Explicitly, Not Hidden

A judge or teammate testing this project should never be surprised by
what it does and doesn't protect. The core pitch is that this prototype
proves the **architecture and data flow** a real TEE deployment needs —
the encryption logic, the request/response boundary, the isolation
concept — so that swapping in real hardware later is a **swap, not a
rebuild**. Overstating what's protected right now undermines that claim
the moment anyone actually tests it.

## Empirical Findings from Phase 7 Testing

During testing with `mem_scraper.py` against Track 2 running inside Docker (host PID 30006):
- **10 occurrences** of the confidential string (`"Project-Titan-Alpha"`) were recovered from live anonymous memory mappings (`[anon]`).
- Even though the server explicitly ran `del plaintext_prompt; del plaintext_response; gc.collect()` immediately after generating the response, copies of the tokens persisted in:
  1. **llama.cpp's internal KV cache / context buffers** (managed in C++ native memory outside Python's garbage collector).
  2. **Unscrubbed glibc heap / arena allocator chunks** that are retained for reuse rather than returned to the kernel or zeroed.
- This proves empirically that **software-level memory clearing is insufficient** to prevent data-in-use exposure. Only silicon-level hardware memory encryption (Intel TDX / AMD SEV-SNP) where physical memory lines are hardware-encrypted by the CPU memory controller can seal this gap.

## The One Sentence to Say Out Loud During Any Demo

> "Our encryption stops anyone from reading this over the network or in
> the request buffer — but during actual inference, the same category of
> RAM exposure remains, because Docker isn't a real hardware TEE. That's
> exactly the gap real hardware enclaves like Gramine on Intel TDX or AMD
> SEV-SNP are built to close, and that's our documented production path."
