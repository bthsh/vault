#!/usr/bin/env bash
# ==============================================================================
# VaultLLM — Live Hackathon Security Demo Runner
# Follows DEMO_SCRIPT.md sequence and talking points exactly.
# ==============================================================================

set -e

# Terminal formatting
BOLD="\033[1m"
GREEN="\033[32m"
RED="\033[31m"
YELLOW="\033[33m"
CYAN="\033[36m"
MAGENTA="\033[35m"
RESET="\033[0m"

# Project root resolution
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

# Activate Python virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
fi

SECRET_TOKEN="Project-Titan-Alpha"
AUTO_MODE=false
if [ "$1" == "--auto" ]; then
    AUTO_MODE=true
fi

pause_step() {
    if [ "$AUTO_MODE" = false ]; then
        echo -e "\n${YELLOW}[Press Enter to continue to next step...]${RESET}"
        read -r
    else
        sleep 2
    fi
}

echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "${BOLD}${CYAN}      VaultLLM — Live Security Demonstration (CPU/RAM Data-in-Use)     ${RESET}"
echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "Core Thesis: \"Local AI\" is not automatically \"Secure AI\"."
echo -e "Demonstrating data-in-use memory exposure and confidential enclave architecture.\n"

# ------------------------------------------------------------------------------
# STEP 1: Verify Track 1 Server (Unprotected Baseline)
# ------------------------------------------------------------------------------
echo -e "${BOLD}${CYAN}[STEP 1] Inspecting Track 1 Server (No TEE - Port 8000)...${RESET}"

TRACK1_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || true)
if [ -z "$TRACK1_HEALTH" ]; then
    echo -e "${YELLOW}[*] Track 1 server not running. Starting track1_no_tee/server.py in background...${RESET}"
    python3 -m uvicorn track1_no_tee.server:app --host 0.0.0.0 --port 8000 &
    TRACK1_BG_PID=$!
    echo -e "[*] Waiting for model to load into RAM..."
    for i in {1..30}; do
        sleep 1
        TRACK1_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || true)
        if [ -n "$TRACK1_HEALTH" ]; then break; fi
    done
fi

TRACK1_PID=$(echo "$TRACK1_HEALTH" | grep -o '"pid":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}[+] Track 1 is ONLINE.${RESET} Host Process PID: ${BOLD}${TRACK1_PID}${RESET}"
echo -e "    Health Response: $TRACK1_HEALTH"
pause_step

# ------------------------------------------------------------------------------
# STEP 2: Send Confidential Prompt to Track 1
# ------------------------------------------------------------------------------
echo -e "${BOLD}${CYAN}[STEP 2] Sending Confidential Acquisition Prompt to Track 1 (Plaintext)...${RESET}"
echo -e "Executing: ${BOLD}python3 track1_no_tee/client.py${RESET}"
python3 track1_no_tee/client.py
pause_step

# ------------------------------------------------------------------------------
# STEP 3: Execute Attack against Track 1
# ------------------------------------------------------------------------------
echo -e "${BOLD}${RED}======================================================================${RESET}"
echo -e "${BOLD}${RED}[STEP 3] Running Memory-Scraping Attack against Track 1 PID ${TRACK1_PID}${RESET}"
echo -e "${BOLD}${RED}======================================================================${RESET}"
echo -e "${MAGENTA}${BOLD}Presenter Talking Point:${RESET}"
echo -e "${BOLD}\"This is what a rogue admin, or malware with root access, can do to any"
echo -e "standard local AI setup right now — no exploit, no hacking tool, just"
echo -e "standard OS-level memory access that any admin already has.\"${RESET}\n"

echo -e "Executing: ${BOLD}sudo python3 attack_tool/mem_scraper.py ${TRACK1_PID} \"${SECRET_TOKEN}\" 3${RESET}"
if sudo -n true 2>/dev/null; then
    sudo python3 attack_tool/mem_scraper.py "${TRACK1_PID}" "${SECRET_TOKEN}" 3 || true
else
    # Run with interactive sudo
    sudo python3 attack_tool/mem_scraper.py "${TRACK1_PID}" "${SECRET_TOKEN}" 3 || true
fi

echo -e "\n${YELLOW}[*] Primary Evidence Logged at: demo/evidence_track1_leak.txt${RESET}"
pause_step

# ------------------------------------------------------------------------------
# STEP 4: Verify Track 2 Container (Simulated Enclave)
# ------------------------------------------------------------------------------
echo -e "${BOLD}${CYAN}[STEP 4] Inspecting Track 2 Container (Dockerized Simulated TEE - Port 8001)...${RESET}"

TRACK2_HEALTH=$(curl -s http://localhost:8001/health 2>/dev/null || true)
if [ -z "$TRACK2_HEALTH" ]; then
    echo -e "${YELLOW}[*] Track 2 container not running. Starting vaultllm-track2...${RESET}"
    docker run -d --name vaultllm-track2 -p 8001:8001 \
        -v "$(pwd)/models:/app/models:ro" \
        --env-file .env \
        vaultllm-track2 2>/dev/null || docker start vaultllm-track2
    sleep 3
fi

CONTAINER_PID=$(docker top vaultllm-track2 2>/dev/null | awk 'NR>1 {print $2}' | head -n1)
echo -e "${GREEN}[+] Track 2 Container is ONLINE.${RESET}"
echo -e "    Container ID: $(docker inspect --format '{{.Id}}' vaultllm-track2 2>/dev/null | cut -c1-12 || echo 'vaultllm-track2')"
echo -e "    Host Process PID: ${BOLD}${CONTAINER_PID}${RESET}"
pause_step

# ------------------------------------------------------------------------------
# STEP 5: Send Encrypted Prompt to Track 2
# ------------------------------------------------------------------------------
echo -e "${BOLD}${CYAN}[STEP 5] Sending Same Secret Prompt via Authenticated Client (Ciphertext)...${RESET}"
echo -e "Executing: ${BOLD}python3 track2_with_tee/client.py${RESET}"
python3 track2_with_tee/client.py
pause_step

# ------------------------------------------------------------------------------
# STEP 6: Execute Attack against Track 2 Container Process
# ------------------------------------------------------------------------------
echo -e "${BOLD}${RED}======================================================================${RESET}"
echo -e "${BOLD}${RED}[STEP 6] Running Same Attack against Track 2 Host PID ${CONTAINER_PID}${RESET}"
echo -e "${BOLD}${RED}======================================================================${RESET}"
echo -e "Executing: ${BOLD}sudo python3 attack_tool/mem_scraper.py ${CONTAINER_PID} \"${SECRET_TOKEN}\" 3${RESET}"

if [ -n "$CONTAINER_PID" ]; then
    sudo python3 attack_tool/mem_scraper.py "${CONTAINER_PID}" "${SECRET_TOKEN}" 3 || true
else
    echo -e "${RED}[!] Could not resolve container host PID.${RESET}"
fi
pause_step

# ------------------------------------------------------------------------------
# STEP 7: The Honest Explanation & Closing Pitch
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${GREEN}======================================================================${RESET}"
echo -e "${BOLD}${GREEN}[STEP 7] Honest Analysis & Architectural Takeaway${RESET}"
echo -e "${BOLD}${GREEN}======================================================================${RESET}"
echo -e "${BOLD}\"Our encryption stops anyone from reading this over the network or in"
echo -e "the request buffer — but during actual inference, the same category of"
echo -e "RAM exposure remains, because Docker isn't a real hardware TEE. That's"
echo -e "exactly the gap real hardware enclaves like Gramine on Intel TDX or AMD"
echo -e "SEV-SNP are built to close, and that's our documented production path."
echo -e "We're not claiming to have solved this fully in a weekend — we're"
echo -e "proving the architecture a real deployment needs, so the hardware"
echo -e "swap-in is straightforward later.\"${RESET}\n"

echo -e "${BOLD}${CYAN}Closing Pitch Line:${RESET}"
echo -e "${BOLD}\"VaultLLM — because 'local' was never actually the same as 'safe.' We've"
echo -e "shown you exactly where that gap is, proven it live, and built the"
echo -e "encryption and isolation architecture needed to close it with real"
echo -e "hardware.\"${RESET}\n"
echo -e "${CYAN}======================================================================${RESET}"
