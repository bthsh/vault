# THREAT_MODEL.md — Formal Threat Model

## Assets Being Protected

1. **The prompt** — whatever the user sends (may contain financials, code,
   PII, trade secrets)
2. **The model's response** — may reconstruct or reveal the prompt's
   sensitive content
3. **The model weights themselves** — a secondary asset (IP theft concern,
   not the primary focus of this project, but worth naming)
4. **The Fernet symmetric key** — if this leaks, all encrypted traffic for
   that session is trivially readable

## Attacker Profile (who we're defending against)

| Attacker | Capability | In scope? |
|---|---|---|
| Network eavesdropper (no host access) | Can sniff traffic between client and server | Yes — solved by encryption in transit |
| Rogue administrator | Has root/sudo on the host machine, no physical access needed | Yes — this is the primary attacker this project targets |
| Malware / compromised process | Gained root or process-level access via an unrelated exploit | Yes — same capability as rogue admin, different route in |
| Physical attacker (cold-boot, bus probing) | Has physical access to the hardware | Named as a real threat (per Trail of Bits' broader TEE research) but NOT demonstrated in this prototype — out of scope for a software-only demo |
| Nation-state / supply-chain attacker | Can compromise the model weights or firmware before deployment | Out of scope entirely — not addressed by this project |

## STRIDE Analysis

| Threat category | Applies here? | Mitigation in this project |
|---|---|---|
| **S**poofing | Low relevance — single-user local demo, no multi-tenant auth in scope | Not addressed (would need proper auth for a real multi-user deployment) |
| **T**ampering | Yes — an attacker with RAM access could theoretically alter a prompt or response mid-processing | Not fully addressed by this prototype; a real TEE's attestation would detect tampering via measured boot |
| **R**epudiation | Low relevance for a demo; would matter in production for audit logging | Not addressed |
| **I**nformation Disclosure | **Yes — this is the primary threat this project addresses.** Plaintext prompts/responses in RAM are readable via `/proc/[pid]/mem` | Encryption in transit + at rest (Track 2); real hardware TEE would close the remaining in-process gap |
| **D**enial of Service | Not addressed — a single quantized model on CPU has no DoS protections built in | Out of scope |
| **E**levation of Privilege | The attack tool itself requires elevated (root) privileges to function — this is intentional, it represents "what a rogue admin can already do" | N/A — this is the threat model's premise, not a gap to fix |

## Primary Threat This Project Demonstrates

**Information Disclosure via data-in-use exposure.** Specifically: any
process with sufficient OS-level privilege (root/sudo) can read another
process's live memory directly, exposing plaintext prompts and responses
even when the AI is running fully offline with no network exposure at
all. This is proven live using `mem_scraper.py` against Track 1, and
partially mitigated (network + at-rest) in Track 2.

## What Remains Unmitigated Even in Track 2 (see LIMITATIONS.md)

The decrypt → infer → encrypt window still exposes plaintext in-process
RAM, because Docker provides process isolation, not hardware memory
encryption. This is the exact gap real hardware TEEs (Intel TDX, AMD
SEV-SNP) are designed to close, and is documented as the production path
rather than solved in this hackathon build.
