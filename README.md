# depfix.py - Dependency Conflict Resolver

A robust command-line interface (CLI) tool that intelligently detects and automatically resolves dependency conflicts within Python virtual environments, going beyond the capabilities of standard tools like pip.

## Features

### 🔍 Conflict Detection (`--scan`)

- Executes `pipdeptree --json-tree` to get structured package information
- Queries PyPI JSON API to fetch package metadata and version requirements
- Uses the `packaging` library to parse version specifiers (>=, <, ~=, etc.)
- Identifies conflicts when version requirements don't overlap
- Outputs human-readable conflict reports

### 🔧 Auto-Resolution (`--auto-fix`)

- Constructs dependency graphs for analysis
- Implements intelligent resolution strategies:
  - **Maximizing Compatibility**: Chooses versions that resolve conflicts without creating new ones
  - **Minimizing Change**: Prefers minor/patch updates over major version changes
  - **Preferring Upgrades**: Favors upgrading packages over downgrading as a tie-breaker
- Automatically executes `pip uninstall` and `pip install` commands
- Handles unsolvable conflicts gracefully

### 🔒 Environment Locking (`--lock`)

- Generates `requirements.lock.json` with exact package versions
- Creates a reproducible environment snapshot
- JSON format for easy integration with other tools

## Installation

1. Install required dependencies:

```bash
pip install -r requirements.txt
```

2. Install pipdeptree (required for dependency analysis):

```bash
pip install pipdeptree
```

## Usage

### Basic Commands

```bash
# Scan for conflicts
python depfix.py --scan

# Auto-fix detected conflicts
python depfix.py --auto-fix

# Lock environment to requirements.lock.json
python depfix.py --lock

# Combine multiple actions
python depfix.py --scan --auto-fix --lock
```

### Advanced Options

```bash
# Verbose output
python depfix.py --scan --verbose

# Debug mode (shows detailed logs)
python depfix.py --auto-fix --debug

# Custom lock file output
python depfix.py --lock --output my-environment.lock.json
```

### Example Workflow

1. **Scan for conflicts:**

```bash
python depfix.py --scan --verbose
```

2. **Review conflicts and auto-fix:**

```bash
python depfix.py --auto-fix
```

3. **Lock the resolved environment:**

```bash
python depfix.py --lock
```

## Output Examples

### Conflict Detection Output

```
❌ Found 2 dependency conflicts:

1. Package: scikit-learn (v1.0.2)
   Dependency: numpy
   Installed: 1.21.0
   Required: >=1.22.0
   Type: version_mismatch

2. Package: pandas (v1.3.0)
   Dependency: numpy
   Installed: 1.21.0
   Required: >=1.21.0,<2.0.0
   Type: version_mismatch
```

### Resolution Plan Output

```
🔧 Resolution Plan (1 packages to update):

1. numpy
   Current: 1.21.0
   Target:  1.22.5
   Conflicts: 2
```

## Technical Details

### Dependencies

- **requests**: HTTP client for PyPI API calls
- **packaging**: Version and specifier parsing
- **pipdeptree**: External tool for dependency tree analysis

### Architecture

- **Modular Design**: Separate classes and methods for detection, resolution, and execution
- **Robust Error Handling**: Comprehensive try-catch blocks with clear error messages
- **Logging**: Configurable logging levels (DEBUG, INFO, WARNING)
- **Rate Limiting**: Built-in delays to respect PyPI API limits

### Resolution Algorithm

1. Groups conflicts by package
2. Collects all version constraints for each conflicting package
3. Fetches available versions from PyPI
4. Finds versions that satisfy all constraints
5. Prioritizes solutions based on compatibility, minimal change, and upgrade preference

## Error Handling

The tool handles various error scenarios:

- Network failures during PyPI API calls
- Invalid version specifiers
- Failed pip operations
- Missing dependencies
- Unsolvable conflicts

## Contributing

This tool is designed to be extensible. Key areas for enhancement:

- Additional resolution strategies
- Integration with other package managers
- GUI interface
- Batch processing capabilities

This project is provided as-is for educational and development purposes.
difference between the pip and depfix.py.

| Function                                           | **pip (built-in resolver)**                        | **Your Dependency Resolver Project**                                        |
| -------------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------- |
| 🧩 **Scans existing environment for conflicts**    | ❌ Only checks during installation                 | ✅ Scans _already installed_ packages for version conflicts                 |
| 🧠 **Understands dependency chains**               | ⚠️ Limited (just enough for install)               | ✅ Builds a full dependency graph and explains conflicts clearly            |
| 📊 **Generates detailed conflict reports**         | ❌ No reporting, just error messages               | ✅ Produces structured JSON + CLI reports for every conflict                |
| 🧰 **Auto-fixes broken environments**              | ❌ You must manually reinstall or upgrade packages | ✅ Automatically selects compatible versions and resolves them              |
| 🧪 **Creates controlled test conflicts**           | ❌ Not possible                                    | ✅ `conflict_setup.py` purposely installs incompatible versions for testing |
| 📈 **Analyzes and visualizes dependency health**   | ❌ No                                              | ✅ Optional reporting of dependency health and conflict count               |
| 🧠 **Educational/Debugging insight**               | ❌ Opaque (hidden internal logic)                  | ✅ Transparent, step-by-step explanation of how dependency resolution works |
| 💬 **Custom CLI options (scan, auto-fix, export)** | ❌ None                                            | ✅ Custom CLI commands: `--scan`, `--auto-fix`, `--json`, etc.              |
| 💾 **Outputs results for further analysis**        | ❌ No output files                                 | ✅ Saves `.json` report for developers or CI/CD systems                     |
