#!/bin/bash
# Quick setup for WSL - Install ItyFuzz and dependencies
# Run this once before using run.sh

set -e

echo "=========================================="
echo "ItyFuzz EVM Setup for WSL"
echo "=========================================="

# Update system
echo "[*] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install dependencies
echo "[*] Installing dependencies..."
sudo apt-get install -y \
    build-essential cmake git curl wget \
    pkg-config libssl-dev libffi-dev \
    python3 python3-pip rustc cargo

# Install/update Rust
echo "[*] Setting up Rust..."
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# Clone and build ItyFuzz
echo "[*] Cloning ItyFuzz repository..."
ITYFUZZ_PATH="$HOME/ityfuzz"

if [ ! -d "$ITYFUZZ_PATH" ]; then
    git clone https://github.com/fuzzland/ityfuzz.git "$ITYFUZZ_PATH"
else
    echo "[+] ItyFuzz already cloned, updating..."
    cd "$ITYFUZZ_PATH"
    git pull origin main
fi

echo "[*] Building ItyFuzz (this may take 5-10 minutes)..."
cd "$ITYFUZZ_PATH"
cargo build --release

# Setup PATH
echo "[*] Setting up PATH..."
if ! grep -q "ityfuzz/target/release" ~/.bashrc; then
    echo 'export PATH="$PATH:'$ITYFUZZ_PATH'/target/release"' >> ~/.bashrc
    echo "[+] Added ItyFuzz to PATH in ~/.bashrc"
fi

# Install Python dependencies
echo "[*] Installing Python dependencies..."
pip3 install web3 pycryptodome eth-keys eth-account

# Test installation
echo "[*] Testing ItyFuzz installation..."
if "$ITYFUZZ_PATH/target/release/ityfuzz" --help > /dev/null 2>&1; then
    echo "[+] ItyFuzz installation successful!"
else
    echo "[!] ItyFuzz test failed"
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
