#!/bin/bash
# Setup for WSL - Install ItyFuzz using official ityfuzzup installer
# Run this once before using run.sh

set -e

echo "=========================================="
echo "ItyFuzz EVM Setup for WSL (Official Installer)"
echo "=========================================="

# Update system
echo "[*] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install system dependencies
echo "[*] Installing system dependencies..."
sudo apt-get install -y \
    build-essential cmake git curl wget \
    pkg-config libssl-dev libffi-dev \
    python3 python3-pip

# Install Python dependencies first
echo "[*] Installing Python dependencies..."
pip3 install web3 pycryptodome eth-keys eth-account

# Official ItyFuzz installation using ityfuzzup
echo "[*] Installing ItyFuzz using official ityfuzzup..."
echo "[*] This will download and setup ItyFuzz with all dependencies..."

# Install ityfuzzup and run it
curl -L https://ity.fuzz.land/ | bash

# Source bashrc to update PATH
echo "[*] Updating PATH..."
source ~/.bashrc || true

# Verify installation
echo "[*] Verifying ItyFuzz installation..."
if command -v ityfuzz &> /dev/null; then
    echo "[+] ItyFuzz installed successfully!"
    ityfuzz --version 2>/dev/null || echo "[+] ItyFuzz is ready to use"
else
    echo "[!] ItyFuzz command not found in PATH"
    echo "[*] Try running: source ~/.bashrc"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To use ItyFuzz EVM fuzzer:"
echo "  1. Source bashrc: source ~/.bashrc"
echo "  2. cd $(dirname "$0")"
echo "  3. bash run.sh"
echo ""
echo "To update ItyFuzz later, run: ityfuzzup"
echo ""
