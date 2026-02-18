import os
import sys
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
CRITICAL_FOLDERS = [
    "apps/accounts",
    "apps/wallets",
    "apps/transactions",
    "apps/ai_engine",
    "apps/ipfs_storage"
]

REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_DIR.mkdir(exist_ok=True)


def hash_file(filepath):
    """Generate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def snapshot_hashes():
    """Create hash snapshot of critical files."""
    snapshot = {}
    for folder in CRITICAL_FOLDERS:
        for path in Path(folder).rglob("*.py"):
            snapshot[str(path)] = hash_file(path)
    return snapshot


def detect_modifications(before, after):
    modified = []
    for file, hash_before in before.items():
        if file in after and after[file] != hash_before:
            modified.append(file)
    return modified


def run_pytest():
    """Run pytest suite with advanced options."""
    print("🚀 Running FubaPay E2E Test Suite...\n")
    cmd = [
        "pytest",
        "-n", "auto",
        "--dist=loadfile"
    ]
    result = subprocess.run(cmd)
    return result.returncode


def main():
    print("🔍 Creating file snapshot BEFORE tests...")
    before_snapshot = snapshot_hashes()

    start_time = datetime.now()

    exit_code = run_pytest()

    print("\n🔍 Creating file snapshot AFTER tests...")
    after_snapshot = snapshot_hashes()

    modified_files = detect_modifications(before_snapshot, after_snapshot)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n==============================")
    print("📊 FubaPay E2E Test Summary")
    print("==============================")
    print(f"Duration: {duration} seconds")

    if modified_files:
        print("\n⚠️ WARNING: Critical files modified during tests:")
        for f in modified_files:
            print(f" - {f}")
    else:
        print("\n✅ No critical file modifications detected.")

    if exit_code != 0:
        print("\n❌ TESTS FAILED.")
        sys.exit(exit_code)
    else:
        print("\n🎉 ALL TESTS PASSED SUCCESSFULLY.")
        sys.exit(0)


if __name__ == "__main__":
    main()
