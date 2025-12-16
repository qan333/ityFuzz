#!/usr/bin/env python3
"""
RQ3 Visualization - Plot state corpus size over time (like Figure 10)
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List

class RQ3Visualizer:
    def __init__(self):
        self.data_dir = Path("results_rq3/data")
        self.plot_dir = Path("results_rq3/plots")
        self.plot_dir.mkdir(exist_ok=True)
        
        self.colors = {
            "ItyFuzz": "#FF8C42",      # Orange
            "ItyFuzz-DF": "#1F77B4",   # Blue
            "ItyFuzz-Rand": "#FFD700"  # Yellow
        }
    
    def load_metrics(self) -> List[Dict]:
        """Load metrics from JSON file"""
        metrics_file = self.data_dir / "rq3_metrics.json"
        
        if not metrics_file.exists():
            print(f"[!] Metrics file not found: {metrics_file}")
            return []
        
        with open(metrics_file, 'r') as f:
            return json.load(f)
    
    def plot_state_corpus_timeline(self, metrics: List[Dict]):
        """Plot state corpus size over time (Figure 10 style)"""
        print("[*] Generating state corpus timeline plot...")
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Group by config
        config_data = {}
        for result in metrics:
            config = result.get('config', 'Unknown')
            if config not in config_data:
                config_data[config] = {'times': [], 'sizes': []}
            
            timeline = result.get('metrics_timeline', [])
            if timeline:
                times = [m.get('timestamp', 0) for m in timeline]
                sizes = [m.get('corpus_size', 0) for m in timeline]
                
                if times and sizes:
                    config_data[config]['times'].append(times)
                    config_data[config]['sizes'].append(sizes)
        
        # Plot each configuration
        for config, data in sorted(config_data.items()):
            if data['times'] and data['sizes']:
                # Average across contracts for this config
                avg_times = []
                avg_sizes = []
                
                for times, sizes in zip(data['times'], data['sizes']):
                    if times:
                        # Interpolate to common timeline
                        max_time = max(times)
                        common_timeline = np.linspace(0, max_time, 20)
                        interpolated = np.interp(common_timeline, times, sizes)
                        
                        if not avg_times:
                            avg_times = list(common_timeline)
                        avg_sizes.append(interpolated)
                
                if avg_sizes:
                    avg_sizes_arr = np.mean(avg_sizes, axis=0)
                    color = self.colors.get(config, '#000000')
                    ax.plot(avg_times, avg_sizes_arr, 
                           label=config, color=color, linewidth=2.5, marker='o')
        
        ax.set_xlabel('Time (s)', fontsize=12)
        ax.set_ylabel('Infant State Corpus Size', fontsize=12)
        ax.set_title('RQ3: Infant State Corpus Storage Overhead\n(Similar to Figure 10)', 
                    fontsize=14, fontweight='bold')
        ax.set_yscale('log')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        output_file = self.plot_dir / "state_corpus_timeline.png"
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"[+] Plot saved: {output_file}")
        plt.close()
    
    def plot_memory_comparison(self, metrics: List[Dict]):
        """Plot memory usage by configuration"""
        print("[*] Generating memory usage comparison plot...")
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Group by contract and config
        contracts = {}
        for result in metrics:
            project = result.get('project', 'Unknown')
            config = result.get('config', 'Unknown')
            memory = result.get('final_memory_mb', 0)
            
            if project not in contracts:
                contracts[project] = {}
            contracts[project][config] = memory
        
        if not contracts:
            print("[!] No memory data to plot")
            return
        
        # Prepare data
        projects = sorted(contracts.keys())
        configs = sorted(self.colors.keys())
        
        x = np.arange(len(projects))
        width = 0.25
        
        for i, config in enumerate(configs):
            values = [contracts[p].get(config, 0) for p in projects]
            offset = (i - 1) * width
            ax.bar(x + offset, values, width, label=config, 
                   color=self.colors.get(config, '#000000'), alpha=0.8)
        
        ax.set_xlabel('Smart Contract', fontsize=12)
        ax.set_ylabel('Memory Usage (MB)', fontsize=12)
        ax.set_title('RQ3: Memory Overhead Comparison', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(projects, rotation=45, ha='right')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')
        
        output_file = self.plot_dir / "memory_comparison.png"
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"[+] Plot saved: {output_file}")
        plt.close()
    
    def plot_detection_time_comparison(self, metrics: List[Dict]):
        """Plot vulnerability detection time comparison"""
        print("[*] Generating detection time comparison plot...")
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Parse detection times
        contracts = {}
        for result in metrics:
            project = result.get('project', 'Unknown')
            config = result.get('config', 'Unknown')
            time_str = result.get('detection_time', '0s')
            
            # Parse time value
            try:
                if 'Timeout' in time_str:
                    time_val = 600  # Use timeout value
                else:
                    time_val = float(time_str.replace('s', ''))
            except:
                time_val = 0
            
            if project not in contracts:
                contracts[project] = {}
            contracts[project][config] = time_val
        
        if not contracts:
            print("[!] No detection time data to plot")
            return
        
        # Prepare data
        projects = sorted(contracts.keys())
        configs = sorted(self.colors.keys())
        
        x = np.arange(len(projects))
        width = 0.25
        
        for i, config in enumerate(configs):
            values = [contracts[p].get(config, 0) for p in projects]
            offset = (i - 1) * width
            ax.bar(x + offset, values, width, label=config,
                   color=self.colors.get(config, '#000000'), alpha=0.8)
        
        ax.set_xlabel('Smart Contract', fontsize=12)
        ax.set_ylabel('Detection Time (seconds)', fontsize=12)
        ax.set_title('RQ3: Vulnerability Detection Time Comparison', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(projects, rotation=45, ha='right')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, axis='y')
        
        output_file = self.plot_dir / "detection_time_comparison.png"
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"[+] Plot saved: {output_file}")
        plt.close()
    
    def generate_all_plots(self):
        """Generate all RQ3 visualization plots"""
        print("\n" + "="*70)
        print("RQ3 Visualization - Generating Plots")
        print("="*70 + "\n")
        
        metrics = self.load_metrics()
        if not metrics:
            print("[!] No metrics to visualize")
            return
        
        self.plot_state_corpus_timeline(metrics)
        self.plot_memory_comparison(metrics)
        self.plot_detection_time_comparison(metrics)
        
        print(f"\n[+] All plots saved to: {self.plot_dir}")
        print("="*70)

def main():
    visualizer = RQ3Visualizer()
    visualizer.generate_all_plots()

if __name__ == "__main__":
    main()
