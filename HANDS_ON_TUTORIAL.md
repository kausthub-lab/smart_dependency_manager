# Hands-On Tutorial: Testing Dependency Conflicts

## 🎯 Your Environment Already Has Conflicts!

Good news - your current environment has **real conflicts** you can test with right now!

### What We Found:
```
Package: dependency-resolver-depfix (v1.0.0)
   ↳ Needs: requests >= 2.28.0
   ✗ But you have: requests 2.26.0

Package: osmnx (v2.0.6)
   ↳ Needs: requests >= 2.27
   ✗ But you have: requests 2.26.0
```

## 🚀 Quick Start: Fix Your Current Conflicts

### Step 1: Scan for Conflicts
```powershell
cd "D:\Version Conflict\dependency_resolver"
python depfix.py --scan
```

**Expected Output:**
```
[ERROR] Found 2 dependency conflicts:
1. Package: dependency-resolver-depfix (v1.0.0)
   Dependency: requests
   Installed: 2.26.0
   Required: >=2.28.0
```

### Step 2: Preview the Fix
```powershell
python depfix.py --auto-fix --dry-run --yes
```

**Expected Output:**
```
[FIX] Resolution Plan (1 packages to update):

1. requests
   Current: 2.26.0
   Target:  2.32.5
   Conflicts: 2

[DRY-RUN] Skipping pip changes.
```

### Step 3: Apply the Fix
```powershell
python depfix.py --auto-fix --yes
```

This will:
1. Uninstall requests 2.26.0
2. Install requests 2.32.5
3. Resolve both conflicts

### Step 4: Verify It's Fixed
```powershell
python depfix.py --scan
```

**Expected Output:**
```
[OK] No dependency conflicts found!
```

---

## 🧪 Create Your Own Test Conflicts

Want to practice? Here's how to create test conflicts:

### Option 1: Simple Test (5 minutes)

**Step 1:** Create test environment
```powershell
# Create and activate
python -m venv test_env
.\test_env\Scripts\Activate.ps1

# Install depfix dependencies
pip install requests packaging pipdeptree
```

**Step 2:** Create a conflict
```powershell
# Install old requests
pip install requests==2.25.0

# Now install something needing newer requests
pip install httpx==0.28.0
# This will warn but install anyway
```

**Step 3:** Detect the conflict
```powershell
# Copy depfix.py to test location or run from parent
python ..\depfix.py --scan
```

**Step 4:** Fix it
```powershell
python ..\depfix.py --auto-fix --yes
```

**Step 5:** Clean up
```powershell
deactivate
cd ..
Remove-Item -Recurse -Force test_env
```

### Option 2: Real-World Scenario (10 minutes)

Test with common data science packages:

```powershell
# Setup
python -m venv ml_test
.\ml_test\Scripts\Activate.ps1
pip install requests packaging pipdeptree

# Install old numpy
pip install numpy==1.19.5

# Install pandas needing newer numpy
pip install pandas==2.0.0
# Will show warnings

# Test depfix
python ..\depfix.py --scan
python ..\depfix.py --auto-fix --dry-run

# Clean up
deactivate
Remove-Item -Recurse -Force ml_test
```

---

## 📊 Understanding the Output

### When You Run `--scan`:

```
[SCAN] Scanning for dependency conflicts...
```
- Runs pipdeptree to get all packages
- Checks version requirements
- Compares with installed versions

### Conflict Details:
```
1. Package: osmnx (v2.0.6)
   Dependency: requests
   Installed: 2.26.0
   Required: >=2.27
   Type: version_mismatch
```

This means:
- **Package**: The package that has a requirement
- **Dependency**: What it depends on
- **Installed**: Current version in your environment
- **Required**: Version specification needed
- **Type**: Type of conflict (version_mismatch, missing, etc.)

### When You Run `--auto-fix --dry-run`:

```
[FIX] Resolution Plan (1 packages to update):

1. requests
   Current: 2.26.0
   Target:  2.32.5
   Conflicts: 2
```

This shows:
- **Package to update**: requests
- **Current version**: What you have now
- **Target version**: What will be installed
- **Conflicts resolved**: How many issues this fixes

---

## 🔍 Advanced Testing

### Compare with pip check
```powershell
# Standard pip check
pip check

# Your tool (more detailed)
python depfix.py --scan --verbose
```

### Get JSON Output for Automation
```powershell
# Machine-readable output
python depfix.py --scan --json > conflicts.json

# View in PowerShell
Get-Content conflicts.json | ConvertFrom-Json
```

### Visualize Dependencies
```powershell
# JSON graph
python depfix.py --graph json > graph.json

# DOT format (for Graphviz)
python depfix.py --graph dot > graph.dot
```

### Check for Updates
```powershell
# See which packages have newer versions
python depfix.py --check-updates
```

---

## 🎓 Learning Exercises

### Exercise 1: Understanding Transitive Dependencies
```powershell
# Install a package
pip install beautifulsoup4

# Check its dependencies
python depfix.py --graph json | Select-String "beautifulsoup4" -Context 5

# Now downgrade one of its dependencies
pip install soupsieve==1.0.0 --force-reinstall

# Scan for conflicts
python depfix.py --scan
```

### Exercise 2: Version Constraints
```powershell
# Install package with strict requirements
pip install flask==2.3.0

# Try to install something incompatible
pip install werkzeug==3.0.0 --force-reinstall

# Detect and fix
python depfix.py --scan
python depfix.py --auto-fix --dry-run
```

### Exercise 3: Lock and Restore
```powershell
# Lock working environment
python depfix.py --lock --output good_state.lock.json

# Break something
pip install requests==2.0.0 --force-reinstall

# Scan to see issues
python depfix.py --scan

# Restore from lock
python depfix.py --restore-lock good_state.lock.json

# Verify
python depfix.py --scan
```

---

## 🎯 Common Testing Scenarios

### Scenario 1: After Installing New Package
```powershell
# Install new package
pip install some-new-package

# Always check for conflicts
python depfix.py --scan

# Fix if needed
python depfix.py --auto-fix
```

### Scenario 2: Before Deploying to Production
```powershell
# Scan current environment
python depfix.py --scan

# If clean, lock it
python depfix.py --lock --output production.lock.json

# Deploy the lock file with your code
```

### Scenario 3: Debugging Broken Environment
```powershell
# Check what's broken
python depfix.py --scan --verbose

# Get detailed dependency graph
python depfix.py --graph json > debug_graph.json

# Try to auto-fix
python depfix.py --auto-fix
```

---

## 💡 Pro Tips

1. **Always test in a virtual environment first**
   ```powershell
   python -m venv test_env
   .\test_env\Scripts\Activate.ps1
   ```

2. **Use --dry-run before applying fixes**
   ```powershell
   python depfix.py --auto-fix --dry-run
   # Review the plan
   python depfix.py --auto-fix --yes  # Then apply
   ```

3. **Save scan results for comparison**
   ```powershell
   python depfix.py --scan > before.txt
   # ... make changes ...
   python depfix.py --scan > after.txt
   Compare-Object (Get-Content before.txt) (Get-Content after.txt)
   ```

4. **Use verbose mode to understand what's happening**
   ```powershell
   python depfix.py --scan --verbose --log-file debug.log
   ```

---

## 🔧 Troubleshooting Your Tests

### Problem: No conflicts detected but pip shows warnings

**Solution**: Your environment might be okay, or conflicts are at install-time only.
```powershell
# Force a conflict
pip install requests==2.20.0 --force-reinstall
python depfix.py --scan
```

### Problem: Fix doesn't work

**Solution**: Some conflicts can't be auto-resolved.
```powershell
# Check verbose output
python depfix.py --auto-fix --verbose

# Manually check PyPI for compatible versions
pip index versions requests
```

### Problem: Test environment activation fails

**Solution**: PowerShell execution policy
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📝 Summary Workflow

```powershell
# 1. Check for conflicts
python depfix.py --scan

# 2. If conflicts found, preview fix
python depfix.py --auto-fix --dry-run

# 3. Apply the fix
python depfix.py --auto-fix --yes

# 4. Verify it's fixed
python depfix.py --scan

# 5. Lock the working state
python depfix.py --lock
```

---

## 🎉 You're Ready!

Now you can:
- ✅ Detect conflicts in any Python environment
- ✅ Understand what causes dependency conflicts
- ✅ Automatically resolve them with depfix.py
- ✅ Test and verify your environments
- ✅ Lock and restore working configurations

Start with your current environment's conflicts and work from there!
