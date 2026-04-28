#!/usr/bin/env python3
"""
dedup.py — Detect duplicate files in a folder (recursively).

Strategy: 3-tier comparison for speed
  1. Size check — different sizes can't be duplicates (instant)
  2. Hash check — same-size files get hashed (SHA-256)
  3. Groups files by hash and reports duplicates

Usage:
  python dedup.py <path>              # scan a folder
  python dedup.py <path> --delete     # move duplicates to trash/staging
  python dedup.py <path> --json       # output as JSON
  python dedup.py <path> --min-size 1024  # ignore files smaller than 1KB
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Default directories to skip
DEFAULT_SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "venv.bak",
    ".idea", ".vscode", ".cache", ".tox", ".mypy_cache", ".pytest_cache",
    "dist", "build", ".next",
}

BUFFER_SIZE = 65536  # 64KB read buffer for hashing


def get_file_hash(filepath: Path, log_callback=None) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                sha256.update(data)
    except (PermissionError, OSError) as e:
        msg = f"  [WARN] Cannot read {filepath}: {e}"
        if log_callback:
            log_callback(msg)
        else:
            print(msg, file=sys.stderr)
        return ""
    return sha256.hexdigest()


def scan_directory(
    root: Path,
    skip_dirs: set[str] | None = None,
    follow_symlinks: bool = False,
    min_size: int = 0,
    log_callback=None,
    progress_callback=None,
    cancel_event=None,
) -> dict[str, list[Path]]:
    """
    Scan directory recursively and group duplicate files by hash.

    Returns dict: hash -> list of file paths (only entries with 2+ files).

    Args:
        log_callback: Optional callable(str) for log messages (GUI support).
        progress_callback: Optional callable(current, total, message) for progress.
        cancel_event: Optional threading.Event to cancel the scan early.
    """
    if skip_dirs is None:
        skip_dirs = DEFAULT_SKIP_DIRS

    def _log(msg, is_error=False):
        if log_callback:
            log_callback(msg)
        else:
            print(msg, file=sys.stderr if is_error else sys.stdout)

    # Phase 1: Collect all files and group by size
    size_groups: dict[int, list[Path]] = defaultdict(list)
    file_count = 0

    _log(f"Scanning: {root}")
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        # Remove skipped directories in-place (affects os.walk recursion)
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]

        for filename in filenames:
            filepath = Path(dirpath) / filename
            try:
                size = filepath.stat().st_size
            except (PermissionError, OSError) as e:
                _log(f"  [WARN] Cannot stat {filepath}: {e}", is_error=True)
                continue

            # Skip files below minimum size (empty files are always skipped)
            if size == 0 or size < min_size:
                continue

            size_groups[size].append(filepath)
            file_count += 1

    _log(f"Found {file_count} files")

    # Phase 2: For groups with same size, hash and group by hash
    # (size groups with only 1 file can't have duplicates — skip them)
    hash_groups: dict[str, list[Path]] = defaultdict(list)
    candidates = sum(len(v) for v in size_groups.values() if len(v) > 1)
    _log(f"Hashing {candidates} candidate files (same-size groups)...")

    hashed = 0
    for size, paths in size_groups.items():
        if len(paths) < 2:
            continue
        for filepath in paths:
            if cancel_event and cancel_event.is_set():
                _log("Scan cancelled.")
                return {}
            file_hash = get_file_hash(filepath, log_callback=log_callback)
            if file_hash:
                hash_groups[file_hash].append(filepath)
                hashed += 1
                if progress_callback:
                    progress_callback(hashed, candidates, f"Hashing {hashed}/{candidates}")

    # Phase 3: Keep only groups with 2+ files (actual duplicates)
    duplicates = {h: ps for h, ps in hash_groups.items() if len(ps) > 1}

    return duplicates


def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def print_report(duplicates: dict[str, list[Path]], root: Path) -> None:
    """Print a human-readable duplicate report."""
    if not duplicates:
        print("\n✅ No duplicate files found!")
        return

    total_groups = len(duplicates)
    total_dupes = sum(len(v) - 1 for v in duplicates.values())  # exclude original per group
    wasted = 0

    print(f"\n{'='*60}")
    print(f"DUPLICATE REPORT")
    print(f"{'='*60}")

    for i, (file_hash, paths) in enumerate(sorted(duplicates.items(), key=lambda x: x[1][0]), 1):
        try:
            size = paths[0].stat().st_size
        except OSError:
            size = 0
        wasted += size * (len(paths) - 1)

        print(f"\nGroup {i} ({format_size(size)} each, SHA-256: {file_hash[:16]}...):")
        for j, p in enumerate(sorted(paths), 1):
            rel = p.relative_to(root) if p.is_relative_to(root) else p
            marker = " <-- original" if j == 1 else ""
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            except OSError:
                mtime = "unknown"
            print(f"  {j}. {rel}  (modified: {mtime}){marker}")

    print(f"\n{'='*60}")
    print(f"Summary: {total_groups} duplicate group(s), {total_dupes} duplicate file(s)")
    print(f"Wasted space: {format_size(wasted)}")
    print(f"{'='*60}")


def json_report(duplicates: dict[str, list[Path]], root: Path) -> dict:
    """Generate a JSON-serializable report."""
    groups = []
    total_wasted = 0

    for file_hash, paths in sorted(duplicates.items(), key=lambda x: x[1][0]):
        try:
            size = paths[0].stat().st_size
        except OSError:
            size = 0
        total_wasted += size * (len(paths) - 1)

        files = []
        for p in sorted(paths):
            try:
                stat = p.stat()
                files.append({
                    "path": str(p.relative_to(root) if p.is_relative_to(root) else p),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            except OSError:
                files.append({"path": str(p), "size": 0, "modified": None})

        groups.append({"hash": file_hash, "size": size, "files": files})

    return {
        "root": str(root),
        "duplicate_groups": len(groups),
        "duplicate_files": sum(len(g["files"]) - 1 for g in groups),
        "wasted_bytes": total_wasted,
        "groups": groups,
    }


def move_duplicates(duplicates: dict[str, list[Path]], root: Path, staging: Path, log_callback=None) -> int:
    """
    Move duplicate files to a staging directory (keeps oldest file per group).

    Returns the number of files moved.
    """
    staging.mkdir(parents=True, exist_ok=True)
    moved = 0

    for file_hash, paths in duplicates.items():
        # Keep the oldest file, move the rest
        sorted_paths = sorted(paths, key=lambda p: p.stat().st_mtime)
        dupes = sorted_paths[1:]

        for dupe in dupes:
            # Preserve directory structure in staging
            rel = dupe.relative_to(root) if dupe.is_relative_to(root) else dupe.name
            dest = staging / rel
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Handle name collision in staging
            if dest.exists():
                stem = dest.stem
                suffix = dest.suffix
                counter = 1
                while dest.exists():
                    dest = dest.parent / f"{stem}_{counter}{suffix}"
                    counter += 1

            try:
                shutil.move(str(dupe), str(dest))
                msg = f"  Moved: {dupe.name} → {dest}"
                if log_callback:
                    log_callback(msg)
                else:
                    print(msg)
                moved += 1
            except (OSError, shutil.Error) as e:
                msg = f"  [ERROR] Failed to move {dupe}: {e}"
                if log_callback:
                    log_callback(msg)
                else:
                    print(msg, file=sys.stderr)

    return moved


def delete_duplicates(duplicates: dict[str, list[Path]], root: Path, log_callback=None) -> int:
    """
    Delete duplicate files (keeps oldest file per group).

    Returns the number of files deleted.
    """
    deleted = 0

    for file_hash, paths in duplicates.items():
        sorted_paths = sorted(paths, key=lambda p: p.stat().st_mtime)
        dupes = sorted_paths[1:]  # keep oldest

        for dupe in dupes:
            try:
                dupe.unlink()
                rel = dupe.relative_to(root) if dupe.is_relative_to(root) else dupe
                msg = f"  Deleted: {rel}"
                if log_callback:
                    log_callback(msg)
                else:
                    print(msg)
                deleted += 1
            except OSError as e:
                msg = f"  [ERROR] Failed to delete {dupe}: {e}"
                if log_callback:
                    log_callback(msg)
                else:
                    print(msg, file=sys.stderr)

    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect duplicate files in a folder (recursively).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python dedup.py ~/Downloads
  python dedup.py ~/Photos --json
  python dedup.py ~/Documents --delete
  python dedup.py ~/Documents --stage ~/dupes_staging
  python dedup.py . --skip node_modules,dist --min-size 1024
""",
    )
    parser.add_argument("path", type=Path, help="Directory to scan")
    parser.add_argument(
        "--json", action="store_true", help="Output report as JSON"
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete duplicates (keeps oldest file per group)",
    )
    parser.add_argument(
        "--stage",
        type=Path,
        metavar="DIR",
        help="Move duplicates to this staging directory instead of deleting",
    )
    parser.add_argument(
        "--skip",
        type=str,
        default="",
        help="Comma-separated list of directory names to skip (added to defaults)",
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symbolic links when scanning",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=0,
        help="Minimum file size in bytes to consider (default: 0)",
    )
    parser.add_argument(
        "--no-default-skip",
        action="store_true",
        help="Don't use the default skip list (.git, node_modules, etc.)",
    )

    args = parser.parse_args()

    # Validate path
    if not args.path.is_dir():
        print(f"Error: '{args.path}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Build skip dirs set
    if args.no_default_skip:
        skip_dirs = set()
    else:
        skip_dirs = set(DEFAULT_SKIP_DIRS)
    if args.skip:
        skip_dirs.update(s.strip() for s in args.skip.split(",") if s.strip())

    # Scan
    duplicates = scan_directory(
        root=args.path,
        skip_dirs=skip_dirs,
        follow_symlinks=args.follow_symlinks,
        min_size=args.min_size,
    )

    # Report
    if args.json:
        report = json_report(duplicates, args.path)
        print(json.dumps(report, indent=2))
    else:
        print_report(duplicates, args.path)

    # Validate mutually exclusive actions
    if args.delete and args.stage:
        print("Error: --delete and --stage are mutually exclusive. Pick one.", file=sys.stderr)
        sys.exit(1)

    # Action
    if duplicates:
        if args.stage:
            print(f"\n📦 Moving duplicates to staging: {args.stage}")
            count = move_duplicates(duplicates, args.path, args.stage)
            print(f"Moved {count} file(s) to staging.")
        elif args.delete:
            total_dupes = sum(len(v) - 1 for v in duplicates.values())
            print(f"\n⚠️  About to delete {total_dupes} duplicate file(s) (keeping oldest per group).")
            confirm = input("Are you sure? [y/N] ").strip().lower()
            if confirm != "y":
                print("Cancelled.")
                return
            count = delete_duplicates(duplicates, args.path)
            print(f"Deleted {count} duplicate file(s).")


if __name__ == "__main__":
    main()
