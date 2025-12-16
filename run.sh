#!/bin/bash
# Simple runner script for ItyFuzz EVM on WSL
# Runs the Python fuzzing script

cd "$(dirname "$0")"

echo "=================================================="
echo "ItyFuzz EVM Fuzzer - WSL Runner"
echo "=================================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip
fi

# Check if ityfuzz is installed
if ! command -v ityfuzz &> /dev/null; then
    echo "[!] ItyFuzz not found in PATH"
    echo "[*] Make sure to install ItyFuzz first:"
    echo "    - Clone: git clone https://github.com/fuzzland/ityfuzz.git"
    echo "    - Build: cd ityfuzz && cargo build --release"
    echo "    - Add to PATH: export PATH=\$PATH:$(pwd)/ityfuzz/target/release"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "[*] Running ItyFuzz EVM ablation study..."
echo "[*] Results will be saved to: ./results/"
echo ""

# Run the Python script
if [ $# -eq 0 ]; then
    python3 run_ityfuzz_evm.py
else
    python3 run_ityfuzz_evm.py "$@"
fi

echo ""
echo "[+] Done! Check results/ folder for outputs"
