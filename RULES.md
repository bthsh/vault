# RULES.md — Non-Negotiable Constraints

These rules override convenience, speed, or "looking more impressive."
If a suggestion from the agent, a teammate, or a judge conflicts with
these, the rule wins.

## 1. Honesty Rules (most important — read first)

- **Never claim the Docker container is a real hardware TEE.** It is a
  process/filesystem isolation boundary only. It does not provide
  hardware-level memory encryption. Every README, comment, and slide must
  say so explicitly.
- **Never claim this prototype fully stops the RAM-scraping attack.** State
  plainly what it does stop (network-transit exposure, at-rest exposure)
  and what it doesn't yet stop (in-process plaintext during inference).
- **Never claim to be first, novel, or unprecedented.** Tinfoil and Prem AI
  already do real hardware-TEE-protected AI inference. This project's claim
  is *accessibility*, not *invention*.
- **Never fabricate a demo result.** If the attack against Track 2 still
  partially succeeds (expected, since Docker ≠ real TEE), show that
  honestly and explain why, rather than editing the result to look cleaner.
- **Never claim mathematical/cryptographic proof of security this project
  doesn't actually have.** Encryption correctness can be demonstrated;
  hardware-level isolation cannot, without real TEE hardware.

## 2. Safety / Scope Rules

- The memory-scraping tool (`mem_scraper.py`) may ONLY be run against
  processes started by this same project, on a machine the user owns or
  controls, for demonstration purposes. It must never be pointed at any
  third-party, production, or shared system.
- No real company names, real financial data, or real personal data in any
  demo prompt — use clearly fictional placeholders (e.g.
  "Project-Titan-Alpha," a made-up company).
- No hardcoded encryption keys or secrets committed to version control.
  Generate keys at setup time; keep them out of git via `.gitignore`.

## 3. Build Discipline Rules

- Follow the phase order in `BUILD_PLAN.md`. Do not start Track 2 or Docker
  before Track 1 and the attack tool are proven working against Track 1.
- Keep the model small (3-4B parameters, Q4 quantization). Do not upgrade
  to a larger model "for better answers" — live-demo responsiveness matters
  more than answer quality for this project's purpose.
- Do not build a React/Next.js frontend. Use Streamlit or plain CLI/curl
  clients only — UI polish is not what this project is graded on.
- The attack tool requires Linux (or WSL2). Do not attempt to port it to
  native Windows/macOS — document this limitation instead.

## 4. Documentation Consistency Rule

Any diagram, claim, or number written in code comments or docs must match
what's stated in the submitted pitch deck (specifically Slide 6's
architecture diagram and Slide 8's real-vs-simulated table). If the code
and the deck ever disagree, fix the code's documentation to match the
deck's honest framing — don't let the two drift apart.
