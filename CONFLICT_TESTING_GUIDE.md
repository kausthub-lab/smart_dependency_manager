# How to Manually Test Dependency Conflicts with depfix.py

## Method 1: Create an Isolated Test Environment

### Step 1: Create a New Virtual Environment

```powershell
# Create a clean test environment
python -m venv test_env

# Activate it
.\test_env\Scripts\Activate.ps1
```

### Step 2: Install Conflicting Packages

**Scenario A: Install Old Version First**
```powershell
# Install an old version of requests
pip install requests==2.25.0

# Now install a package that requires a newer requests
pip install httpx==0.28.0
# httpx requires requests>=2.26.0, but you have 2.25.0

# Check for conflicts
python ..\depfix.py --scan
```

**Scenario B: NumPy Version Conflicts**
```powershell
# Install old NumPy
pip install numpy==1.19.0

# Install pandas that needs newer NumPy
pip install pandas==2.0.0
# pandas requires numpy>=1.22.0

# Check conflicts
python ..\depfix.py --scan
```

**Scenario C: Multiple Package Conflicts**
```powershell
# Install specific versions
pip install urllib3==1.25.0
pip install requests==2.31.0
# requests 2.31.0 requires urllib3<3,>=1.21.1
# This should work

# Now force an incompatible urllib3
pip install --force-reinstall urllib3==2.0.0

# Install something that needs old urllib3
pip install botocore==1.29.0
# botocore needs urllib3<1.27

# Check conflicts
python ..\depfix.py --scan
```

## Method 2: Use the Existing Environment (Simpler)

Your current environment already has real conflicts! Let's check them:

```powershell
# Navigate to the tool directory
cd D:\Version Conflict\dependency_resolver

# Scan your current environment
python depfix.py --scan --verbose

# You should see conflicts like:
# - dependency-resolver-depfix requires requests>=2.28.0
# - osmnx requires requests>=2.27
# - But you have requests 2.26.0 installed
```

## Method 3: Create Conflicts from requirements.txt

### Step 1: Create a Conflicting Requirements File

Create `test_requirements.txt`:
```text
# This will create conflicts
requests==2.25.0
httpx==0.28.0        # Needs requests>=2.26.0
beautifulsoup4==4.12.0
lxml==5.0.0          # Needs specific library versions
```

### Step 2: Install and Test
```powershell
# In your test environment
pip install -r test_requirements.txt

# Some installations will fail or show warnings
# Then scan for conflicts
python depfix.py --scan
```

## Method 4: Downgrade Packages to Create Conflicts

```powershell
# Check current version
pip show requests

# Downgrade to create conflicts
pip install requests==2.26.0 --force-reinstall

# Now scan
python depfix.py --scan

# You'll see conflicts with packages requiring newer requests
```

## Complete Testing Workflow

### 1. **Create the Conflict**
```powershell
# In test environment
pip install requests==2.26.0
pip install python-docx==1.1.0  # Requires requests>=2.28.0
```

### 2. **Detect the Conflict**
```powershell
# Basic scan
python depfix.py --scan

# Detailed scan with JSON output
python depfix.py --scan --json > conflict_report.json

# Verbose mode to see all details
python depfix.py --scan --verbose
```

### 3. **Analyze the Conflict**
```powershell
# Check dependency graph
python depfix.py --graph json > deps.json

# Visualize dependencies (if graphviz installed)
python depfix.py --graph dot > deps.dot
dot -Tpng deps.dot -o deps.png
```

### 4. **Preview the Fix**
```powershell
# Dry-run to see what would be fixed
python depfix.py --auto-fix --dry-run

# With verbose output
python depfix.py --auto-fix --dry-run --verbose
```

### 5. **Apply the Fix**
```powershell
# Interactive mode (asks for confirmation)
python depfix.py --auto-fix

# Non-interactive mode (automatic)
python depfix.py --auto-fix --yes
```

### 6. **Verify the Fix**
```powershell
# Scan again to confirm no conflicts
python depfix.py --scan

# Should show: [OK] No dependency conflicts found!
```

### 7. **Lock the Working Environment**
```powershell
# Create a lock file
python depfix.py --lock --output working_env.lock.json
```

## Real-World Testing Scenarios

### Scenario 1: Machine Learning Stack Conflicts
```powershell
# Common ML package conflicts
pip install numpy==1.19.0
pip install tensorflow==2.13.0  # Needs numpy>=1.22.0
pip install scipy==1.11.0       # Needs numpy>=1.21.6

python depfix.py --scan
python depfix.py --auto-fix --dry-run
```

### Scenario 2: Web Framework Conflicts
```powershell
pip install django==3.2.0
pip install djangorestframework==3.14.0  # May have version conflicts
pip install celery==5.3.0

python depfix.py --scan
```

### Scenario 3: Data Science Stack
```powershell
pip install pandas==1.3.0
pip install scikit-learn==1.3.0  # Needs numpy>=1.17.3
pip install matplotlib==3.8.0    # Needs numpy>=1.21

python depfix.py --scan --verbose
```

## Using pip check for Comparison

```powershell
# Compare depfix.py with pip check
pip check

# Then run depfix.py
python depfix.py --scan

# depfix.py provides:
# - More detailed conflict information
# - Automatic resolution suggestions
# - Ability to actually fix the conflicts
```

## Tips for Testing

1. **Always use virtual environments for testing**
   - Keeps your main environment clean
   - Easy to destroy and recreate

2. **Start simple**
   - Begin with 2-3 packages
   - Gradually increase complexity

3. **Document your findings**
   ```powershell
   # Save scan results
   python depfix.py --scan > scan_results.txt
   
   # Save fix plan
   python depfix.py --auto-fix --dry-run > fix_plan.txt
   ```

4. **Test edge cases**
   - Multiple packages depending on the same library
   - Circular dependencies
   - Version ranges vs exact versions

## Common Conflict Patterns to Test

### Pattern 1: Transitive Dependency Conflicts
```
Package A → requires Library X >= 2.0
Package B → requires Library X < 2.0
❌ No version satisfies both
```

### Pattern 2: Cascade Updates
```
Update Package A → needs newer Library X
Newer Library X → breaks Package B
✅ depfix.py finds compatible versions for all
```

### Pattern 3: Pin Conflicts
```
requirements.txt: Library X == 1.5.0 (pinned)
Package Y: requires Library X >= 2.0
❌ Pinned version conflicts
```

## Cleanup After Testing

```powershell
# Deactivate virtual environment
deactivate

# Remove test environment
Remove-Item -Recurse -Force test_env

# Or recreate fresh
python -m venv test_env
```

## Advanced: Create Custom Conflict Scripts

Create `create_conflict.py`:
```python
import subprocess
import sys

def create_conflict():
    """Install packages that will conflict"""
    conflicts = [
        ("requests==2.25.0", "Old requests"),
        ("httpx==0.28.0", "New httpx needing requests>=2.26.0")
    ]
    
    for package, description in conflicts:
        print(f"Installing {description}: {package}")
        subprocess.run([sys.executable, "-m", "pip", "install", package])
    
    print("\nConflicts created! Run: python depfix.py --scan")

if __name__ == "__main__":
    create_conflict()
```

Run it:
```powershell
python create_conflict.py
python depfix.py --scan
```

## Monitoring and Logging

```powershell
# Enable detailed logging
python depfix.py --scan --debug --log-file conflict_test.log

# Review the log
Get-Content conflict_test.log

# JSON output for automation
python depfix.py --scan --json | ConvertFrom-Json
```

## Summary Checklist

- [ ] Created isolated test environment
- [ ] Installed conflicting packages
- [ ] Ran `--scan` to detect conflicts
- [ ] Used `--verbose` to understand details
- [ ] Ran `--auto-fix --dry-run` to preview fixes
- [ ] Applied fixes with `--auto-fix`
- [ ] Verified fix with another `--scan`
- [ ] Locked working environment with `--lock`
- [ ] Cleaned up test environment

## Quick Reference Commands

```powershell
# Setup
python -m venv test_env && .\test_env\Scripts\Activate.ps1

# Create conflict
pip install requests==2.26.0 && pip install httpx==0.28.0

# Detect
python depfix.py --scan

# Preview fix
python depfix.py --auto-fix --dry-run

# Apply fix
python depfix.py --auto-fix --yes

# Verify
python depfix.py --scan

# Cleanup
deactivate && Remove-Item -Recurse -Force test_env
```
