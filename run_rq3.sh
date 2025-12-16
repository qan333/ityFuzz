#!/bin/bash
# RQ3 Runner - Execute RQ3 State Overhead Analysis
# Measures infant state corpus size, memory, and detection time

cd "$(dirname "$0")"

echo "=================================================="
echo "RQ3: State Overhead Analysis"
echo "=================================================="
echo ""
echo "This script measures:"
echo "  - Infant state corpus size over time (Figure 10)"
echo "  - Memory overhead for each configuration"
echo "  - Vulnerability detection time comparison"
echo ""

# Check if ityfuzz is installed
if ! command -v ityfuzz &> /dev/null; then
    echo "[!] ItyFuzz not found in PATH"
    echo "[*] Please run: bash setup_wsl.sh first"
    exit 1
fi

echo "[*] Running RQ3 analysis..."
echo "[*] Results will be saved to: ./results_rq3/"
echo ""

# Run the RQ3 analysis
python3 rq3_state_overhead.py

if [ $? -eq 0 ]; then
    echo ""
    echo "[*] Generating visualizations..."
    python3 rq3_visualization.py
    
    echo ""
    echo "[+] RQ3 Analysis Complete!"
    echo "[*] Check results_rq3/ folder for:"
    echo "    - data/rq3_summary.csv"
    echo "    - data/rq3_metrics.json"
    echo "    - plots/ (visualization images)"
else
    echo "[!] RQ3 analysis failed"
    exit 1
fi
