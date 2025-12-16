#!/usr/bin/env python3
"""
Quick start script - Setup and run ItyFuzz EVM in one command
"""

import subprocess
import sys
import os
import platform

def run_command(cmd, description=""):
    """Execute a shell command"""
    if description:
        print(f"[*] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed: {description}")
        return False

def main():
    print("="*60)
    print("ItyFuzz EVM Quick Start")
    print("="*60)
    print()
    
    system = platform.system()
    
    if system == "Windows":
        print("[*] Windows detected - you need WSL to run this")
        print("[*] Run this command in WSL terminal:")
        print()
        print("    bash run.sh")
        print()
        sys.exit(0)
    
    # For Linux/WSL
    print("[1] Checking Python...")
    if not run_command("python3 --version"):
        print("[!] Python 3 required")
        sys.exit(1)
    
    print("[2] Checking for contracts directory...")
    if not os.path.exists("contracts"):
        os.makedirs("contracts")
        print("[+] Created contracts directory")
    
    print("[3] Starting fuzzing runner...")
    print()
    
    # Run the main fuzzer
    run_command("python3 run_ityfuzz_evm.py", "Running ablation study")
    
    print()
    print("[+] Fuzzing complete!")
    print("[*] Results saved to: ./results/")
    print()

if __name__ == "__main__":
    main()
