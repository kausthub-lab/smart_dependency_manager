#!/usr/bin/env python3
"""
depfix.py - A robust CLI tool for detecting and automatically resolving 
dependency conflicts within Python virtual environments.

Author: Expert Python Developer
Version: 1.0.0
"""

import argparse
import json
import logging
import subprocess
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Any
from urllib.parse import quote

import requests
from packaging import version
from packaging.specifiers import SpecifierSet, InvalidSpecifier
from packaging.requirements import Requirement


class DependencyConflictResolver:
    """Main class for dependency conflict detection and resolution."""
    
    def __init__(self, verbose: bool = False, debug: bool = False, log_file: Optional[str] = None):
        """Initialize the resolver with logging configuration."""
        self.setup_logging(verbose, debug, log_file)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'depfix/1.0.0'})
        
    def setup_logging(self, verbose: bool, debug: bool, log_file: Optional[str] = None):
        """Configure logging based on verbosity level."""
        level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)

    def run_pip_check(self) -> List[Dict[str, Any]]:
        """Use `pip check` to detect broken dependencies in the current interpreter.

        Returns a list of conflicts with keys compatible with this tool's schema.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True,
                text=True,
                check=False
            )
            combined = "".join([part for part in [result.stdout, "\n", result.stderr] if part])
            output = combined.strip()
            conflicts: List[Dict[str, Any]] = []
            if not output:
                return conflicts

            for line in output.splitlines():
                # Example line:
                # requests 2.26.0 requires urllib3<1.27,>=1.21.1, but you have urllib3 2.2.0.
                if " requires " in line and ", but you have " in line:
                    try:
                        left, right = line.split(", but you have ", 1)
                        pkg_part, req_part = left.split(" requires ", 1)
                        pkg_name, pkg_version = pkg_part.strip().split(" ", 1)
                        have_part = right.strip().rstrip(".")
                        # have_part like: urllib3 2.2.0
                        dep_name, installed_version = have_part.split(" ", 1)
                        # req_part like: urllib3<1.27,>=1.21.1
                        if " " in req_part:
                            # sometimes includes extras/markers; keep as-is
                            required_constraint = req_part.split(" ")[1].strip()
                        else:
                            # name glued to spec; strip name prefix if present
                            required_constraint = req_part
                            if required_constraint.startswith(dep_name):
                                required_constraint = required_constraint[len(dep_name):]

                        conflicts.append({
                            'package': pkg_name,
                            'package_version': pkg_version,
                            'conflicting_dependency': dep_name,
                            'installed_version': installed_version,
                            'required_constraint': required_constraint,
                            'conflict_type': 'version_mismatch'
                        })
                    except Exception:
                        continue

            return conflicts
        except Exception as e:
            self.logger.debug(f"pip check failed or unavailable: {e}")
            return []
        
    def get_installed_packages(self) -> List[Dict[str, Any]]:
        """Get installed packages using pipdeptree."""
        try:
            self.logger.info("Executing pipdeptree --json-tree...")
            result = subprocess.run(
                [sys.executable, "-m", "pipdeptree", "--json-tree"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            if not result.stdout.strip():
                self.logger.warning("No packages found in environment")
                return []
                
            data = json.loads(result.stdout)
            self.logger.debug(f"Retrieved {len(data)} top-level packages")
            return data

        except subprocess.CalledProcessError as e:
            self.logger.error(f"pipdeptree failed: {e}")
            raise RuntimeError("Failed to get installed packages. Is pipdeptree installed?")
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse pipdeptree output: {e}")
            raise RuntimeError("Invalid JSON output from pipdeptree")
            
    def get_pypi_metadata(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Fetch package metadata from PyPI."""
        try:
            url = f"https://pypi.org/pypi/{quote(package_name)}/json"
            self.logger.debug(f"Fetching metadata for {package_name}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Failed to fetch metadata for {package_name}: {e}")
            return None
            
    def parse_version_constraints(self, requires_dist: List[str]) -> Dict[str, str]:
        """Parse version constraints from requires_dist field."""
        constraints = {}
        
        if not requires_dist:
            return constraints
            
        for req_str in requires_dist:
            try:
                parsed = Requirement(req_str)
                name = parsed.name
                specifier_text = str(parsed.specifier)
                if name and specifier_text:
                    constraints[name] = specifier_text
            except Exception as e:
                self.logger.debug(f"Failed to parse requirement '{req_str}': {e}")
                continue
                
        return constraints
        
    def build_dependency_map(self, packages_data: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Build a comprehensive dependency map from pipdeptree output."""
        dependency_map = {}
        
        def process_package(pkg_data: Dict[str, Any], parent_name: str = None):
            """Recursively process package and its dependencies."""
            # Handle both old and new pipdeptree JSON format
            if 'package' in pkg_data:
                pkg_info = pkg_data['package']
            else:
                pkg_info = pkg_data
            pkg_name = pkg_info.get('key', '')
            pkg_version = pkg_info.get('installed_version', '')
            
            if not pkg_name:
                return
                
            if pkg_name not in dependency_map:
                dependency_map[pkg_name] = {
                    'version': pkg_version,
                    'dependencies': {},  # dep_name -> installed_version
                    'constraints': {},   # dep_name -> required specifier string
                    'dependents': set(),
                    'pypi_metadata': None
                }
                
            # Add current version if not set
            if not dependency_map[pkg_name]['version']:
                dependency_map[pkg_name]['version'] = pkg_version
                
            # Process dependencies
            deps = pkg_data.get('dependencies', [])
            for dep in deps:
                # Handle both old and new pipdeptree JSON format
                if 'package' in dep:
                    dep_info = dep['package']
                else:
                    dep_info = dep
                dep_name = dep_info.get('key', '')
                if dep_name:
                    dependency_map[pkg_name]['dependencies'][dep_name] = dep_info.get('installed_version', '')
                    # required constraint as reported by pipdeptree (may be None/empty)
                    required_spec = dep.get('required_version') or dep.get('version') or ''
                    # Skip 'Any' and empty constraints
                    if required_spec and required_spec != 'Any':
                        dependency_map[pkg_name]['constraints'][dep_name] = required_spec
                    # Ensure the dependency exists in the map before referencing
                    if dep_name not in dependency_map:
                        dependency_map[dep_name] = {
                            'version': dep_info.get('installed_version', ''),
                            'dependencies': {},
                            'constraints': {},
                            'dependents': set(),
                            'pypi_metadata': None
                        }
                    dependency_map[dep_name]['dependents'].add(pkg_name)
                    
                    # Recursively process sub-dependencies
                    process_package(dep, pkg_name)
                    
        # Process all top-level packages
        for pkg_data in packages_data:
            process_package(pkg_data)
            
        return dependency_map
        
    def detect_conflicts(self, dependency_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect dependency conflicts using installed environment requirements (pipdeptree)."""
        conflicts: List[Dict[str, Any]] = []
        self.logger.info("Analyzing dependency conflicts (local requirements)...")

        for pkg_name, pkg_info in dependency_map.items():
            constraints: Dict[str, str] = pkg_info.get('constraints', {})
            if not constraints:
                continue

            for dep_name, dep_constraint in constraints.items():
                if dep_name not in dependency_map:
                    continue
                installed_version = dependency_map[dep_name]['version']
                try:
                    spec_set = SpecifierSet(dep_constraint)
                    if not spec_set.contains(installed_version):
                        conflict = {
                            'package': pkg_name,
                            'package_version': pkg_info['version'],
                            'conflicting_dependency': dep_name,
                            'installed_version': installed_version,
                            'required_constraint': dep_constraint,
                            'conflict_type': 'version_mismatch'
                        }
                        conflicts.append(conflict)
                        self.logger.debug(f"Conflict: {pkg_name} requires {dep_name}{dep_constraint} but {installed_version} is installed")
                except InvalidSpecifier:
                    self.logger.warning(f"Invalid version specifier '{dep_constraint}' for {dep_name}")
                    continue

        return conflicts
        
    def get_available_versions(self, package_name: str) -> List[str]:
        """Get all available versions for a package from PyPI."""
        metadata = self.get_pypi_metadata(package_name)
        if not metadata:
            return []
            
        versions = list(metadata.get('releases', {}).keys())
        # Sort versions properly
        try:
            versions.sort(key=lambda v: version.Version(v), reverse=True)
        except version.InvalidVersion:
            # Keep original order if sorting fails
            pass
            
        return versions
        
    def find_compatible_version(self, package_name: str, constraints: List[str]) -> Optional[str]:
        """Find a version that satisfies all given constraints."""
        available_versions = self.get_available_versions(package_name)
        
        for version_str in available_versions:
            try:
                version_obj = version.Version(version_str)
                satisfies_all = True
                
                for constraint in constraints:
                    try:
                        spec_set = SpecifierSet(constraint)
                        if not spec_set.contains(version_str):
                            satisfies_all = False
                            break
                    except InvalidSpecifier:
                        self.logger.warning(f"Invalid constraint '{constraint}' for {package_name}")
                        satisfies_all = False
                        break
                        
                if satisfies_all:
                    return version_str
                    
            except version.InvalidVersion:
                continue
                
        return None
        
    def resolve_conflicts(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve conflicts by finding compatible versions."""
        resolutions = []
        
        # Group conflicts by package
        conflict_groups = defaultdict(list)
        for conflict in conflicts:
            dep_name = conflict['conflicting_dependency']
            conflict_groups[dep_name].append(conflict)
            
        self.logger.info(f"Resolving conflicts for {len(conflict_groups)} packages...")
        
        for dep_name, dep_conflicts in conflict_groups.items():
            self.logger.debug(f"Resolving conflicts for {dep_name}")
            
            # Collect all constraints for this dependency
            constraints = []
            for conflict in dep_conflicts:
                constraints.append(conflict['required_constraint'])
                
            # Find compatible version
            compatible_version = self.find_compatible_version(dep_name, constraints)
            
            if compatible_version:
                resolution = {
                    'package': dep_name,
                    'current_version': dep_conflicts[0]['installed_version'],
                    'resolved_version': compatible_version,
                    'conflicts': dep_conflicts
                }
                resolutions.append(resolution)
                self.logger.info(f"Resolved {dep_name}: {dep_conflicts[0]['installed_version']} -> {compatible_version}")
            else:
                self.logger.error(f"Cannot resolve conflicts for {dep_name} - no compatible version found")
                
        return resolutions
        
    def apply_fixes(self, resolutions: List[Dict[str, Any]]) -> bool:
        """Apply the resolved dependency fixes."""
        if not resolutions:
            self.logger.info("No fixes to apply")
            return True
            
        self.logger.info(f"Applying {len(resolutions)} fixes...")
        success = True
        
        for resolution in resolutions:
            package_name = resolution['package']
            current_version = resolution['current_version']
            target_version = resolution['resolved_version']
            
            try:
                # Uninstall current version
                self.logger.info(f"Uninstalling {package_name}-{current_version}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "-y", package_name],
                    check=True,
                    capture_output=True
                )
                
                # Install target version
                self.logger.info(f"Installing {package_name}-{target_version}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", f"{package_name}=={target_version}"],
                    check=True,
                    capture_output=True
                )
                
                self.logger.info(f"Successfully updated {package_name} to {target_version}")
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to update {package_name}: {e}")
                success = False
                
        return success
        
    def lock_environment(self, output_file: str = "requirements.lock.json") -> bool:
        """Lock the current environment to a JSON file."""
        try:
            self.logger.info("Locking current environment...")
            
            # Get current package list
            result = subprocess.run(
                [sys.executable, "-m", "pip", "freeze"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            lock_data = {}
            for line in result.stdout.strip().split('\n'):
                if '==' in line:
                    package, version = line.split('==', 1)
                    lock_data[package.strip()] = version.strip()
                    
            # Write to file
            with open(output_file, 'w') as f:
                json.dump(lock_data, f, indent=2, sort_keys=True)
                
            self.logger.info(f"Environment locked to {output_file}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to get package list: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to write lock file: {e}")
            return False

    def list_outdated(self) -> List[Dict[str, Any]]:
        """Return outdated packages via pip list --outdated."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--outdated', '--format', 'json'],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout or '[]')
        except subprocess.CalledProcessError as e:
            self.logger.error(f"pip list --outdated failed: {e}")
            return []
        except json.JSONDecodeError:
            return []

    def restore_lock(self, lock_file: str = 'requirements.lock.json') -> bool:
        """Reinstall packages pinned in the given lock file."""
        try:
            with open(lock_file, 'r') as f:
                lock_data = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to read lock file {lock_file}: {e}")
            return False

        # Install all exact versions
        spec_list = [f"{pkg}=={ver}" for pkg, ver in lock_data.items()]
        if not spec_list:
            self.logger.info("Lock file is empty; nothing to install")
            return True
        try:
            self.logger.info(f"Restoring {len(spec_list)} packages from lock...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', *spec_list], check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to restore from lock: {e}")
            return False

    def build_graph(self, packages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return a serializable dependency graph based on pipdeptree data."""
        dep_map = self.build_dependency_map(packages_data)
        serializable = {}
        for name, info in dep_map.items():
            serializable[name] = {
                'version': info.get('version', ''),
                'dependencies': info.get('dependencies', {}),
                'constraints': info.get('constraints', {}),
                'dependents': sorted(list(info.get('dependents', [])))
            }
        return serializable

    def build_graph_dot(self, packages_data: List[Dict[str, Any]]) -> str:
        """Return a DOT representation of the dependency graph."""
        dep_map = self.build_dependency_map(packages_data)
        lines = ["digraph deps {"]
        for src, info in dep_map.items():
            for dst in info.get('dependencies', {}).keys():
                lines.append(f'  "{src}" -> "{dst}";')
        lines.append("}")
        return "\n".join(lines)


def print_conflicts(conflicts: List[Dict[str, Any]]):
    """Print conflicts in a human-readable format."""
    if not conflicts:
        print("[OK] No dependency conflicts found!")
        return
        
    print(f"\n[ERROR] Found {len(conflicts)} dependency conflicts:\n")
    
    for i, conflict in enumerate(conflicts, 1):
        print(f"{i}. Package: {conflict['package']} (v{conflict['package_version']})")
        print(f"   Dependency: {conflict['conflicting_dependency']}")
        print(f"   Installed: {conflict['installed_version']}")
        print(f"   Required: {conflict['required_constraint']}")
        print(f"   Type: {conflict['conflict_type']}")
        print()


def print_resolutions(resolutions: List[Dict[str, Any]]):
    """Print resolution plan in a human-readable format."""
    if not resolutions:
        print("No resolutions available")
        return
        
    print(f"\n[FIX] Resolution Plan ({len(resolutions)} packages to update):\n")
    
    for i, resolution in enumerate(resolutions, 1):
        print(f"{i}. {resolution['package']}")
        print(f"   Current: {resolution['current_version']}")
        print(f"   Target:  {resolution['resolved_version']}")
        print(f"   Conflicts: {len(resolution['conflicts'])}")
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Detect and automatically resolve dependency conflicts in Python environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python depfix.py --scan                    # Scan for conflicts
  python depfix.py --auto-fix               # Auto-fix conflicts
  python depfix.py --lock                   # Lock environment
  python depfix.py --scan --verbose         # Verbose scanning
  python depfix.py --auto-fix --debug       # Debug auto-fix
        """
    )
    
    parser.add_argument(
        '--scan', 
        action='store_true',
        help='Scan for dependency conflicts'
    )
    
    parser.add_argument(
        '--auto-fix', 
        action='store_true',
        help='Automatically resolve detected conflicts'
    )
    
    parser.add_argument(
        '--lock', 
        action='store_true',
        help='Lock current environment to requirements.lock.json'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug output'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Emit machine-readable JSON output for scan/fix results'
    )
    
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Proceed non-interactively for --auto-fix (assume yes)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='requirements.lock.json',
        help='Output file for lock command (default: requirements.lock.json)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be fixed without changing anything'
    )
    parser.add_argument(
        '--check-updates',
        action='store_true',
        help='List outdated packages'
    )
    parser.add_argument(
        '--restore-lock',
        metavar='LOCKFILE',
        nargs='?',
        const='requirements.lock.json',
        help='Reinstall environment from a lock file (default: requirements.lock.json)'
    )
    parser.add_argument(
        '--graph',
        nargs='?',
        const='json',
        choices=['json', 'dot'],
        help='Output dependency graph (json or dot)'
    )
    parser.add_argument(
        '--log-file',
        metavar='FILE',
        help='Write logs to the specified file (e.g., depfix.log)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.scan, args.auto_fix, args.lock, args.check_updates, args.restore_lock, args.graph]):
        parser.error("At least one action must be specified (--scan, --auto-fix, --lock, --check-updates, --restore-lock, or --graph)")
        
    # Initialize resolver
    resolver = DependencyConflictResolver(verbose=args.verbose, debug=args.debug, log_file=args.log_file)
    
    try:
        if args.scan:
            print("[SCAN] Scanning for dependency conflicts...")
            packages_data = resolver.get_installed_packages()
            dependency_map = resolver.build_dependency_map(packages_data)
            conflicts = resolver.detect_conflicts(dependency_map)
            # Fallback to pip check if none found
            if not conflicts:
                pip_check_conflicts = resolver.run_pip_check()
                if pip_check_conflicts:
                    conflicts = pip_check_conflicts
            if args.json:
                output = {
                    'action': 'scan',
                    'conflict_count': len(conflicts),
                    'conflicts': conflicts
                }
                print(json.dumps(output, indent=2))
            else:
                print_conflicts(conflicts)
            if conflicts:
                sys.exit(2)
            else:
                sys.exit(0)
            
        if args.auto_fix:
            print("[FIX] Auto-fixing dependency conflicts...")
            packages_data = resolver.get_installed_packages()
            dependency_map = resolver.build_dependency_map(packages_data)
            conflicts = resolver.detect_conflicts(dependency_map)
            if not conflicts:
                pip_check_conflicts = resolver.run_pip_check()
                if pip_check_conflicts:
                    conflicts = pip_check_conflicts
            
            if conflicts:
                resolutions = resolver.resolve_conflicts(conflicts)
                if args.json:
                    output = {
                        'action': 'auto-fix',
                        'conflict_count': len(conflicts),
                        'resolutions': resolutions
                    }
                    print(json.dumps(output, indent=2))
                else:
                    print_resolutions(resolutions)
                
                if resolutions:
                    proceed = args.yes
                    if not proceed:
                        response = input("\nProceed with applying fixes? (y/N): ")
                        proceed = response.lower() in ['y', 'yes']
                    if proceed:
                        if args.dry_run:
                            print("[DRY-RUN] Skipping pip changes.")
                            success = True
                        else:
                            success = resolver.apply_fixes(resolutions)
                        if success:
                            print("[OK] All fixes applied successfully!")
                            sys.exit(0)
                        else:
                            print("[ERROR] Some fixes failed. Check logs for details.")
                            sys.exit(1)
                    else:
                        print("Fix application cancelled.")
                        sys.exit(0)
                else:
                    print("[ERROR] No compatible resolutions found.")
                    sys.exit(2)
            else:
                print("[OK] No conflicts to fix!")
                sys.exit(0)
                
        if args.lock:
            success = resolver.lock_environment(args.output)
            if success:
                print(f"[OK] Environment locked to {args.output}")
                sys.exit(0)
            else:
                print("[ERROR] Failed to lock environment")
                sys.exit(1)

        if args.check_updates:
            updates = resolver.list_outdated()
            if args.json:
                print(json.dumps({'action': 'check-updates', 'updates': updates}, indent=2))
            else:
                if not updates:
                    print("All packages up to date.")
                else:
                    print("Outdated packages:")
                    for item in updates:
                        print(f"- {item.get('name')} {item.get('version')} -> {item.get('latest_version')}")
            sys.exit(0)

        if args.restore_lock is not None:
            ok = resolver.restore_lock(args.restore_lock)
            sys.exit(0 if ok else 1)

        if args.graph:
            packages_data = resolver.get_installed_packages()
            if args.graph == 'json':
                graph = resolver.build_graph(packages_data)
                print(json.dumps(graph, indent=2))
            else:
                dot = resolver.build_graph_dot(packages_data)
                print(dot)
            sys.exit(0)
                
    except KeyboardInterrupt:
        print("\n[WARN] Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        resolver.logger.error(f"Unexpected error: {e}")
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
