# Duplicate File Detector

A lightweight CLI + GUI tool to detect duplicate files in a folder (recursively). Pure Python, no external dependencies.

## How It Works

Uses a **3-tier comparison strategy** for speed:

1. **Size check** — files with different sizes can't be duplicates (instant, no I/O)
2. **SHA-256 hash** — same-size files get hashed to confirm duplicates
3. **Grouping** — files with identical hashes are grouped and reported

This means for a typical directory, 99%+ of comparisons are eliminated at the size step.

## Quick Start (GUI)

```bash
python dedup_gui.py
```

The GUI provides:
- Folder browser to select scan directory
- Treeview with checkboxes to select which duplicates to delete or move
- "Select All Duplicates" button (keeps the oldest file per group)
- Progress bar during scanning/hashing
- Move to staging directory (preserves folder structure)
- Export results as JSON
- Settings persistence (window position, paths, options)
- Cancel support for long scans

## CLI Usage

```bash
# Basic scan — reports duplicates found
python dedup.py /path/to/folder

# Output as JSON (useful for scripting)
python dedup.py /path/to/folder --json

# Move duplicates to a staging folder (keeps oldest file per group)
python dedup.py /path/to/folder --stage ./staging

# Delete duplicates outright (keeps oldest file per group)
python dedup.py /path/to/folder --delete

# Ignore files smaller than 1KB
python dedup.py /path/to/folder --min-size 1024

# Add extra directories to skip
python dedup.py /path/to/folder --skip my_private_dir,temp

# Follow symbolic links
python dedup.py /path/to/folder --follow-symlinks

# Disable default skip list (.git, node_modules, etc.)
python dedup.py /path/to/folder --no-default-skip
```

## Default Skip Directories

The following directories are automatically skipped:

`.git`, `__pycache__`, `node_modules`, `.venv`, `venv`, `venv.bak`, `.idea`, `.vscode`, `.cache`, `.tox`, `.mypy_cache`, `.pytest_cache`, `dist`, `build`, `.next`

Use `--no-default-skip` to disable, or `--skip` to add more.

## Duplicate Handling

When using `--delete` or `--stage`, the tool keeps the **oldest file** (by modification time) in each duplicate group and removes/moves the rest.

## Documentation

| File | Description |
|------|-------------|
| `README.md` | Quick start guide (this file) |
| `USER_MANUAL.md` | Comprehensive manual — GUI guide, CLI reference, troubleshooting, architecture |
| `PROJECT_NOTES.md` | Technical project notes (Chinese) — decisions, architecture, risks |
| `TODO.md` | Task tracker — current priorities, future plans, completed items |

## Source Files

| File | Description |
|------|-------------|
| `dedup.py` | Core scan engine + CLI interface |
| `dedup_gui.py` | Tkinter GUI |
| `settings.py` | JSON settings persistence |

## Requirements

- Python 3.10+ (uses `set[str]` type hints and `Path.is_relative_to()`)
- No external packages needed (Tkinter included with Python)
