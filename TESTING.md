# TESTING.md — Testing Strategy

## 1. Crypto Correctness Tests (`shared/crypto_utils.py`)

- [ ] **Round-trip test:** `decrypt(encrypt(plaintext)) == plaintext` for
      a range of inputs (empty string, short string, long string with
      special characters/unicode)
- [ ] **Wrong-key test:** decrypting with an incorrect key must raise a
      clear exception, never silently return garbage as if it succeeded
- [ ] **Tamper test:** flip a byte in a valid ciphertext, confirm
      decryption fails (proves Fernet's built-in authentication is
      working, not just encryption)

## 2. Track 1 Server Tests

- [ ] `/health` returns a valid PID that matches the actual running
      process (`ps aux | grep uvicorn` should show the same PID)
- [ ] `/chat` returns a non-empty response for a normal prompt
- [ ] `/chat` handles an empty-string prompt without crashing
- [ ] Server does not crash on a very long prompt (test with something
      near your model's context window limit)

## 3. Track 2 Server Tests

- [ ] `/chat` correctly decrypts a valid encrypted request and returns a
      correctly encrypted response (verify by decrypting the response
      client-side and confirming it's readable text)
- [ ] `/chat` returns a clean error (not a stack trace or plaintext leak)
      when given malformed ciphertext
- [ ] Confirm memory cleanup: after a request completes, the plaintext
      prompt variable should no longer be easily found via a quick manual
      `mem_scraper.py` check performed several seconds after the request
      finishes (some residual risk is expected and documented in
      LIMITATIONS.md — this test is about reducing the *window*, not
      claiming zero exposure)

## 4. Attack Tool Reliability Tests

- [ ] Run `mem_scraper.py` against Track 1 at least 5 times with the same
      secret string — it should find the secret consistently, not
      intermittently (intermittent results would undermine the demo's
      credibility)
- [ ] Confirm the tool correctly reports "permission denied" when run
      without `sudo`, rather than silently failing
- [ ] Confirm the tool correctly reports "no such process" for an invalid
      PID, rather than crashing with an unhandled exception

## 5. Integration / End-to-End Test

- [ ] Run the full `demo/run_demo.sh` sequence start to finish at least
      three times before the actual presentation, on the exact machine
      that will be used live — environment differences (missing sudo
      rights, Docker not installed, model path wrong) are the most common
      cause of live-demo failure

## 6. What We Are Deliberately NOT Testing (and why)

- **GPU memory extraction** — out of scope; this prototype is CPU-only
  (see STACK.md, LIMITATIONS.md)
- **Real hardware TEE attestation** — not built in this prototype; no
  test needed for functionality that doesn't exist yet
- **Multi-user concurrency / load testing** — this is a single-session
  demo tool, not a production service; load testing would be a false
  signal of readiness it doesn't need to send

## Pre-Demo Checklist (run this the morning of the presentation)

- [ ] Model file present at the expected path on the demo machine
- [ ] `pip install -r requirements.txt` completed with no errors
- [ ] Docker image builds successfully from a clean state (`docker build
      --no-cache`)
- [ ] Full demo sequence run once, live, on the actual presentation
      machine — not just a dev laptop
- [ ] Backup: a screen recording of a successful run, in case live
      execution fails during the actual presentation
