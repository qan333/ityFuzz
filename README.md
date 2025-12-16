# ItyFuzz EVM - README

## Quick Start (WSL)

### 1. Initial Setup (run once)
```bash
bash setup_wsl.sh
source ~/.bashrc
```

### 2. Run Fuzzing
```bash
# Method 1: Run all ablation tests
bash run.sh

# Method 2: Run single contract
python3 run_ityfuzz_evm.py single dvd_unstoppable

# Method 3: Run with specific config
python3 run_ityfuzz_evm.py single bacon_protocol ItyFuzz-DF
```

## Files

- **setup_wsl.sh** - Install ItyFuzz and dependencies on WSL
- **run.sh** - Simple runner script
- **run_ityfuzz_evm.py** - Main fuzzing executor (generates results like Table 1)
- **config.yaml** - Configuration for fuzzing parameters
- **quickstart.py** - Quick start helper

## Output

Results are saved in `results/` folder:
- `results/logs/` - Detailed logs for each test
- `results/data/results.csv` - Summary table (like Table 1 in paper)

## Paper Results Replication

The script replicates the ablation study from the paper:
- 6 smart contracts (DVD, Bacon, N00d, EGD, Contract1, Contract2)
- 3 configurations (ItyFuzz, ItyFuzz-DF, ItyFuzz-Rand)
- Measures: Detection time, Timeout, OOM

## Customization

Edit `config.yaml` to modify:
- Timeout per contract
- Contracts to test
- Fuzzing parameters
- Output format

## Troubleshooting

If ityfuzz not found:
1. Check PATH: `echo $PATH`
2. Manual add: `export PATH="$PATH:$HOME/ityfuzz/target/release"`
3. Verify: `ityfuzz --help`

## Requirements

- WSL with Rust installed
- Python 3.7+
- 4GB+ RAM
- 1-2 hours for full ablation study

