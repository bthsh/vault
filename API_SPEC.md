# API_SPEC.md — API Contract

## Track 1 — No TEE (port 8000)

### `POST /chat`

**Request body:**
```json
{
  "prompt": "string, plaintext, required"
}
```

**Response body:**
```json
{
  "response": "string, plaintext"
}
```

**Notes:** No authentication, no encryption. Prompt and response both
travel and process as plaintext. This is intentional — it's the
vulnerable baseline.

### `GET /health`

**Response body:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "pid": 12345
}
```

**Notes:** `pid` is required for the attack demo — the scraper tool needs
this to target the correct process.

---

## Track 2 — With TEE (simulated) (port 8001)

### `POST /chat`

**Request body:**
```json
{
  "prompt": "string, base64-encoded Fernet ciphertext, required"
}
```

**Response body:**
```json
{
  "response": "string, base64-encoded Fernet ciphertext"
}
```

**Notes:** Both request and response bodies are ciphertext, produced/
consumed using a shared Fernet key (see `shared/crypto_utils.py`). The
client is responsible for encrypting before sending and decrypting after
receiving. The server never logs or persists plaintext.

**Encryption details:**
- Scheme: Fernet (AES-128-CBC + HMAC-SHA256, authenticated)
- Key: generated once at setup, shared out-of-band between client and
  server for this prototype (production would use per-session keys
  released only after remote attestation succeeds)
- Key format: 32-byte URL-safe base64-encoded string

### `GET /health`

Same shape as Track 1 — used to retrieve the container's process ID for
the attack demo.

---

## Error Handling (both tracks)

| Status Code | Meaning |
|---|---|
| 200 | Success |
| 422 | Malformed request body (missing `prompt` field) |
| 500 | Model inference failure or (Track 2 only) decryption failure — e.g. wrong key, corrupted ciphertext |

Track 2 must NOT return decryption error details that leak information
about the key or plaintext structure — return a generic
`{"error": "decryption failed"}` message only.

## Versioning

This is a single-version hackathon prototype — no `/v1/` prefixing or
backward-compatibility guarantees are in scope.
