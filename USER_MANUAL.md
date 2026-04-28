# Duplicate File Detector — User Manual

> **Version:** 1.0 · **Date:** July 2025 · **Author:** Daniel
> Cross-platform tool for detecting duplicate files. Runs on **Windows**, **macOS**, and **Linux**.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Installation](#2-installation)
3. [Quick Start](#3-quick-start)
4. [GUI Guide](#4-gui-guide)
5. [CLI Reference](#5-cli-reference)
6. [How It Works](#6-how-it-works)
7. [Duplicate Handling](#7-duplicate-handling)
8. [Settings Persistence](#8-settings-persistence)
9. [Default Skip Directories](#9-default-skip-directories)
10. [Troubleshooting](#10-troubleshooting)
11. [Architecture & File Layout](#11-architecture--file-layout)

---

## 1. Overview

**Duplicate File Detector** scans a folder (recursively) and finds duplicate files using a fast 3-tier comparison strategy. It provides both a **GUI** (Tkinter) and a **CLI** interface.

### What it does

```
Your Folder
      │
      ▼
┌─────────────┐
│  1. Walk     │  Recursively collect all files (skip .git, node_modules, etc.)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  2. Size     │  Group files by size — different sizes can't be duplicates
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  3. Hash     │  For same-size groups, compute SHA-256 hashes
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  4. Report   │  Group files by hash — 2+ files with same hash = duplicates
└─────────────┘
```

### Key features

- **Free & offline** — No cloud APIs, no network required
- **Fast 3-tier strategy** — Size check eliminates 99%+ of comparisons before hashing
- **SHA-256 hashing** — Cryptographic-grade duplicate detection (virtually zero false positives)
- **GUI + CLI** — Use the GUI for interactive work, CLI for scripting and automation
- **Smart skip list** — Automatically skips `.git`, `node_modules`, `venv`, and 13 other common directories
- **Delete or stage** — Permanently delete duplicates, or move them to a staging folder (preserving directory structure)
- **JSON export** — Export results as structured JSON for scripting
- **Cancel support** — Cancel long scans at any time (GUI)
- **Settings persistence** — Remembers your paths, options, and window size between sessions
- **Pure Python** — No external dependencies beyond the standard library (+ Tkinter for GUI)

---

## 2. Installation

### Prerequisites

| Requirement | Purpose | Required For |
|-------------|---------|--------------|
| **Python 3.10+** | Runtime | All features |
| **Tkinter** | GUI interface | GUI only (included with Python on most systems) |

### Step-by-step

```bash
# 1. Navigate to the application directory
cd duplicate_file_detector

# 2. No pip install needed — no external dependencies!
#    Just run it directly.
```

#### Installing Tkinter (if missing on Linux)

On most systems, Tkinter comes pre-installed with Python. If it's missing:

```bash
# Ubuntu / Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

> **Windows and macOS:** Tkinter is always included with the standard Python installer — no extra steps needed.

---

## 3. Quick Start

### GUI (recommended for interactive use)

```bash
python dedup_gui.py
```

1. Click **Browse…** next to **Scan Folder** and pick a directory
2. Click **🔍 Scan**
3. Review duplicate groups in the results tree
4. Click **Select All Duplicates** (keeps the oldest file per group)
5. Click **🗑️ Delete Selected** or **📦 Move to Staging**

### CLI (for scripting and automation)

```bash
# Basic scan — prints a report to the console
python dedup.py ~/Downloads

# Output as JSON (pipe to jq, save to file, etc.)
python dedup.py ~/Downloads --json

# Delete duplicates (with confirmation prompt)
python dedup.py ~/Downloads --delete

# Move duplicates to a staging folder instead of deleting
python dedup.py ~/Downloads --stage ./dupes_staging

# Export JSON report to a file
python dedup.py ~/Downloads --json > report.json
```

---

## 4. GUI Guide

### Launching

```bash
python dedup_gui.py
```

The main window opens with your saved settings restored from the last session.

### Interface Layout

```
┌──────────────────────────────────────────────────────────────┐
│  🔍  Duplicate File Detector                                 │  ← Title
├──────────────────────────────────────────────────────────────┤
│  📁  Scan Settings                                           │
│  ├─ Scan Folder:     [path]        [Browse…]                 │
│  ├─ Staging Dir:     [path]        [Browse…]  (for Move)    │
│  ├─ Min Size (bytes): [0]  ▲▼  ☐ Follow Symlinks           │
│  │                          ☐ Disable Default Skips          │
│  └─ Extra Skip Dirs:  [comma-separated]                     │
├──────────────────────────────────────────────────────────────┤
│  📋  Duplicate Results                                       │
│  ┌────┬───────┬──────────────────┬────────┬──────────┐      │
│  │ ✓  │ Group │ File Path        │ Size   │ Modified │      │
│  ├────┼───────┼──────────────────┼────────┼──────────┤      │
│  │ ☐  │ 1 ◄   │ docs/a.txt      │ 12 B   │ 2025-07  │      │
│  │ ☑  │ 1     │ docs/sub/b.txt  │ 12 B   │ 2025-07  │      │
│  │ ☑  │ 1     │ docs/sub2/c.txt │ 12 B   │ 2025-07  │      │
│  └────┴───────┴──────────────────┴────────┴──────────┘      │
│  1 duplicate group(s)  •  2 duplicate file(s)  •  Wasted…   │
│  [Select All Duplicates]  [Deselect All]                     │
├──────────────────────────────────────────────────────────────┤
│  ████████████████████████░░░░░░░░░░  3/7                    │  ← Progress
├──────────────────────────────────────────────────────────────┤
│  [🔍 Scan] [✖ Cancel] [🗑️ Delete] [📦 Move] [💾 Export]    │
│  [↺ Clear]                        Status: Scanning…         │
└──────────────────────────────────────────────────────────────┘
```

### Scan Settings

| Control | Default | Description |
|---------|---------|-------------|
| **Scan Folder** | (empty) | Directory to scan. Click **Browse…** to select. |
| **Staging Dir** | (empty) | Directory for moved files. Click **Browse…** to select. Only needed for the **Move to Staging** action. |
| **Min Size (bytes)** | `0` | Minimum file size to consider. Files smaller than this are skipped. Set to `1024` to ignore files under 1 KB. |
| **Follow Symlinks** | Off | Follow symbolic links when scanning. **Caution:** may cause infinite loops if symlinks form cycles. |
| **Disable Default Skips** | Off | Don't skip the default directories (`.git`, `node_modules`, etc.). Useful if you want to scan everything. |
| **Extra Skip Dirs** | (empty) | Comma-separated list of additional directory names to skip. Added to the default list. |

### Results Tree

The results tree shows all files in duplicate groups:

| Column | Description |
|--------|-------------|
| **✓** | Checkbox — click to select/deselect for delete/move actions |
| **Group** | Group number. `◄` marks the **original** file (oldest by modification time). |
| **File Path** | Relative path from the scan root |
| **Size** | Human-readable file size (e.g., `1.2 MB`) |
| **Modified** | Last modification date (`YYYY-MM-DD HH:MM`) |

### Understanding Groups

Each duplicate group contains files with **identical SHA-256 hashes** (and therefore identical content). Within each group:

- The **◄** marker shows the **original** file — the one with the oldest modification time
- All other files in the group are **duplicates**
- When you delete or move duplicates, the original is always kept

### Action Buttons

| Button | Function |
|--------|----------|
| **🔍 Scan** | Start scanning the selected folder |
| **✖ Cancel** | Cancel the current scan or action |
| **🗑️ Delete Selected** | Permanently delete all selected (checked) files. Prompts for confirmation. |
| **📦 Move to Staging** | Move selected files to the staging directory, preserving their folder structure. |
| **💾 Export JSON** | Export the current results as a JSON file. Prompts for save location. |
| **↺ Clear Results** | Clear the results tree and reset the display. |

### Select All Duplicates

Click **Select All Duplicates** to automatically:
- ✅ Check all **duplicate** files (not the original)
- ☐ Uncheck all **original** files (marked with ◄)

This is the fastest way to select files for deletion — it keeps the oldest file in each group and selects everything else.

### Delete vs Move to Staging

| Action | What happens | Recoverable? |
|--------|-------------|--------------|
| **Delete** | Files are permanently deleted (`unlink`) | ❌ No — files are permanently deleted, not moved to the recycle bin |
| **Move to Staging** | Files are moved to the staging directory, preserving their original folder structure | ✅ Yes — files are moved, not deleted. You can browse the staging folder and recover files manually. |

> **Tip:** If you're unsure, use **Move to Staging** first. Review the staged files, then delete them from the staging folder when you're confident.

### Progress Bar

During scanning, the progress bar shows hashing progress:

- `3/7` means 3 of 7 candidate files (same-size) have been hashed
- Files that have unique sizes are skipped instantly (no hashing needed)
- The bar fills as hashing progresses

### After Delete / Move

After deleting or moving files, the tool asks:

> **"Re-scan the folder to refresh results?"**

- **Yes** — Automatically re-scans the folder to show updated results (remaining duplicates). If no duplicates remain, the results tree is cleared.
- **No** — Clears the results tree

### Cross-folder duplicate detection

The tool detects duplicates **across all subfolders** within the scan root. For example, if you scan `C:\Users\Documents` and identical files exist in `Documents\FolderA\photo.jpg` and `Documents\FolderB\photo.jpg`, they will be reported as duplicates.

> **Note:** You can only scan one root folder at a time. To find duplicates across two completely separate folder trees (e.g., `C:\Photos` and `D:\Photos`), scan a common parent directory. Multi-path scanning is planned for a future release (see TODO.md).

---

## 5. CLI Reference

### Basic usage

```
python dedup.py <path> [OPTIONS]
```

### All options

| Flag | Default | Description |
|------|---------|-------------|
| `path` | (required) | Directory to scan |
| `--json` | off | Output report as JSON instead of text |
| `--delete` | off | Delete duplicates (keeps oldest file per group). Prompts for confirmation. |
| `--stage DIR` | — | Move duplicates to this staging directory instead of deleting |
| `--skip DIRS` | `""` | Comma-separated list of directory names to skip (added to defaults) |
| `--follow-symlinks` | off | Follow symbolic links when scanning |
| `--min-size BYTES` | `0` | Minimum file size in bytes to consider |
| `--no-default-skip` | off | Don't use the default skip list (`.git`, `node_modules`, etc.) |

### Examples

```bash
# Basic scan — reports duplicates found
python dedup.py ~/Downloads

# Output as JSON (useful for scripting)
python dedup.py ~/Downloads --json

# Move duplicates to a staging folder (keeps oldest file per group)
python dedup.py ~/Downloads --stage ./staging

# Delete duplicates outright (keeps oldest file per group, with confirmation)
python dedup.py ~/Downloads --delete

# Ignore files smaller than 1KB
python dedup.py ~/Downloads --min-size 1024

# Add extra directories to skip
python dedup.py ~/Downloads --skip my_private_dir,temp

# Follow symbolic links
python dedup.py ~/Downloads --follow-symlinks

# Disable default skip list (scan everything)
python dedup.py ~/Downloads --no-default-skip

# Scan current directory
python dedup.py .

# Combine options: scan with min size, extra skips, and JSON output
python dedup.py ~/Photos --min-size 10240 --skip .thumbnails,.preview --json

# Export JSON report to a file
python dedup.py ~/Downloads --json > duplicate_report.json
```

### Text report format

```
============================================================
DUPLICATE REPORT
============================================================

Group 1 (12.0 B each, SHA-256: a1b2c3d4e5f67890...):
  1. docs/a.txt  (modified: 2025-07-15 09:30) <-- original
  2. docs/sub/b.txt  (modified: 2025-07-15 10:15)
  3. docs/sub2/c.txt  (modified: 2025-07-15 11:00)

============================================================
Summary: 1 duplicate group(s), 2 duplicate file(s)
Wasted space: 24.0 B
============================================================
```

### JSON report format

```json
{
  "root": "/home/daniel/Downloads",
  "duplicate_groups": 1,
  "duplicate_files": 2,
  "wasted_bytes": 24,
  "groups": [
    {
      "hash": "a1b2c3d4e5f67890...",
      "size": 12,
      "files": [
        {
          "path": "docs/a.txt",
          "size": 12,
          "modified": "2025-07-15T09:30:00"
        },
        {
          "path": "docs/sub/b.txt",
          "size": 12,
          "modified": "2025-07-15T10:15:00"
        }
      ]
    }
  ]
}
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success (duplicates may or may not have been found) |
| `1` | Error (invalid path, mutually exclusive flags, etc.) |

### Mutual exclusivity

`--delete` and `--stage` are mutually exclusive. Using both together produces an error:

```
Error: --delete and --stage are mutually exclusive. Pick one.
```

---

## 6. How It Works

### 3-Tier Comparison Strategy

The tool uses a 3-tier strategy that makes it extremely fast in practice:

#### Tier 1: Size Check (instant, no I/O)

Files with different sizes **cannot** be duplicates. This step groups all files by size and instantly eliminates all size-unique files from consideration.

**Typical result:** For a folder with 10,000 files, only 500–2,000 may share a size with another file. The remaining 8,000–9,500 are eliminated instantly.

#### Tier 2: SHA-256 Hash (reads file content)

For each group of same-size files, the tool computes a SHA-256 hash. Files with different hashes are not duplicates.

SHA-256 is a cryptographic hash — the probability of two different files having the same hash is effectively zero (≈ 1 in 2^256). This means **hash matches are definitive**; no further verification is needed.

#### Tier 3: Grouping (no I/O)

Files with identical hashes are grouped together. Any group with 2+ files is reported as a duplicate set.

### Performance characteristics

| Phase | Work done | Typical proportion of total time |
|-------|-----------|--------------------------------|
| Size check | Stat each file | < 1% |
| Hashing | Read + hash candidate files | > 99% |
| Grouping | Sort hash groups | < 0.1% |

The hashing phase is the only I/O-intensive step. Its speed depends on:
- **Number of same-size candidates** — determined by Tier 1
- **Size of candidate files** — larger files take longer to hash
- **Disk speed** — SSD is much faster than HDD

### Empty files

Empty (0-byte) files are always skipped. Multiple empty files are technically duplicates of each other, but they contain no useful content and reporting them would be noisy.

---

## 7. Duplicate Handling

### Which file is kept?

When deleting or moving duplicates, the tool keeps the **oldest file** in each group (by modification time) and removes/moves the rest.

**Rationale:** The oldest file is most likely the original. Later copies are likely duplicates.

### Delete action

```bash
# CLI
python dedup.py ~/Downloads --delete
```

- Prompts for confirmation before deleting: `Are you sure? [y/N]`
- Permanently deletes selected files using `unlink()`
- Shows count of deleted files

### Move to Staging action

```bash
# CLI
python dedup.py ~/Downloads --stage ./staging
```

- Moves selected files to the staging directory
- **Preserves folder structure** — a file at `Photos/2024/beach.jpg` is moved to `staging/Photos/2024/beach.jpg`
- Handles name collisions in the staging folder (appends `_1`, `_2`, etc.)
- Shows count of moved files

### GUI delete/move

In the GUI, you have fine-grained control:
1. **Select which files** to delete/move using checkboxes
2. Use **Select All Duplicates** to auto-select all non-original files
3. Or manually select specific files within groups
4. Click **🗑️ Delete Selected** or **📦 Move to Staging**
5. Confirm the action in the dialog

---

## 8. Settings Persistence

All GUI settings are saved automatically when you close the window and restored when you launch the app again.

### What is saved

- Scan folder path
- Staging directory path
- Minimum file size
- Follow symlinks option
- Disable default skips option
- Extra skip directories
- Window position and size

### Where settings are stored

| Platform | Path |
|----------|------|
| **All platforms** | `~/.dedup/settings.json` |

> Settings are stored in the user's home directory under `.dedup/`. If the settings file is corrupted, the app silently falls back to defaults.

### CLI settings

The CLI does **not** use the settings file. All options are specified via command-line flags. This is by design — the CLI is stateless and suitable for scripting.

---

## 9. Default Skip Directories

The following directories are automatically skipped during scanning:

| Directory | Why it's skipped |
|-----------|-----------------|
| `.git` | Git repository data — never user files |
| `__pycache__` | Python bytecode cache |
| `node_modules` | NPM packages — huge, full of duplicates by design |
| `.venv`, `venv`, `venv.bak` | Python virtual environments |
| `.idea`, `.vscode` | IDE configuration |
| `.cache` | General cache directory |
| `.tox` | Python tox environments |
| `.mypy_cache`, `.pytest_cache` | Python tool caches |
| `dist`, `build` | Build output directories |
| `.next` | Next.js build cache |

### Customizing the skip list

- **Add directories** — Use `--skip` (CLI) or **Extra Skip Dirs** (GUI) to add more names
- **Disable defaults** — Use `--no-default-skip` (CLI) or check **Disable Default Skips** (GUI) to scan everything
- **Combine** — You can disable defaults AND add your own skips at the same time

```bash
# Disable defaults and add your own skips
python dedup.py ~/Downloads --no-default-skip --skip .git,node_modules,.venv
```

---

## 10. Troubleshooting

### "Not a directory"

**Symptom:** Error message when running the CLI.

**Fix:** Make sure the path you provide is a directory, not a file:

```bash
# ❌ Wrong
python dedup.py ~/file.txt

# ✅ Correct
python dedup.py ~/folder
```

### Scan is slow on large directories

**Symptom:** Hashing takes a long time.

**Tips:**
- Use `--min-size` to skip small files: `python dedup.py . --min-size 1024`
- Add extra skip directories: `python dedup.py . --skip .thumbnails,.preview`
- The hashing phase is I/O-bound — SSD is much faster than HDD
- Large files (videos, archives) take longer to hash — this is expected

### "Permission denied" warnings during scan

**Symptom:** `[WARN] Cannot stat` or `[WARN] Cannot read` messages.

**Fix:**
- These are normal — some files/directories require elevated permissions
- The tool skips inaccessible files and continues scanning
- To scan system directories, run as Administrator (Windows) or with `sudo` (Linux/macOS)

### GUI doesn't open / "No module named _tkinter"

**Symptom:** `ImportError: No module named '_tkinter'` on Linux.

**Fix:**
```bash
# Ubuntu / Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

### GUI is too small / controls are cut off

**Symptom:** Not all settings are visible.

**Fix:**
- Resize the window — it's fully resizable with a minimum of 700×580
- The app remembers window size between sessions

### No duplicates found

**Symptom:** Scan completes with "No duplicate files found!"

**Possible causes:**
- The folder genuinely has no duplicates (this is good!)
- Too many directories are being skipped — try `--no-default-skip`
- Small files are being skipped — lower `--min-size` or set it to `0`

### Settings not persisting

**Symptom:** Settings revert to defaults on next GUI launch.

**Fix:**
- Make sure you close the window normally (X button) — settings are saved on close
- Check that `~/.dedup/` is writable
- If the JSON file is corrupted, delete `~/.dedup/settings.json` and the app will use defaults

### Cancel doesn't stop immediately

**Symptom:** Clicking Cancel takes a few seconds to take effect.

**Explanation:** The cancel event is checked between file hashes. If a large file is currently being hashed, the cancel takes effect after that file's hash completes. This is by design — canceling mid-hash could leave data in an inconsistent state.

---

## 11. Architecture & File Layout

```
duplicate_file_detector/
├── dedup.py            Core scan engine + CLI interface
├── dedup_gui.py        Tkinter GUI
├── settings.py         JSON settings persistence
├── README.md           Quick start guide
├── USER_MANUAL.md      This file — comprehensive manual
├── PROJECT_NOTES.md    Technical project notes (Chinese)
└── TODO.md             Future plans & completed items
```

### Dependencies

None beyond the Python standard library and Tkinter.

### Key functions in `dedup.py`

| Function | Purpose |
|----------|---------|
| `get_file_hash()` | Compute SHA-256 hash of a file (64KB buffer) |
| `scan_directory()` | 3-tier scan: walk → size groups → hash groups → duplicates |
| `format_size()` | Convert bytes to human-readable size (B, KB, MB, GB, TB) |
| `print_report()` | Print human-readable duplicate report to stdout |
| `json_report()` | Generate JSON-serializable report dict |
| `move_duplicates()` | Move duplicate files to staging directory |
| `delete_duplicates()` | Permanently delete duplicate files |
| `main()` | CLI entry point (argparse) |

### Key functions in `dedup_gui.py`

| Function | Purpose |
|----------|---------|
| `DedupGUI.__init__()` | Initialize GUI, load settings, build UI |
| `DedupGUI._on_scan()` | Start scan in a worker thread |
| `DedupGUI._do_scan()` | Worker thread: run scan with progress callbacks |
| `DedupGUI._populate_tree()` | Fill treeview with duplicate groups |
| `DedupGUI._on_delete()` | Delete selected files with confirmation |
| `DedupGUI._on_stage()` | Move selected files to staging |
| `DedupGUI._on_export()` | Export results as JSON |
| `DedupGUI._select_all_dupes()` | Auto-select all non-original duplicates |
| `run_gui()` | Entry point — create Tk root and run mainloop |

### Thread safety

The GUI uses worker threads for scan, delete, and move operations to keep the UI responsive. Thread safety is maintained by:

1. **Capturing Tkinter variables on the main thread** before spawning workers
2. **Using `root.after()`** to schedule UI updates from worker threads
3. **Never reading Tk variables from worker threads**

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────┐
│  DUPLICATE FILE DETECTOR — Quick Reference                   │
├──────────────────────────────────────────────────────────────┤
│  GUI:   python dedup_gui.py                                  │
│  CLI:   python dedup.py <path>                               │
│  Help:  python dedup.py --help                               │
├──────────────────────────────────────────────────────────────┤
│  CLI Flags:                                                  │
│    --json              Output as JSON                         │
│    --delete            Delete duplicates (with confirm)       │
│    --stage DIR         Move duplicates to staging folder      │
│    --min-size N        Skip files smaller than N bytes       │
│    --skip D1,D2        Add directories to skip list          │
│    --follow-symlinks   Follow symbolic links                 │
│    --no-default-skip   Scan all directories (incl. .git)     │
├──────────────────────────────────────────────────────────────┤
│  Strategy:  Size → SHA-256 → Group                           │
│  Keeps:     Oldest file per group (by modification time)     │
│  Skips:     .git, node_modules, venv, __pycache__, etc.     │
│  Settings:  ~/.dedup/settings.json                           │
└──────────────────────────────────────────────────────────────┘
```

---

_Duplicate File Detector — Pure Python, no external dependencies_
