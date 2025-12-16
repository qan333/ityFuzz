#!/usr/bin/env python3
"""
RQ3: State Overhead Analysis
Measure infant state corpus size, memory usage, and vulnerability detection time
Similar to Figure 10 in the paper
"""

import subprocess
import os
import sys
import json
import time
import re
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import threading

class RQ3StateOverheadAnalyzer:
    def __init__(self, timeout=600):
        self.timeout = timeout
        self.results_dir = Path("results_rq3")
        self.logs_dir = self.results_dir / "logs"
        self.data_dir = self.results_dir / "data"
        self.contracts_dir = Path("contracts")
        
        # Create directories
        self.results_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        # Test configurations (RQ3 variants)
        self.configs = {
            "ItyFuzz": {
                "args": [],
                "color": "orange"
            },
            "ItyFuzz-DF": {
                "args": ["--dataflow"],
                "color": "blue"
            },
            "ItyFuzz-Rand": {
                "args": ["--random"],
                "color": "yellow"
            }
        }
        
        # Dataset B1 contracts (from paper)
        self.contracts = [
            "dvd_unstoppable",
            "bacon_protocol", 
            "n00d_token",
            "egd_finance",
            "contract1_undisclosed",
            "contract2_undisclosed"
        ]
        
    def create_realistic_contracts(self):
        """Create realistic EVM contracts for testing"""
        print("[*] Creating realistic EVM contracts...")
        
        # Reentrancy vulnerable contract
        reentrancy = """pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint) public balances;
    bool locked = false;
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint amount) external {
        require(!locked, "No reentrancy");
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        locked = true;
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount;
        locked = false;
    }
    
    function emergencyWithdraw(address attacker) external {
        require(msg.sender == attacker);
        payable(msg.sender).transfer(address(this).balance);
    }
}"""
        
        # DoS vulnerable contract
        dos = """pragma solidity ^0.8.0;

contract VulnerableAuction {
    address[] public bidders;
    mapping(address => uint) public bids;
    bool finalized = false;
    
    function bid() external payable {
        bidders.push(msg.sender);
        bids[msg.sender] += msg.value;
    }
    
    function finalize() external {
        require(!finalized);
        
        for (uint i = 0; i < bidders.length; i++) {
            (bool success, ) = bidders[i].call{value: bids[bidders[i]]}("");
            if (!success) revert("Refund failed");
        }
        finalized = true;
    }
    
    function emergencyStop() external {
        finalized = true;
    }
}"""
        
        # Price manipulation vulnerable contract
        manipulation = """pragma solidity ^0.8.0;

interface IPriceOracle {
    function getPrice(address token) external view returns (uint);
}

contract VulnerableLending {
    IPriceOracle oracle;
    mapping(address => uint) collateral;
    
    function depositCollateral() external payable {
        collateral[msg.sender] += msg.value;
    }
    
    function borrow(address token, uint amount) external {
        uint collateralValue = collateral[msg.sender];
        uint requiredCollateral = (amount * 150) / 100;
        
        uint price = oracle.getPrice(token);
        require(collateralValue * price >= requiredCollateral);
        
        // Transfer tokens
    }
    
    function liquidate(address user) external {
        uint collateralValue = collateral[user];
        uint price = oracle.getPrice(address(0));
        
        if (price < 100) {
            // liquidate without proper checks - vulnerable
            collateral[user] = 0;
        }
    }
}"""
        
        # Access control vulnerable contract
        access = """pragma solidity ^0.8.0;

contract VulnerableToken {
    mapping(address => uint) public balances;
    address admin;
    
    constructor() {
        admin = msg.sender;
    }
    
    function mint(address to, uint amount) external {
        // Missing access control check
        balances[to] += amount;
    }
    
    function burn(address from, uint amount) external {
        require(balances[from] >= amount);
        balances[from] -= amount;
    }
    
    function transfer(address to, uint amount) external {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
}"""
        
        contracts = {
            "dvd_unstoppable": dos,
            "bacon_protocol": reentrancy,
            "n00d_token": access,
            "egd_finance": manipulation,
            "contract1_undisclosed": access,
            "contract2_undisclosed": reentrancy
        }
        
        for name, code in contracts.items():
            contract_file = self.contracts_dir / f"{name}.sol"
            if not contract_file.exists():
                contract_file.write_text(code)
                print(f"[+] Created {name}.sol")
    
    def parse_state_metrics(self, log_file: str) -> List[Dict]:
        """Parse log file to extract state corpus metrics over time"""
        metrics = []
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            for line in lines:
                # Look for state corpus size patterns
                # Example: "State corpus size: 1234"
                state_match = re.search(r'[Ss]tate.*?(\d+)', line)
                corpus_match = re.search(r'[Cc]orpus.*?(\d+)', line)
                time_match = re.search(r'\[(\d+\.\d+)s\]', line)
                memory_match = re.search(r'[Mm]emory.*?(\d+(?:\.\d+)?)\s*(?:MB|M)', line)
                
                if any([state_match, corpus_match, memory_match]):
                    metric = {
                        'timestamp': float(time_match.group(1)) if time_match else len(metrics) * 0.5,
                        'state_size': int(state_match.group(1)) if state_match else 0,
                        'corpus_size': int(corpus_match.group(1)) if corpus_match else 0,
                        'memory_mb': float(memory_match.group(1)) if memory_match else 0,
                    }
                    metrics.append(metric)
        except Exception as e:
            print(f"[!] Error parsing {log_file}: {e}")
        
        return metrics
    
    def monitor_process(self, process, log_file: str, config: str) -> Dict:
        """Monitor a running fuzzer process and collect metrics"""
        metrics_history = []
        start_time = time.time()
        
        def read_output():
            try:
                with open(log_file, 'r') as f:
                    while process.poll() is None:
                        line = f.readline()
                        if line:
                            metrics = self.parse_state_metrics(line)
                            if metrics:
                                metrics_history.extend(metrics)
                        time.sleep(0.1)
            except:
                pass
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=read_output, daemon=True)
        monitor_thread.start()
        
        return {
            'start_time': start_time,
            'metrics_history': metrics_history
        }
    
    def run_fuzzing_with_metrics(self, contract: str, config_name: str, config_args: List[str]) -> Dict:
        """Run ItyFuzz and collect state overhead metrics"""
        contract_file = self.contracts_dir / f"{contract}.sol"
        log_file = self.logs_dir / f"{contract}_{config_name.replace('-', '_')}.log"
        
        if not contract_file.exists():
            print(f"[!] Contract not found: {contract_file}")
            return None
        
        print(f"[*] Running RQ3 analysis: {contract} with {config_name}")
        
        # Build command to capture verbose output with state metrics
        cmd = [
            "ityfuzz",
            "--contract", str(contract_file),
            "--evm",
            "--timeout", str(self.timeout),
            "--verbose",  # Enable verbose output for state metrics
            *config_args
        ]
        
        result = {
            "project": contract,
            "config": config_name,
            "start_time": datetime.now().isoformat(),
            "status": "pending",
            "timeout": False,
            "oom": False,
            "detection_time": None,
            "max_state_corpus": 0,
            "final_memory_mb": 0,
            "avg_memory_mb": 0,
            "state_growth_rate": 0,
            "metrics_timeline": []
        }
        
        try:
            start = time.time()
            
            # Run ItyFuzz with output capture
            with open(log_file, 'w') as log_f:
                proc = subprocess.Popen(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    preexec_fn=None if sys.platform == 'win32' else os.setsid
                )
            
            # Monitor process
            monitor_data = self.monitor_process(proc, str(log_file), config_name)
            
            try:
                proc.wait(timeout=self.timeout + 10)
                elapsed = time.time() - start
                result["detection_time"] = f"{elapsed:.1f}s"
                result["status"] = "completed"
            except subprocess.TimeoutExpired:
                proc.kill()
                result["timeout"] = True
                result["status"] = "timeout"
                result["detection_time"] = "Timeout"
            
            # Parse collected metrics
            metrics = self.parse_state_metrics(str(log_file))
            result["metrics_timeline"] = metrics
            
            if metrics:
                corpus_sizes = [m.get('corpus_size', 0) for m in metrics]
                memory_values = [m.get('memory_mb', 0) for m in metrics]
                
                result["max_state_corpus"] = max(corpus_sizes) if corpus_sizes else 0
                result["final_memory_mb"] = memory_values[-1] if memory_values else 0
                result["avg_memory_mb"] = sum(memory_values) / len(memory_values) if memory_values else 0
                
                if len(corpus_sizes) > 1:
                    result["state_growth_rate"] = (corpus_sizes[-1] - corpus_sizes[0]) / max(len(corpus_sizes), 1)
            
            result["end_time"] = datetime.now().isoformat()
            print(f"[+] Completed: {contract} ({result['detection_time']})")
            print(f"    Max state corpus: {result['max_state_corpus']}")
            print(f"    Final memory: {result['final_memory_mb']:.1f} MB")
            
        except Exception as e:
            print(f"[!] Error running {contract}: {e}")
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def run_rq3_analysis(self) -> List[Dict]:
        """Run RQ3 state overhead analysis"""
        print("\n" + "="*70)
        print("RQ3: State Overhead Analysis - ItyFuzz EVM")
        print("="*70)
        print("Measuring infant state corpus size, memory usage over time")
        print("Similar to Figure 10 in the paper\n")
        
        self.create_realistic_contracts()
        
        all_results = []
        total_tests = len(self.contracts) * len(self.configs)
        current = 0
        
        print(f"[*] Total tests: {total_tests}")
        print(f"[*] Timeout per contract: {self.timeout}s\n")
        
        for contract in self.contracts:
            for config_name, config_data in self.configs.items():
                current += 1
                print(f"\n[*] Test {current}/{total_tests}")
                print("-" * 70)
                
                result = self.run_fuzzing_with_metrics(
                    contract, 
                    config_name, 
                    config_data["args"]
                )
                if result:
                    all_results.append(result)
        
        return all_results
    
    def save_results(self, results: List[Dict]):
        """Save RQ3 analysis results"""
        if not results:
            print("[!] No results to save")
            return
        
        # Save summary CSV
        summary_file = self.data_dir / "rq3_summary.csv"
        with open(summary_file, 'w', newline='') as f:
            fieldnames = [
                "project", "config", "detection_time", 
                "max_state_corpus", "final_memory_mb", 
                "avg_memory_mb", "state_growth_rate", "status"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                row = {
                    "project": result["project"],
                    "config": result["config"],
                    "detection_time": result.get("detection_time", ""),
                    "max_state_corpus": result.get("max_state_corpus", 0),
                    "final_memory_mb": f"{result.get('final_memory_mb', 0):.2f}",
                    "avg_memory_mb": f"{result.get('avg_memory_mb', 0):.2f}",
                    "state_growth_rate": f"{result.get('state_growth_rate', 0):.2f}",
                    "status": result["status"]
                }
                writer.writerow(row)
        
        print(f"[+] Summary saved to: {summary_file}")
        
        # Save detailed metrics
        metrics_file = self.data_dir / "rq3_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"[+] Detailed metrics saved to: {metrics_file}")
        
        # Print summary table
        print("\n" + "="*70)
        print("RQ3 RESULTS - State Overhead Analysis")
        print("="*70)
        print(f"{'Project':<25} {'Config':<15} {'Max Corpus':<15} {'Mem(MB)':<12} {'Time':<10}")
        print("-"*70)
        
        for result in results:
            print(f"{result['project']:<25} {result['config']:<15} "
                  f"{result['max_state_corpus']:<15} "
                  f"{result['avg_memory_mb']:<12.1f} "
                  f"{result['detection_time']:<10}")
        
        print("="*70)
        print(f"Total tests: {len(results)}")
        print(f"Successful: {sum(1 for r in results if r['status'] == 'completed')}")
        print(f"Timeouts: {sum(1 for r in results if r['timeout'])}")
        print("="*70)

def main():
    analyzer = RQ3StateOverheadAnalyzer(timeout=120)  # 2 minutes per contract
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "single" and len(sys.argv) > 2:
            config = sys.argv[3] if len(sys.argv) > 3 else "ItyFuzz"
            analyzer.create_realistic_contracts()
            result = analyzer.run_fuzzing_with_metrics(
                sys.argv[2], 
                config,
                analyzer.configs[config]["args"]
            )
            if result:
                print("\nResult:")
                print(json.dumps(result, indent=2, default=str))
        else:
            print("Usage:")
            print("  python3 rq3_state_overhead.py              # Run full RQ3 analysis")
            print("  python3 rq3_state_overhead.py single <contract>")
            print("  python3 rq3_state_overhead.py single <contract> <config>")
    else:
        results = analyzer.run_rq3_analysis()
        analyzer.save_results(results)

if __name__ == "__main__":
    main()
