#!/usr/bin/env python3
"""
ItyFuzz EVM Runner - Execute fuzzing with different configurations
Similar to Table 1 ablation study in the paper
"""

import subprocess
import os
import sys
import json
import time
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict

class ItyFuzzRunner:
    def __init__(self, timeout=3600):
        self.timeout = timeout
        self.results_dir = Path("results")
        self.logs_dir = self.results_dir / "logs"
        self.data_dir = self.results_dir / "data"
        self.contracts_dir = Path("contracts")
        
        # Create directories
        self.results_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        self.contracts_dir.mkdir(exist_ok=True)
        
        # Test configurations
        self.configs = {
            "ItyFuzz": [],
            "ItyFuzz-DF": ["--dataflow"],
            "ItyFuzz-Rand": ["--random"]
        }
        
        # Contracts from paper (Table 1)
        self.contracts = [
            "dvd_unstoppable",
            "bacon_protocol", 
            "n00d_token",
            "egd_finance",
            "contract1_undisclosed",
            "contract2_undisclosed"
        ]
        
    def create_sample_contracts(self):
        """Create sample contract files for testing"""
        print("[*] Creating sample smart contracts...")
        
        # Simple Reentrancy vulnerable contract
        reentrancy_contract = """
pragma solidity ^0.8.0;

contract ReentrancyVulnerable {
    mapping(address => uint) public balances;
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint amount) external {
        require(balances[msg.sender] >= amount);
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;
    }
}
"""
        
        # Simple DoS vulnerable contract
        dos_contract = """
pragma solidity ^0.8.0;

contract DoSVulnerable {
    address[] public participants;
    
    function addParticipant(address addr) external {
        participants.push(addr);
    }
    
    function refund() external {
        for(uint i = 0; i < participants.length; i++) {
            (bool success, ) = participants[i].call{value: 1 ether}("");
            require(success);
        }
    }
}
"""
        
        # Simple Price Manipulation contract
        manipulation_contract = """
pragma solidity ^0.8.0;

interface IPriceOracle {
    function getPrice(address token) external view returns (uint);
}

contract PriceManipulation {
    IPriceOracle oracle;
    
    function liquidate(address user) external {
        uint price = oracle.getPrice(address(0));
        if (price < 100) {
            // liquidate user - vulnerable to price oracle manipulation
        }
    }
}
"""
        
        contracts = {
            "dvd_unstoppable": dos_contract,
            "bacon_protocol": reentrancy_contract,
            "n00d_token": dos_contract,
            "egd_finance": manipulation_contract,
            "contract1_undisclosed": reentrancy_contract,
            "contract2_undisclosed": dos_contract
        }
        
        for name, code in contracts.items():
            contract_file = self.contracts_dir / f"{name}.sol"
            if not contract_file.exists():
                contract_file.write_text(code)
                print(f"[+] Created {name}.sol")
    
    def run_fuzzing(self, contract: str, config_name: str, config_args: List[str]) -> Dict:
        """Run ItyFuzz on a single contract with given configuration"""
        contract_file = self.contracts_dir / f"{contract}.sol"
        log_file = self.logs_dir / f"{contract}_{config_name.replace('-', '_')}.log"
        
        if not contract_file.exists():
            print(f"[!] Contract not found: {contract_file}")
            return None
        
        print(f"[*] Running: {contract} with {config_name}")
        
        cmd = [
            "ityfuzz",
            "--contract", str(contract_file),
            "--evm",
            "--timeout", str(self.timeout),
            *config_args
        ]
        
        result = {
            "project": contract,
            "config": config_name,
            "exploit_type": "various",
            "start_time": datetime.now().isoformat(),
            "timeout": False,
            "oom": False,
            "detection_time": None,
            "status": "pending"
        }
        
        try:
            start = time.time()
            proc = subprocess.Popen(
                cmd,
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
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
            
            result["end_time"] = datetime.now().isoformat()
            print(f"[+] Completed: {contract} ({result['detection_time']})")
            
        except Exception as e:
            print(f"[!] Error running {contract}: {e}")
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def run_all_tests(self) -> List[Dict]:
        """Run full ablation study"""
        print("\n" + "="*60)
        print("ItyFuzz EVM Ablation Study")
        print("="*60 + "\n")
        
        self.create_sample_contracts()
        
        all_results = []
        total_tests = len(self.contracts) * len(self.configs)
        current = 0
        
        print(f"[*] Total tests: {total_tests}")
        print(f"[*] Timeout per contract: {self.timeout}s\n")
        
        for contract in self.contracts:
            for config_name, config_args in self.configs.items():
                current += 1
                print(f"\n[*] Test {current}/{total_tests}")
                print("-" * 60)
                
                result = self.run_fuzzing(contract, config_name, config_args)
                if result:
                    all_results.append(result)
        
        return all_results
    
    def save_results(self, results: List[Dict]):
        """Save results to CSV file (like Table 1)"""
        if not results:
            print("[!] No results to save")
            return
        
        output_file = self.data_dir / "results.csv"
        
        with open(output_file, 'w', newline='') as f:
            fieldnames = [
                "project", "config", "exploit_type", 
                "detection_time", "timeout", "oom", "status"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                row = {
                    "project": result["project"],
                    "config": result["config"],
                    "exploit_type": result.get("exploit_type", ""),
                    "detection_time": result.get("detection_time", ""),
                    "timeout": result["timeout"],
                    "oom": result["oom"],
                    "status": result["status"]
                }
                writer.writerow(row)
        
        print(f"\n[+] Results saved to: {output_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY TABLE (like Table 1 in paper)")
        print("="*60)
        print(f"{'Project':<25} {'Config':<15} {'Time':<15}")
        print("-"*60)
        
        for result in results:
            print(f"{result['project']:<25} {result['config']:<15} {result['detection_time']:<15}")
        
        # Count statistics
        timeouts = sum(1 for r in results if r["timeout"])
        completed = sum(1 for r in results if r["status"] == "completed")
        print("-"*60)
        print(f"Completed: {completed} | Timeouts: {timeouts} | Total: {len(results)}")
        print("="*60)
    
    def run_single_contract(self, contract: str, config: str = "ItyFuzz"):
        """Run fuzzing on a single contract"""
        if contract not in self.contracts:
            print(f"[!] Unknown contract: {contract}")
            print(f"Available: {', '.join(self.contracts)}")
            return
        
        if config not in self.configs:
            print(f"[!] Unknown config: {config}")
            print(f"Available: {', '.join(self.configs.keys())}")
            return
        
        self.create_sample_contracts()
        result = self.run_fuzzing(contract, config, self.configs[config])
        
        if result:
            print("\nResult:")
            print(json.dumps(result, indent=2))

def main():
    runner = ItyFuzzRunner(timeout=60)  # 60s per contract for quick test
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "single" and len(sys.argv) > 2:
            config = sys.argv[3] if len(sys.argv) > 3 else "ItyFuzz"
            runner.run_single_contract(sys.argv[2], config)
        else:
            print("Usage:")
            print("  python3 run_ityfuzz_evm.py              # Run all ablation tests")
            print("  python3 run_ityfuzz_evm.py single <contract>")
            print("  python3 run_ityfuzz_evm.py single <contract> <config>")
    else:
        results = runner.run_all_tests()
        runner.save_results(results)

if __name__ == "__main__":
    main()
