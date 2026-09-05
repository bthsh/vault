# BUILD_PLAN.md — Phased Build Order

Follow this sequence. Do not start a later phase before the current one's
checklist is fully working — each phase depends on the previous one being
proven functional.

## Phase 1 — Model Sanity Check
- [ ] Download a small GGUF model (see STACK.md) onto the build machine
- [ ] Load it directly with `llama-cpp-python` in a plain Python shell
- [ ] Confirm it returns a coherent response to a simple test prompt
- [ ] No server code yet — this only proves the model + runtime work

## Phase 2 — Track 1 Server (No TEE)
- [ ] Build `track1_no_tee/server.py`: FastAPI app, one `/chat` endpoint
      taking `{"prompt": str}`, returning `{"response": str}`
- [ ] Add `/health` endpoint returning the process's own PID
- [ ] Confirm it runs via `uvicorn server:app --port 8000`
- [ ] Confirm a `curl` request or `client.py` gets a real model response

## Phase 3 — Attack Tool, Proven Against Track 1
- [ ] Build `attack_tool/mem_scraper.py` using `/proc/[pid]/mem`
- [ ] Start Track 1, send a prompt containing a unique fake secret
      (e.g. `"Project-Titan-Alpha"`)
- [ ] Run `sudo python3 mem_scraper.py <PID> "Project-Titan-Alpha"`
- [ ] Confirm the secret is found and printed — this is the "before" proof
      and must work reliably before moving on

## Phase 4 — Crypto Utilities
- [ ] Build `shared/crypto_utils.py`: Fernet key generation,
      `encrypt(plaintext: str) -> bytes`, `decrypt(ciphertext: bytes) -> str`
- [ ] Write a quick standalone round-trip test (encrypt then decrypt
      returns the original string exactly)

## Phase 5 — Track 2 Server (With TEE, simulated)
- [ ] Copy Track 1's server as a starting point
- [ ] Add decryption on request receipt, encryption on response send
- [ ] After handling each request: `del prompt_var; gc.collect()`
- [ ] Confirm `client.py` (sending an encrypted payload with the shared
      key) gets a correctly encrypted-then-decrypted round trip

## Phase 6 — Dockerize Track 2
- [ ] Write `track2_with_tee/Dockerfile`
- [ ] Build the image, run the container on a different port (e.g. 8001)
      so Track 1 and Track 2 can run simultaneously
- [ ] Confirm the encrypted client still works against the containerized
      version

## Phase 7 — Attack Track 2, Document Honestly
- [ ] Get the container's process PID (`docker top <container_id>`)
- [ ] Run `mem_scraper.py` against it
- [ ] Record what actually happens — whether plaintext is found during
      the decrypt/inference window (expected per LIMITATIONS.md) — do not
      alter the result to look better than it is

## Phase 8 — Demo Script
- [ ] Write `demo/run_demo.sh` sequencing: start Track 1 → send secret →
      attack it → show leak → start Track 2 (Docker) → send secret →
      attack it → print the honest explanation text (see DEMO_SCRIPT.md)

## Phase 9 — Documentation Pass
- [ ] Confirm `DESIGN.md`, `LIMITATIONS.md`, and code comments all agree
      with each other and with the submitted pitch deck (Slide 6 diagram,
      Slide 8 honesty table)
- [ ] Write `README.md` so a teammate who didn't build any of this can set
      up and run the full demo in under 10 minutes

## Definition of Done
- [ ] Track 1 runs and responds to prompts
- [ ] Track 2 runs, encrypts/decrypts correctly, inside Docker
- [ ] Attack tool demonstrates the leak against Track 1 reliably
- [ ] Attack tool run against Track 2 is documented honestly either way
- [ ] All docs are internally consistent and match the pitch deck
- [ ] `run_demo.sh` works end-to-end without missing manual steps
