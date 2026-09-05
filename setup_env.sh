#!/usr/bin/env bash
set -e

echo "===================================================="
echo "  VaultLLM - Environment Setup (from SETUP.md)"
echo "===================================================="

# 1. Update system packages
echo "[+] Updating apt repositories..."
sudo apt update

echo "[+] Installing system dependencies (Python venv, build tools, cmake, docker)..."
sudo apt install -y python3 python3-pip python3-venv build-essential cmake docker.io

# 2. Enable Docker and set user permissions
echo "[+] Enabling and starting Docker..."
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"

# 3. Optional: enable passwordless sudo for local agent automation (needed for mem_scraper.py and automated testing)
echo "[+] Configuring sudoers for seamless local automation..."
echo "$USER ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/vaultllm_automation > /dev/null
sudo chmod 0440 /etc/sudoers.d/vaultllm_automation

echo "===================================================="
echo "  System setup complete!"
echo "===================================================="
