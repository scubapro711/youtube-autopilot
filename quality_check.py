#!/usr/bin/env python3
"""
Quality Gates Monitoring Script
Performs basic health checks on the repository
"""
import os
import subprocess
import json
from datetime import datetime

def run_command(cmd):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_git_status():
    """Check Git repository status"""
    success, stdout, stderr = run_command("git status --porcelain")
    return {
        "name": "Git Status",
        "status": "PASS" if success and not stdout else "FAIL",
        "details": "Working tree clean" if not stdout else f"Uncommitted changes: {stdout}"
    }

def check_remote_sync():
    """Check if local is in sync with remote"""
    success, stdout, stderr = run_command("git status -uno")
    is_synced = "up to date" in stdout.lower()
    return {
        "name": "Remote Sync",
        "status": "PASS" if is_synced else "WARN",
        "details": "Local branch is up to date with remote" if is_synced else "May need push/pull"
    }

def check_file_structure():
    """Check basic file structure"""
    required_files = ["README.md", ".gitignore"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    return {
        "name": "File Structure",
        "status": "PASS" if not missing_files else "WARN",
        "details": "All required files present" if not missing_files else f"Missing: {missing_files}"
    }

def main():
    """Run all quality checks"""
    checks = [
        check_git_status(),
        check_remote_sync(),
        check_file_structure()
    ]
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "PASS" if all(c["status"] == "PASS" for c in checks) else "WARN",
        "checks": checks
    }
    
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    main()
