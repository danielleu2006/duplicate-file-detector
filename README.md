# Duplicate File Detector

A lightweight CLI + GUI tool to detect duplicate files in a folder (recursively). **Core scan logic uses only the Python standard library** (plus Tkinter for the GUI). **Optional** installs improve previews in the GUI.

## How It Works

Uses a **3-tier comparison strategy** for speed:

1. **Size check** — files with different sizes can't be duplicates (instant)
2. **SHA-256 hash** — same-size files get hashed to confirm duplicates
3. **Grouping** — files with identical hashes are grouped and reported

This means for a typical directory, 99%+ of comparisons are eliminated at the size step.

## Quick Start (GUI)

```bash
python dedup_gui.py
```

The GUI provides:

- Folder browser to select scan directory
- **View** modes: **List**, **Thumbnails**, **Grid**, **List + preview** (visual compare)
- Grid/Thumbnails large-result safety: chunked rendering + **Load more** footer
- Tree table with checkboxes, or thumbnail tiles with **Select** on duplicate files
- **Note** column (List mode): hints such as `copy-style name`, `longer name`
- Image previews (**Pillow**): `pip install Pillow`
- Video first-frame previews (**ffmpeg** on your `PATH`)
- “Select All Duplicates” (selects every file except the **keeper** per group — see [Duplicate Handling](#duplicate-handling))
- Progress bar during scanning/hashing
- Move to staging directory (preserves folder structure)
- Export results as JSON (`copy_style_name` per file in groups)
- Settings persistence (`~/.dedup/settings.json`, including view mode and window geometry)
- Cancel support for long scans

## CLI Usage

```bash
# Basic scan — reports duplicates found
python dedup.py /path/to/folder

# Output as JSON (useful for scripting)
python dedup.py /path/to/folder --json

# Move duplicates to a staging folder (keeps preferred keeper per group)
python dedup.py /path/to/folder --stage ./staging

# Delete duplicates outright (keeps preferred keeper per group)
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

When using `--delete` or `--stage`, the tool picks one **keeper** per group and removes or moves the rest. The keeper is chosen in this order:

1. Prefer a filename **without** a copy-style suffix: stem ending in `(digits)` like `Report (1).pdf`, or ending in `-digits` before the extension like `image-2.jpg`.
2. Among remaining ties, prefer the **shorter basename** (`path.name`) — longer filenames are treated as duplicates first.
3. If still tied (same length), keep the **oldest** file by modification time.
4. Final tie-break: lexicographic order on the filename.

## Documentation

| File | Description |
|------|-------------|
| `README.md` | Quick start guide (this file) |
| `USER_MANUAL.md` | Full manual — GUI, CLI, previews, troubleshooting |
| `PROJECT_NOTES.md` | Technical notes (Chinese) — decisions, architecture |
| `TODO.md` | Task tracker |

## Source Files

| File | Description |
|------|-------------|
| `dedup.py` | Core scan engine + CLI (`sort_paths_for_keep`, reports, delete/stage) |
| `dedup_gui.py` | Tkinter GUI (views, thumbnails, threading) |
| `settings.py` | JSON settings persistence |

## Requirements

- **Python 3.10+** (`set[str]` hints, `Path.is_relative_to()`)
- **Tkinter** (included with most Python installs — GUI only)

**Optional (GUI previews):**

| Package / tool | Purpose |
|----------------|---------|
| **Pillow** (`pip install Pillow`) | Image thumbnails in Thumbnails / Grid / List + preview |
| **ffmpeg** (on `PATH`) | First-frame preview for common video extensions |

The CLI and duplicate detection **do not** require Pillow or ffmpeg.
