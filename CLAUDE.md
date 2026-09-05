# CLAUDE.md — VaultLLM Project Index

Read this file first. It points to everything else — don't start coding
until you've at least skimmed `RULES.md` and `BUILD_PLAN.md`.

## What This Project Is

VaultLLM is a hackathon proof-of-concept proving that "local AI" is not
automatically "secure AI." It demonstrates a real, documented data-in-use
vulnerability (attacker reads a local LLM's live RAM) and shows an
encryption + isolation architecture that closes it — while being fully
honest about what's real hardware-grade security versus what's simulated
for the hackathon timeframe.

## Read These Files, In This Order

1. **`SETUP.md`** — run this FIRST, before any code is written. Exact
   installation commands: Python venv, dependencies, Docker, model
   download, encryption key generation, git setup. Do not proceed to
   BUILD_PLAN.md until every checkbox in SETUP.md's final verification
   list is confirmed working.
2. **`RULES.md`** — non-negotiable constraints. Read this before writing
   any code. Contains the critical honesty rule: never claim the Docker
   boundary is a real hardware TEE.
2. **`STACK.md`** — exact tech stack, and why each choice was made over
   alternatives. Don't substitute components without checking this first.
3. **`DESIGN.md`** — full architecture and data flow for both tracks
   (Track 1: no protection, Track 2: encrypted + containerized), plus the
   documented (not built) production path using real hardware TEEs.
4. **`BUILD_PLAN.md`** — the exact 9-phase build order with checkboxes.
   Follow this sequence; later phases depend on earlier ones working.
5. **`LIMITATIONS.md`** — the explicit real-vs-simulated table. Must stay
   consistent with the project's pitch deck (Slide 8) at all times.
6. **`DEMO_SCRIPT.md`** — the exact live demo sequence and talking points,
   including what to say when the attack against the protected version
   doesn't fully "win" (spoiler: that's expected and fine, see
   LIMITATIONS.md).
7. **`THREAT_MODEL.md`** — formal STRIDE-style threat model: who the
   attacker is, what's being protected, and which threat categories this
   project actually addresses vs. leaves out of scope.
8. **`API_SPEC.md`** — exact request/response contracts for both servers'
   `/chat` and `/health` endpoints, including error handling rules.
9. **`TESTING.md`** — specific test cases for the crypto layer, both
   servers, and the attack tool's reliability, plus a pre-demo checklist.
10. **`GLOSSARY.md`** — quick definitions of every technical term used
    across these docs (TEE, attestation, Fernet, quantization, etc.) —
    useful for teammates or judges unfamiliar with the space.

## One-Sentence Summary of the Core Claim

> Network encryption protects data in transit. Disk encryption protects
> data at rest. Nobody protects data while it's actually being processed —
> this project proves that gap is real (via a live memory-scraping attack)
> and builds the encryption/isolation architecture needed to close it,
> using Docker as a stand-in for a real hardware TEE that a production
> version would use.

## Real-World Evidence This Project Is Built On

Trail of Bits disclosed **CVE-2023-4969 ("LeftoverLocals")** in January
2024 — a real vulnerability letting attackers read live LLM session data
from leftover GPU memory across AMD, Apple, and Qualcomm hardware. This
project demonstrates the same *category* of vulnerability at the CPU/RAM
level (via `/proc/[pid]/mem`), since GPU-level extraction requires
specialized tooling outside hackathon scope. Say this distinction
explicitly whenever citing the CVE — see `RULES.md`.

## Folder Structure

```
vaultllm/
├── CLAUDE.md              — you are here
├── RULES.md               — non-negotiable constraints
├── STACK.md                — tech stack + reasoning
├── DESIGN.md               — architecture + data flow
├── BUILD_PLAN.md            — phased build checklist
├── LIMITATIONS.md           — real vs. simulated, honesty table
├── DEMO_SCRIPT.md           — live demo sequence + talking points
├── THREAT_MODEL.md          — formal STRIDE threat model
├── API_SPEC.md              — request/response contracts
├── TESTING.md               — test cases + pre-demo checklist
├── GLOSSARY.md              — key terms defined
├── requirements.txt
├── shared/
│   └── crypto_utils.py
├── track1_no_tee/
│   ├── server.py
│   └── client.py
├── track2_with_tee/
│   ├── server.py
│   ├── client.py
│   └── Dockerfile
├── attack_tool/
│   └── mem_scraper.py
└── demo/
    └── run_demo.sh
```

## If You're an AI Agent Reading This

Work through `BUILD_PLAN.md` phase by phase. Do not skip ahead. Do not
violate anything in `RULES.md`, especially the honesty constraints around
what Docker does and doesn't protect. When in doubt about a design
decision, check `STACK.md` for the reasoning before substituting a
different tool or library.
