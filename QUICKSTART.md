# depfix.py - Quick Start Guide

## 🚀 Get Started in 3 Minutes

### Installation

```bash
# 1. Navigate to the project directory
cd dependency_resolver

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify installation
python depfix.py --help
```

### Basic Commands

```bash
# Scan for conflicts
python depfix.py --scan

# Fix conflicts automatically
python depfix.py --auto-fix

# Lock your environment
python depfix.py --lock
```

### Common Workflows

#### Daily Development Workflow
```bash
# Check for conflicts after installing new packages
python depfix.py --scan

# If conflicts found, preview the fix
python depfix.py --auto-fix --dry-run

# Apply the fix
python depfix.py --auto-fix --yes
```

#### Production Deployment Workflow
```bash
# Lock your tested environment
python depfix.py --lock --output production.lock.json

# Later, restore the exact environment
python depfix.py --restore-lock production.lock.json
```

#### CI/CD Integration
```bash
# Fail build if conflicts detected
python depfix.py --scan
# Exit code 2 = conflicts found

# Get machine-readable output
python depfix.py --scan --json > results.json
```

## What It Does

**depfix.py** intelligently:
- 🔍 Detects version conflicts in your Python environment
- 🔧 Finds compatible versions that resolve conflicts
- 🔒 Locks environments for reproducibility
- 📊 Visualizes dependency graphs

## Example Output

```
$ python depfix.py --scan

[SCAN] Scanning for dependency conflicts...

[ERROR] Found 2 dependency conflicts:

1. Package: dependency-resolver-depfix (v1.0.0)
   Dependency: requests
   Installed: 2.26.0
   Required: >=2.28.0
   Type: version_mismatch

2. Package: osmnx (v2.0.6)
   Dependency: requests
   Installed: 2.26.0
   Required: >=2.27
   Type: version_mismatch
```

```
$ python depfix.py --auto-fix --dry-run

[FIX] Auto-fixing dependency conflicts...

[FIX] Resolution Plan (1 packages to update):

1. requests
   Current: 2.26.0
   Target:  2.32.5
   Conflicts: 2

[DRY-RUN] Skipping pip changes.
```

## Need More Help?

- 📖 Full documentation: See `README.md`
- 🧪 Testing details: See `TESTING_REPORT.md`
- 🐛 Issues: Check troubleshooting section in `TESTING_REPORT.md`

## Tips

- Always use `--dry-run` before applying fixes
- Use `--verbose` to see detailed logs
- Use `--json` for automation/scripting
- Lock environments before deploying to production
