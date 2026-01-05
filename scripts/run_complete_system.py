"""
Complete System Runner

Orchestrates the full lock contention monitoring system:
1. Generate dataset
2. Train ML model
3. Launch CLI monitor

This script runs the entire pipeline end-to-end.
"""

import subprocess
import sys
import os
import time

def run_command(command, description):
    """Execute a command and handle errors."""
    print(f"\n{'='*70}")
    print(f"{description}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        print(f"\nError: {description} failed with return code {result.returncode}")
        sys.exit(1)
    
    return result

def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║          LOCK CONTENTION MONITORING & PREDICTION SYSTEM           ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

This system will:
  1. Generate a dummy dataset of lock contention metrics
  2. Train an ML model to predict contention risk
  3. Launch a live CLI monitoring dashboard

Press Ctrl+C at any time to stop.
    """)
    
    time.sleep(2)
    
    # Step 1: Generate dataset
    run_command(
        "python scripts/generate_dataset.py",
        "STEP 1: Generating dummy dataset"
    )
    
    time.sleep(2)
    
    # Step 2: Train model
    run_command(
        "python scripts/train_model.py",
        "STEP 2: Training ML model"
    )
    
    time.sleep(2)
    
    # Step 3: Launch monitor
    print(f"\n{'='*70}")
    print("STEP 3: Launching live monitoring dashboard")
    print(f"{'='*70}\n")
    print("Monitor will start in 3 seconds...")
    time.sleep(3)
    
    # Run monitor (this will run until interrupted)
    subprocess.run("python scripts/cli_monitor.py --interval 2", shell=True)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSystem stopped by user.")
        sys.exit(0)
