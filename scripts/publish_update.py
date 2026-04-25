from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE_DATA_PATH = ROOT / "site" / "data" / "latest.json"


def run(cmd: list[str], check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd or ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def main() -> int:
    if not (ROOT / ".git").exists():
        print("git repository not found. run: git init -b main")
        return 2

    print("step: generate data")
    run([sys.executable, "scripts/generate_update.py"])

    latest_path = ROOT / "data" / "latest.json"
    if not latest_path.exists():
        print("latest.json not found after generation")
        return 2

    site_root = ROOT / "site"
    if not site_root.exists():
        print(f"site folder not found: {site_root}")
        return 2

    SITE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(latest_path, SITE_DATA_PATH)
    print(f"step: synced {latest_path} -> {SITE_DATA_PATH}")

    add = run(["git", "add", "data/latest.json", "data/history.json", "site/data/latest.json"], check=False, cwd=ROOT)
    if add.returncode != 0:
        print(add.stdout)
        print(add.stderr)
        return add.returncode
    status = run(
        ["git", "status", "--short", "data/latest.json", "data/history.json", "site/data/latest.json"],
        check=False,
        cwd=ROOT,
    ).stdout.strip()
    if not status:
        print("no changes to commit")
        return 0

    msg = f"chore: update monitor data ({datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')})"
    commit = run(["git", "commit", "-m", msg], check=False, cwd=ROOT)
    if commit.returncode != 0:
        print(commit.stdout)
        print(commit.stderr)
        return commit.returncode

    print("step: push current repo")
    push = run(["git", "push", "origin", "main"], check=False, cwd=ROOT)
    print(push.stdout)
    print(push.stderr)
    return push.returncode


if __name__ == "__main__":
    raise SystemExit(main())
