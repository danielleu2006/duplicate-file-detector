# Duplicate File Detector — User Manual

> **Version:** 1.1 · **Date:** April 2026 · **Author:** Daniel  
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
- **Settings persistence** — Remembers paths, options, **view mode**, and window size (`~/.dedup/settings.json`)
- **Core scan** — Standard library only (`dedup.py` + CLI)
- **GUI previews (optional)** — **Pillow** for images; **ffmpeg** on `PATH` for video first-frame thumbnails

---

## 2. Installation

### Prerequisites

| Requirement | Purpose | Required For |
|-------------|---------|--------------|
| **Python 3.10+** | Runtime | All features |
| **Tkinter** | GUI interface | GUI (included with Python on most systems) |
| **Pillow** | `pip install Pillow` | GUI image thumbnails (Thumbnails / Grid / List + preview) |
| **ffmpeg** | Install separately; add to `PATH` | GUI video first-frame thumbnails |

### Step-by-step

```bash
# 1. Navigate to the application directory
cd duplicate_file_detector

# 2. Core: no pip required for scanning / CLI.
#    Optional — for GUI image & video previews:
pip install Pillow
# Install ffmpeg from https://ffmpeg.org/download.html (Windows: winget install ffmpeg, etc.)
```

Without Pillow or ffmpeg, the GUI still works; non-image/video files (or missing tools) show a small placeholder tile with the file extension.

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
3. Review duplicate groups (switch **View** if you want thumbnails — see [§4](#4-gui-guide))
4. Click **Select All Duplicates** (leaves the **keeper** per group — see [§7](#7-duplicate-handling))
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
│  🔍  Duplicate File Detector                                 │
├──────────────────────────────────────────────────────────────┤
│  📁  Scan Settings                                           │
│  ├─ Scan Folder / Staging Dir / Min size / symlinks / skips  │
├──────────────────────────────────────────────────────────────┤
│  📋  Duplicate Results                                       │
│  View: [ List ▼ ]  (List | Thumbnails | Grid | List + preview) │
│  ┌────┬───────┬─────────────┬──────┬─────────┬──────────────┐ │
│  │ ✓  │ Group │ File Path   │ Size │ Modified │ Note       │ │
│  │ ☐  │ 1 ◄   │ a.jpg       │ …    │ …       │            │ │
│  │ ☑  │ 1     │ a (1).jpg   │ …    │ …       │ copy-style │ │
│  └────┴───────┴─────────────┴──────┴─────────┴──────────────┘ │
│  … or thumbnail / grid tiles with Original vs Duplicate …    │
├──────────────────────────────────────────────────────────────┤
│  Progress   [🔍 Scan] [✖ Cancel] [🗑️ Delete] [📦 Move] …     │
└──────────────────────────────────────────────────────────────┘
```

### View modes

| Mode | What you see |
|------|----------------|
| **List** | Table: ✓, Group, path, size, modified, **Note** |
| **Thumbnails** | Scrollable groups; each file is a tile (image or video first frame when Pillow/ffmpeg available) |
| **Grid** | Same tiles as Thumbnails, arranged in a **multi-column grid** per group (large results render in batches with **Load more**) |
| **List + preview** | List on top; **Visual compare** strip below shows thumbnails for the **selected tree row’s group** |
| **Smooth Scroll** (toggle) | ON = unit scrolling (slower/precise); OFF = fast multi-unit scrolling |

Hints under **View** remind you to install **Pillow** and/or add **ffmpeg** to `PATH` when missing.

### Scan Settings

| Control | Default | Description |
|---------|---------|-------------|
| **Scan Folder** | (empty) | Directory to scan. Click **Browse…** to select. |
| **Staging Dir** | (empty) | Directory for moved files. Click **Browse…** to select. Only needed for the **Move to Staging** action. |
| **Min Size (bytes)** | `0` | Minimum file size to consider. Files smaller than this are skipped. Set to `1024` to ignore files under 1 KB. |
| **Follow Symlinks** | Off | Follow symbolic links when scanning. **Caution:** may cause infinite loops if symlinks form cycles. |
| **Disable Default Skips** | Off | Don't skip the default directories (`.git`, `node_modules`, etc.). Useful if you want to scan everything. |
| **Extra Skip Dirs** | (empty) | Comma-separated list of additional directory names to skip. Added to the default list. |

### Results Tree (List view)

| Column | Description |
|--------|-------------|
| **✓** | Checkbox — click the ✓ column to toggle selection for delete/move |
| **Group** | Group number. **`◄`** marks the **keeper** (preferred file to keep when using **Select All Duplicates**). |
| **File Path** | Relative path from the scan root |
| **Size** | Human-readable file size (e.g., `1.2 MB`) |
| **Modified** | Last modification date (`YYYY-MM-DD HH:MM`) |
| **Note** | Short hint: e.g. `copy-style name`, `longer name`, `copy-style (keeper)` |

### Understanding Groups

Each group lists files with the **same SHA-256 hash** (identical bytes).

- **`◄`** = **keeper** — the file the tool prefers to retain (see [§7 Duplicate Handling](#7-duplicate-handling)).
- Other rows are **duplicates** relative to that keeper.
- **Select All Duplicates** checks every duplicate row and leaves the keeper unchecked (unless you change checkboxes manually).

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

- Check every **duplicate** row (not the keeper marked **◄**)
- Uncheck each **keeper**

This matches the CLI’s default keeper rules ([§7](#7-duplicate-handling)).

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
| `--delete` | off | Delete duplicates (keeps **keeper** per group — see §7). Prompts for confirmation. |
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

# Move duplicates to a staging folder (keeps keeper per group — §7)
python dedup.py ~/Downloads --stage ./staging

# Delete duplicates outright (keeps keeper per group; confirms first)
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
  1. docs/a.txt  (modified: 2025-07-15 09:30) <-- original (keeper)
  2. docs/sub/b.txt  (modified: 2025-07-15 10:15) <-- duplicate
  3. docs/sub2/c.txt  (modified: 2025-07-15 11:00) <-- duplicate

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
          "modified": "2025-07-15T09:30:00",
          "copy_style_name": false
        },
        {
          "path": "docs/sub/b.txt",
          "size": 12,
          "modified": "2025-07-15T10:15:00",
          "copy_style_name": false
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

### Which file is kept (the “keeper”)?

For each group of byte-identical files, exactly one **keeper** is chosen. The rest are candidates for delete/stage. Order of preference:

1. **Non–copy-style stem** — does **not** end with `(digits)` or `-digits` before the extension (e.g. prefer `report.pdf` over `report (1).pdf` or `photo-2.jpg`).
2. **Shorter basename** — smaller `len(path.name)` (longer names are treated as duplicates first when this rule applies).
3. **Older modification time** — if still tied on length and copy-style class.
4. **Lexicographic `path.name`** — final stable tie-break.

The CLI text report labels the keeper line with `<-- original (keeper)` and may label duplicates with reasons such as `(copy-style name)` or `(longer name)`.

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

In the GUI:

1. Select files with checkboxes (✓ column), or **Select All Duplicates** to select every non-keeper in each group.
2. **Delete Selected** / **Move to Staging** operate only on checked paths (relative paths are tracked consistently in List and thumbnail views).
3. Confirm in the dialog when deleting.

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
- **Results view mode** (`list` / `thumbs` / `grid` / `split` — see View combobox)
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
- Resize the window — it's fully resizable with a typical minimum around **700×580** (may vary by theme).
- The app remembers window size between sessions.

### Thumbnails show gray boxes / no pictures or video frames

**Symptom:** Tiles show only the file extension, not a preview.

**Fix:**
- **Images:** `pip install Pillow` and restart the GUI.
- **Videos** (MP4, MOV, etc.): install **ffmpeg** and ensure it is on your system **PATH** (`ffmpeg -version` in a terminal). Restart the GUI after changing PATH.

### Video thumbnails are slow

**Explanation:** Each video runs **ffmpeg** once to extract the first frame on the UI thread. Large batches of videos can feel sluggish (see TODO.md for future async work).

### No duplicates found

**Symptom:** Scan completes with "No duplicate files found!" (after a full, non-cancelled scan)

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

### "Scan was cancelled" appears instead of results

**Symptom:** After clicking Cancel during a scan, the message "Scan was cancelled" appears.

**Explanation:** This is the correct behavior. When you cancel a scan, the tool shows "Scan was cancelled" instead of "No duplicate files found!" — which would be misleading since the scan didn't complete. To get full results, simply scan the folder again without cancelling.

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

- **Required:** Python standard library + **Tkinter** (GUI).
- **Optional (GUI previews):** **Pillow** (images), **ffmpeg** on `PATH` (video first frame).

### Key functions in `dedup.py`

| Function | Purpose |
|----------|---------|
| `stem_suggests_copy()` | True if stem looks like `… (1)` / `…-2` download-style names |
| `sort_paths_for_keep()` | Order paths so index `0` is the keeper for a duplicate group |
| `get_file_hash()` | SHA-256 hash of a file (64 KB buffer) |
| `scan_directory()` | Walk → size groups → hash → duplicate dict |
| `format_size()` | Human-readable byte sizes |
| `print_report()` / `json_report()` | Text / JSON output (`copy_style_name` per file in JSON) |
| `move_duplicates()` / `delete_duplicates()` | Stage or delete non-keepers |
| `main()` | CLI entry |

### Key functions in `dedup_gui.py`

| Function | Purpose |
|----------|---------|
| `_apply_results_mode()` | Show List vs Thumbnails vs Grid vs split preview layout |
| `_populate_tree()` | Fill tree + `_group_paths` / hashes |
| `_load_thumbnail_photo()` | PIL image or ffmpeg pipe → `PhotoImage` |
| `_collect_selected_paths()` | Resolve `_selected_rel_paths` to absolute `Path`s |
| `_on_scan()` / `_do_scan()` | Threaded scan with progress |
| `_select_all_dupes()` | Select every path that is not the keeper |
| `run_gui()` | Entry point |

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
│  Keeper:    copy-style → shorter name → mtime → name       │
│  Skips:     .git, node_modules, venv, __pycache__, etc.      │
│  Settings:  ~/.dedup/settings.json (+ view mode)           │
│  Previews:  Pillow (images), ffmpeg PATH (video) — optional │
└──────────────────────────────────────────────────────────────┘
```

---

_Core scanning: standard library. GUI previews: optional Pillow + ffmpeg._
