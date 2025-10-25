import sys
import subprocess

def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)

def main() -> None:
    python = sys.executable

    print("[SETUP] Creating dependency conflicts...")
    # Create conflicts with requests and urllib3
    print("Installing requests 2.28.0...")
    run([python, "-m", "pip", "install", "requests==2.28.0", "--force-reinstall"])
    
    print("Installing incompatible urllib3 2.0.7...")
    run([python, "-m", "pip", "install", "urllib3==2.0.7", "--no-deps"])
    
    print("[DONE] Conflict setup complete.")
    print("Now run:")
    print("  python depfix.py --scan")
    print("Optionally auto-fix:")
    print("  python depfix.py --auto-fix --yes")

if __name__ == "__main__":
    main()
