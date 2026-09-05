# DEMO_SCRIPT.md — Live Demo Sequence

Run this on Linux or WSL2 (the attack tool needs `/proc`, unavailable on
native Windows/macOS).

## Setup (before judges arrive)

- [ ] Model downloaded and path confirmed in both server configs
- [ ] Track 1 and Track 2 dependencies installed (`pip install -r
      requirements.txt`)
- [ ] Docker image for Track 2 built and tested at least once
- [ ] Two terminal windows arranged side by side, font size large enough
      to read from a distance
- [ ] `sudo` password ready to type quickly (or passwordless sudo
      configured for the demo machine only)

## Live Sequence

**1. Show Track 1 running (no protection)**
```
cd track1_no_tee
uvicorn server:app --port 8000
```
In a second terminal: `curl http://localhost:8000/health` — note the PID.

**2. Send the secret prompt**
```
python3 client.py
```
(Sends the built-in fake secret: "Project-Titan-Alpha", a $14.25M fake
acquisition detail.)

**3. Run the attack — live, in front of judges**
```
sudo python3 attack_tool/mem_scraper.py <PID> "Project-Titan-Alpha"
```
**Say:** *"This is what a rogue admin, or malware with root access, can
do to any standard local AI setup right now — no exploit, no hacking
tool, just standard OS-level memory access that any admin already has."*

The secret should appear in plaintext on screen. Pause here — let it land.

**4. Start Track 2 (Docker-wrapped, encrypted)**
```
docker build -t vaultllm-track2 ./track2_with_tee
docker run -p 8001:8001 vaultllm-track2
```
Get its PID: `docker top <container_id>`

**5. Send the same secret prompt, encrypted this time**
```
python3 track2_with_tee/client.py
```

**6. Run the same attack against Track 2**
```
sudo python3 attack_tool/mem_scraper.py <PID> "Project-Titan-Alpha"
```

**7. Deliver the honest explanation, regardless of the exact result:**
> "Our encryption stops anyone from reading this over the network or in
> the request buffer — but during actual inference, the same category of
> RAM exposure remains, because Docker isn't a real hardware TEE. That's
> exactly the gap real hardware enclaves like Gramine on Intel TDX or AMD
> SEV-SNP are built to close, and that's our documented production path.
> We're not claiming to have solved this fully in a weekend — we're
> proving the architecture a real deployment needs, so the hardware
> swap-in is straightforward later."

## Closing Line

> "VaultLLM — because 'local' was never actually the same as 'safe.' We've
> shown you exactly where that gap is, proven it live, and built the
> encryption and isolation architecture needed to close it with real
> hardware."

## If Something Breaks Mid-Demo

- If the model is slow to respond: have a pre-recorded terminal
  screen-capture as backup, and say so honestly ("here's a recording from
  our test run in case of live latency")
- If Docker fails to start: fall back to running Track 2 as a plain
  (non-Dockerized) Python process and explain verbally that the
  containerization step is what would normally represent the boundary
- Never fabricate a result live — if the attack against Track 2 doesn't
  behave as expected, describe what actually happened; this is more
  credible than a scripted "clean" outcome
