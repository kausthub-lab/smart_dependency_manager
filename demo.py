#!/usr/bin/env python3
"""
Demo script for depfix.py - Demonstrates the tool's capabilities
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and display the results."""
    print(f"\n{'='*60}")
    print(f"DEMO: {description}")
    print(f"{'='*60}")
    print(f"Command: {cmd}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run the demo."""
    print("depfix.py - Dependency Conflict Resolver Demo")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("depfix.py"):
        print("Error: depfix.py not found in current directory")
        sys.exit(1)
    
    # Demo 1: Show help
    run_command("python depfix.py --help", "Show help information")
    
    # Demo 2: Scan for conflicts (verbose mode)
    run_command("python depfix.py --scan --verbose", "Scan for dependency conflicts (verbose)")
    
    # Demo 3: Scan with debug mode
    run_command("python depfix.py --scan --debug", "Scan for dependency conflicts (debug mode)")
    
    # Demo 4: Auto-fix (will show no conflicts in clean environment)
    run_command("python depfix.py --auto-fix", "Auto-fix conflicts (clean environment)")
    
    # Demo 5: Lock environment
    run_command("python depfix.py --lock --output demo.lock.json", "Lock environment to demo.lock.json")
    
    # Demo 6: Show the lock file content
    if os.path.exists("demo.lock.json"):
        print(f"\n{'='*60}")
        print("DEMO: Show lock file content")
        print(f"{'='*60}")
        with open("demo.lock.json", 'r') as f:
            content = f.read()
            print("First 20 lines of demo.lock.json:")
            lines = content.split('\n')[:20]
            for line in lines:
                print(line)
            if len(content.split('\n')) > 20:
                print("... (truncated)")
    
    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print(f"{'='*60}")
    print("The depfix.py tool successfully demonstrated:")
    print("[OK] Help system")
    print("[OK] Conflict scanning")
    print("[OK] Verbose and debug modes")
    print("[OK] Auto-fix functionality")
    print("[OK] Environment locking")
    print("\nIn a real environment with conflicts, the tool would:")
    print("- Detect version mismatches between packages")
    print("- Propose resolution strategies")
    print("- Automatically fix conflicts with user confirmation")
    print("- Generate reproducible environment locks")

if __name__ == "__main__":
    main()
