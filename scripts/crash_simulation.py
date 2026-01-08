#!/usr/bin/env python3
"""
Crash Simulation Script for Demo 5
Simulates a crash during backup by killing the process after a delay.
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def print_banner():
    """Print demo banner"""
    print("=" * 70)
    print("  CRASH SIMULATION - Demo 5")
    print("=" * 70)
    print()

def start_backup_and_crash(dataset_path: str, store_path: str, delay_seconds: float = 2.0):
    """
    Start a backup process and kill it after a delay to simulate crash.
    
    Args:
        dataset_path: Path to dataset directory
        store_path: Path to backup store
        delay_seconds: How long to wait before killing (default: 2 seconds)
    """
    print(f"📦 Starting backup process...")
    print(f"   Dataset: {dataset_path}")
    print(f"   Store: {store_path}")
    print(f"   Will crash after: {delay_seconds}s")
    print()
    
    # Build command
    cmd = [
        sys.executable,
        "-m",
        "src.cli.main",
        "backup",
        dataset_path,
        "--label",
        "Incomplete - Crashed",
        "--store",
        store_path
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print()
    
    # Start backup process
    print("⏳ Backup starting...")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    print(f"   Process ID: {process.pid}")
    print()
    
    # Wait for specified delay
    print(f"⏱️  Waiting {delay_seconds} seconds before crash...")
    time.sleep(delay_seconds)
    
    # Kill the process
    print()
    print("💥 SIMULATING CRASH - Killing backup process...")
    
    try:
        if sys.platform == "win32":
            # Windows: Use taskkill for forceful termination
            subprocess.run(
                ["taskkill", "/F", "/PID", str(process.pid)],
                capture_output=True
            )
        else:
            # Unix: Send SIGKILL
            os.kill(process.pid, signal.SIGKILL)
        
        # Wait for process to terminate
        process.wait(timeout=2)
        
    except subprocess.TimeoutExpired:
        print("⚠️  Process didn't terminate, forcing...")
        process.kill()
        process.wait()
    
    print("✓ Process killed successfully")
    print()
    
    # Show any output from the process
    stdout, stderr = process.communicate()
    
    if stdout:
        print("📄 Process output (before crash):")
        print(stdout[:500])  # Show first 500 chars
        if len(stdout) > 500:
            print("... (truncated)")
        print()
    
    if stderr:
        print("⚠️  Process errors:")
        print(stderr[:500])
        if len(stderr) > 500:
            print("... (truncated)")
        print()
    
    print("=" * 70)
    print("  CRASH SIMULATION COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Check snapshots: python -m src.cli.main list-snapshots --store", store_path)
    print("  2. Retry backup: python -m src.cli.main backup", dataset_path, "--store", store_path)
    print()

def main():
    """Main function"""
    print_banner()
    
    # Default paths
    dataset_path = "dataset/"
    store_path = "store/"
    delay_seconds = 2.0
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    if len(sys.argv) > 2:
        store_path = sys.argv[2]
    if len(sys.argv) > 3:
        try:
            delay_seconds = float(sys.argv[3])
        except ValueError:
            print(f"⚠️  Invalid delay: {sys.argv[3]}, using default: {delay_seconds}s")
    
    # Validate paths
    if not os.path.exists(dataset_path):
        print(f"❌ Error: Dataset path not found: {dataset_path}")
        print()
        print("Usage: python scripts/crash_simulation.py [dataset_path] [store_path] [delay_seconds]")
        print("Example: python scripts/crash_simulation.py dataset/ store/ 2.0")
        sys.exit(1)
    
    # Run simulation
    try:
        start_backup_and_crash(dataset_path, store_path, delay_seconds)
    except KeyboardInterrupt:
        print()
        print("⚠️  Simulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
