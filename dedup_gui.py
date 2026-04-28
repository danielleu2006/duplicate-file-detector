#!/usr/bin/env python3
"""
dedup_gui.py — Tkinter GUI for Duplicate File Detector
=======================================================
Cross-platform GUI for detecting duplicate files in a folder.
Uses the scan engine from dedup.py with GUI-friendly callbacks.

Pattern follows Daniel's existing Tkinter apps:
  - text_to_wavsrt_gui.py
  - lyric_video_gui.py
"""

import os
import shutil
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional

import dedup
import settings

# ---------------------------------------------------------------------------
# Default skip dirs for display
# ---------------------------------------------------------------------------

SKIP_DIRS_DISPLAY = ", ".join(sorted(dedup.DEFAULT_SKIP_DIRS))


# ---------------------------------------------------------------------------
# Main GUI Application
# ---------------------------------------------------------------------------

class DedupGUI:
    """Main GUI application for Duplicate File Detector."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Duplicate File Detector")
        self.root.resizable(True, True)
        self.root.minsize(700, 580)

        # Worker thread state
        self._worker_thread: Optional[threading.Thread] = None
        self._scan_running = False
        self._cancel_event = threading.Event()

        # Scan results (populated after scan)
        self._duplicates: dict[str, list[Path]] = {}
        self._scan_root: Optional[Path] = None

        # Build UI
        self._apply_styles()
        self._build_ui()

        # Load saved settings
        self._load_settings()

        # Save settings on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _apply_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

        base_font = ("Segoe UI", 9)
        header_font = ("Segoe UI", 10, "bold")
        title_font = ("Segoe UI", 14, "bold")

        style.configure("Title.TLabel", font=title_font, foreground="#1a1a2e")
        style.configure("Header.TLabel", font=header_font, foreground="#16213e")
        style.configure("TLabelframe.Label", font=header_font, foreground="#0f3460")
        style.configure("TButton", font=base_font, padding=4)
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=8)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Main container with padding
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # ── Title ──
        ttk.Label(main, text="🔍  Duplicate File Detector", style="Title.TLabel").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 8)
        )

        # ── Top panel: settings (fixed, not scrollable) ──
        top_panel = ttk.Frame(main)
        top_panel.grid(row=1, column=0, sticky=tk.NSEW, pady=(0, 6))
        top_panel.columnconfigure(0, weight=1)
        top_panel.rowconfigure(0, weight=0)  # settings don't stretch
        top_panel.rowconfigure(1, weight=1)  # results stretch

        # ── Scan Settings group ──
        self._build_settings_group(top_panel)

        # ── Results group ──
        self._build_results_group(top_panel)

        # ── Buttons + Progress ──
        bottom = ttk.Frame(main, padding=(0, 4, 0, 0))
        bottom.grid(row=2, column=0, sticky=tk.EW)

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            bottom, orient=tk.HORIZONTAL, mode="determinate", maximum=1, value=0
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 6))

        # Button row
        btn_frame = ttk.Frame(bottom)
        btn_frame.pack(fill=tk.X)

        self.btn_scan = ttk.Button(
            btn_frame, text="🔍  Scan", style="Accent.TButton", command=self._on_scan
        )
        self.btn_scan.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_cancel = ttk.Button(
            btn_frame, text="✖  Cancel", command=self._on_cancel, state=tk.DISABLED
        )
        self.btn_cancel.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_delete = ttk.Button(
            btn_frame, text="🗑️  Delete Selected", style="Danger.TButton",
            command=self._on_delete, state=tk.DISABLED,
        )
        self.btn_delete.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_stage = ttk.Button(
            btn_frame, text="📦  Move to Staging", command=self._on_stage, state=tk.DISABLED
        )
        self.btn_stage.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_export = ttk.Button(
            btn_frame, text="💾  Export JSON", command=self._on_export, state=tk.DISABLED
        )
        self.btn_export.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_clear = ttk.Button(
            btn_frame, text="↺  Clear Results", command=self._on_clear_results, state=tk.DISABLED
        )
        self.btn_clear.pack(side=tk.LEFT, padx=(0, 6))

        self.status_var = tk.StringVar(value="Ready — choose a folder and scan")
        ttk.Label(btn_frame, textvariable=self.status_var, foreground="#555").pack(
            side=tk.RIGHT, padx=6
        )

    # ── Settings group ──

    def _build_settings_group(self, parent):
        frame = ttk.LabelFrame(parent, text="📁  Scan Settings", padding=8)
        frame.grid(row=0, column=0, sticky=tk.EW, pady=(0, 6), padx=2)
        frame.columnconfigure(1, weight=1)

        row = 0

        # Scan directory
        ttk.Label(frame, text="Scan Folder:").grid(row=row, column=0, sticky=tk.W, pady=3)
        dir_row = ttk.Frame(frame)
        dir_row.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=3)
        dir_row.columnconfigure(0, weight=1)

        self.scan_path_var = tk.StringVar()
        ttk.Entry(dir_row, textvariable=self.scan_path_var).grid(
            row=0, column=0, sticky=tk.EW
        )
        ttk.Button(dir_row, text="Browse…", command=self._browse_scan_dir, width=9).grid(
            row=0, column=1, padx=(4, 0)
        )
        row += 1

        # Staging directory
        ttk.Label(frame, text="Staging Dir:").grid(row=row, column=0, sticky=tk.W, pady=3)
        stage_row = ttk.Frame(frame)
        stage_row.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=3)
        stage_row.columnconfigure(0, weight=1)

        self.staging_path_var = tk.StringVar()
        ttk.Entry(stage_row, textvariable=self.staging_path_var).grid(
            row=0, column=0, sticky=tk.EW
        )
        ttk.Button(stage_row, text="Browse…", command=self._browse_staging_dir, width=9).grid(
            row=0, column=1, padx=(4, 0)
        )
        ttk.Label(stage_row, text="(for Move)", foreground="#888", font=("Segoe UI", 8)).grid(
            row=0, column=2, padx=4
        )
        row += 1

        # Min size + options row
        ttk.Label(frame, text="Min Size (bytes):").grid(row=row, column=0, sticky=tk.W, pady=3)
        opts_row = ttk.Frame(frame)
        opts_row.grid(row=row, column=1, sticky=tk.W, padx=4, pady=3)

        self.min_size_var = tk.IntVar(value=0)
        ttk.Spinbox(
            opts_row, from_=0, to=1000000000, increment=1024,
            textvariable=self.min_size_var, width=12,
        ).pack(side=tk.LEFT, padx=(0, 12))

        self.follow_symlinks_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opts_row, text="Follow Symlinks", variable=self.follow_symlinks_var
        ).pack(side=tk.LEFT, padx=(0, 12))

        self.no_default_skip_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            opts_row, text="Disable Default Skips", variable=self.no_default_skip_var
        ).pack(side=tk.LEFT, padx=(0, 12))
        row += 1

        # Extra skip dirs
        ttk.Label(frame, text="Extra Skip Dirs:").grid(row=row, column=0, sticky=tk.W, pady=3)
        skip_row = ttk.Frame(frame)
        skip_row.grid(row=row, column=1, sticky=tk.EW, padx=4, pady=3)
        skip_row.columnconfigure(0, weight=1)

        self.skip_dirs_var = tk.StringVar()
        ttk.Entry(skip_row, textvariable=self.skip_dirs_var).grid(
            row=0, column=0, sticky=tk.EW
        )
        ttk.Label(
            skip_row,
            text=f"(comma-separated; defaults: {SKIP_DIRS_DISPLAY})",
            foreground="#888", font=("Segoe UI", 8),
        ).grid(row=0, column=1, padx=4)

    # ── Results group ──

    def _build_results_group(self, parent):
        frame = ttk.LabelFrame(parent, text="📋  Duplicate Results", padding=8)
        frame.grid(row=1, column=0, sticky=tk.NSEW, pady=(0, 2), padx=2)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        # Treeview for duplicate groups
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=0, column=0, sticky=tk.NSEW)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        columns = ("select", "group", "path", "size", "modified")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="extended"
        )
        self.tree.heading("select", text="✓", command=self._toggle_select_all)
        self.tree.heading("group", text="Group")
        self.tree.heading("path", text="File Path")
        self.tree.heading("size", text="Size")
        self.tree.heading("modified", text="Modified")

        self.tree.column("select", width=40, minwidth=40, stretch=False)
        self.tree.column("group", width=60, minwidth=50, stretch=False)
        self.tree.column("path", width=400, minwidth=200)
        self.tree.column("size", width=90, minwidth=70, stretch=False)
        self.tree.column("modified", width=130, minwidth=100, stretch=False)

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)

        # Click to toggle checkbox
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

        # Summary label
        self.summary_var = tk.StringVar(value="No results yet")
        ttk.Label(
            frame, textvariable=self.summary_var,
            foreground="#555", font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky=tk.W, pady=(6, 0))

        # Select All / Deselect All buttons
        sel_row = ttk.Frame(frame)
        sel_row.grid(row=2, column=0, sticky=tk.W, pady=(4, 0))

        ttk.Button(sel_row, text="Select All Duplicates", command=self._select_all_dupes, width=20).pack(
            side=tk.LEFT, padx=(0, 6)
        )
        ttk.Button(sel_row, text="Deselect All", command=self._deselect_all, width=14).pack(
            side=tk.LEFT, padx=(0, 6)
        )

        # Track selected items for delete/stage operations
        self._selected_items: set[str] = set()

    # ------------------------------------------------------------------
    # File browse callbacks
    # ------------------------------------------------------------------

    def _browse_scan_dir(self):
        path = filedialog.askdirectory(title="Select Folder to Scan")
        if path:
            self.scan_path_var.set(path)

    def _browse_staging_dir(self):
        path = filedialog.askdirectory(title="Select Staging Directory")
        if path:
            self.staging_path_var.set(path)

    # ------------------------------------------------------------------
    # Tree / checkbox helpers
    # ------------------------------------------------------------------

    def _on_tree_click(self, event):
        """Toggle checkbox when clicking the 'select' column."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)
        if column != "#1":  # only the select column
            return
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        self._toggle_item(item_id)

    def _toggle_item(self, item_id):
        """Toggle the checkbox state for a tree item."""
        values = list(self.tree.item(item_id, "values"))
        if values[0] == "☑":
            values[0] = "☐"
            self._selected_items.discard(item_id)
        else:
            values[0] = "☑"
            self._selected_items.add(item_id)
        self.tree.item(item_id, values=values)
        self._update_action_buttons()

    def _toggle_select_all(self):
        """Toggle all items when clicking the header checkbox."""
        if not self.tree.get_children():
            return
        # If any are unchecked, check all; otherwise uncheck all
        all_selected = all(
            self.tree.item(item, "values")[0] == "☑"
            for item in self.tree.get_children()
        )
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            if all_selected:
                values[0] = "☐"
                self._selected_items.discard(item)
            else:
                values[0] = "☑"
                self._selected_items.add(item)
            self.tree.item(item, values=values)
        self._update_action_buttons()

    def _select_all_dupes(self):
        """Select all items that are duplicates (i.e., not the first/oldest in each group)."""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            # First item in each group is the original (marked with ◄ in group col)
            group_val = str(values[1]).strip()
            if "◄" not in group_val:
                values[0] = "☑"
                self._selected_items.add(item)
            else:
                values[0] = "☐"
                self._selected_items.discard(item)
            self.tree.item(item, values=values)
        self._update_action_buttons()

    def _deselect_all(self):
        """Deselect all items."""
        for item in self.tree.get_children():
            values = list(self.tree.item(item, "values"))
            values[0] = "☐"
            self._selected_items.discard(item)
            self.tree.item(item, values=values)
        self._update_action_buttons()

    def _update_action_buttons(self):
        """Enable/disable action buttons based on selection and results."""
        has_results = bool(self.tree.get_children())
        has_selection = bool(self._selected_items)
        self.btn_delete.configure(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.btn_stage.configure(state=tk.NORMAL if has_selection else tk.DISABLED)
        self.btn_export.configure(state=tk.NORMAL if has_results else tk.DISABLED)
        self.btn_clear.configure(state=tk.NORMAL if has_results else tk.DISABLED)

    # ------------------------------------------------------------------
    # Populate results tree
    # ------------------------------------------------------------------

    def _populate_tree(self, duplicates: dict[str, list[Path]], root: Path):
        """Fill the treeview with duplicate groups."""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._selected_items.clear()

        total_groups = len(duplicates)
        total_dupes = sum(len(v) - 1 for v in duplicates.values())
        wasted = 0

        for i, (file_hash, paths) in enumerate(
            sorted(duplicates.items(), key=lambda x: x[1][0]), 1
        ):
            try:
                size = paths[0].stat().st_size
            except OSError:
                size = 0
            wasted += size * (len(paths) - 1)

            # Sort by mtime (oldest first) — oldest is the "original"
            sorted_paths = sorted(paths, key=lambda p: p.stat().st_mtime if p.exists() else 0)

            for j, p in enumerate(sorted_paths):
                rel = p.relative_to(root) if p.is_relative_to(root) else p
                try:
                    mtime = p.stat().st_mtime
                    mod_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                    file_size = p.stat().st_size
                except OSError:
                    mod_str = "unknown"
                    file_size = 0

                group_label = f"{i} ◄" if j == 0 else str(i)
                checked = "☐"
                self.tree.insert("", tk.END, values=(
                    checked,
                    group_label,
                    str(rel),
                    dedup.format_size(file_size),
                    mod_str,
                ))

        self.summary_var.set(
            f"{total_groups} duplicate group(s)  •  "
            f"{total_dupes} duplicate file(s)  •  "
            f"Wasted space: {dedup.format_size(wasted)}"
        )
        self._update_action_buttons()

    # ------------------------------------------------------------------
    # Scan
    # ------------------------------------------------------------------

    def _on_scan(self):
        scan_path = self.scan_path_var.get().strip()
        if not scan_path:
            messagebox.showwarning("Scan", "Please choose a folder to scan.")
            return
        if not Path(scan_path).is_dir():
            messagebox.showerror("Scan", f"Not a directory: {scan_path}")
            return

        if self._scan_running:
            return

        # Capture all Tkinter variables on the main thread (thread safety)
        self._scan_params = {
            "scan_path": scan_path,
            "follow_symlinks": self.follow_symlinks_var.get(),
            "min_size": self.min_size_var.get(),
            "no_default_skip": self.no_default_skip_var.get(),
            "skip_dirs": self.skip_dirs_var.get().strip(),
        }

        self._cancel_event.clear()
        self._set_running(True)
        self.progress_bar.configure(mode="determinate", maximum=1, value=0)
        self.status_var.set("Scanning…")

        self._worker_thread = threading.Thread(
            target=self._do_scan, daemon=True
        )
        self._worker_thread.start()

    def _do_scan(self):
        """Worker thread: run scan with progress callbacks."""
        try:
            # Use pre-captured params (thread safety — never read Tk vars from worker)
            params = self._scan_params
            scan_path = Path(params["scan_path"])

            # Build skip dirs set
            if params["no_default_skip"]:
                skip_dirs = set()
            else:
                skip_dirs = set(dedup.DEFAULT_SKIP_DIRS)
            extra = params["skip_dirs"]
            if extra:
                skip_dirs.update(s.strip() for s in extra.split(",") if s.strip())

            def log_cb(msg):
                self.root.after(0, lambda m=msg: self._log_message(m))

            def progress_cb(current, total, message):
                self.root.after(0, lambda c=current, t=total, m=message: self._update_progress(c, t, m))

            cancel_event = self._cancel_event

            duplicates = dedup.scan_directory(
                root=scan_path,
                skip_dirs=skip_dirs,
                follow_symlinks=params["follow_symlinks"],
                min_size=params["min_size"],
                log_callback=log_cb,
                progress_callback=progress_cb,
                cancel_event=cancel_event,
            )

            self._duplicates = duplicates
            self._scan_root = scan_path

            # Populate tree on main thread
            self.root.after(0, lambda: self._on_scan_complete(duplicates, scan_path))

        except Exception as ex:
            self.root.after(0, lambda: self._on_scan_error(str(ex)))
        finally:
            self.root.after(0, self._set_running_false)

    def _log_message(self, msg):
        """Append a log message to status (called on main thread)."""
        compact = " ".join(msg.strip().split())
        if compact:
            self.status_var.set(compact[:120])

    def _update_progress(self, current, total, message):
        """Update progress bar (called on main thread)."""
        if total > 0:
            self.progress_bar.configure(maximum=total, value=current)
        self.status_var.set(message)

    def _on_scan_complete(self, duplicates, scan_root):
        """Handle scan completion on the main thread."""
        self.progress_bar.configure(mode="determinate", maximum=1, value=1)

        if not duplicates:
            # Clear stale results from previous scan
            for item in self.tree.get_children():
                self.tree.delete(item)
            self._selected_items.clear()
            self._update_action_buttons()
            self.summary_var.set("✅ No duplicate files found!")
            self.status_var.set("Scan complete — no duplicates")
            messagebox.showinfo("Scan Complete", "No duplicate files found!")
        else:
            self._populate_tree(duplicates, scan_root)
            total_groups = len(duplicates)
            total_dupes = sum(len(v) - 1 for v in duplicates.values())
            self.status_var.set(
                f"Scan complete — {total_groups} group(s), {total_dupes} duplicate(s)"
            )

    def _on_scan_error(self, error_msg):
        self.status_var.set(f"Error: {error_msg[:100]}")
        messagebox.showerror("Scan Error", error_msg)

    # ------------------------------------------------------------------
    # Delete selected
    # ------------------------------------------------------------------

    def _on_delete(self):
        if not self._selected_items:
            messagebox.showwarning("Delete", "No files selected.")
            return

        selected_paths = self._collect_selected_paths()
        if not selected_paths:
            return

        count = len(selected_paths)
        if not messagebox.askyesno(
            "Confirm Delete",
            f"⚠️  Permanently delete {count} selected file(s)?\n\n"
            f"This cannot be undone!",
        ):
            return

        # Capture cancel_event on main thread
        cancel_event = self._cancel_event
        cancel_event.clear()
        self._set_running(True)
        self.status_var.set(f"Deleting {count} file(s)…")

        self._worker_thread = threading.Thread(
            target=self._do_delete, args=(selected_paths, cancel_event), daemon=True
        )
        self._worker_thread.start()

    def _do_delete(self, paths: list[Path], cancel_event: threading.Event):
        deleted = 0
        for p in paths:
            if cancel_event.is_set():
                break
            try:
                p.unlink()
                deleted += 1
            except OSError as e:
                self.root.after(0, lambda msg=f"Error deleting {p}: {e}": self._log_message(msg))
        self.root.after(0, lambda: self._on_action_complete("Deleted", deleted))

    # ------------------------------------------------------------------
    # Move to staging
    # ------------------------------------------------------------------

    def _on_stage(self):
        if not self._selected_items:
            messagebox.showwarning("Stage", "No files selected.")
            return

        staging = self.staging_path_var.get().strip()
        if not staging:
            messagebox.showwarning("Stage", "Please set a staging directory first.")
            return

        selected_paths = self._collect_selected_paths()
        if not selected_paths:
            return

        count = len(selected_paths)
        if not messagebox.askyesno(
            "Confirm Move",
            f"Move {count} selected file(s) to:\n{staging}\n\nContinue?",
        ):
            return

        # Capture cancel_event and scan_root on main thread
        cancel_event = self._cancel_event
        scan_root = self._scan_root or Path(".")
        cancel_event.clear()
        self._set_running(True)
        self.status_var.set(f"Moving {count} file(s) to staging…")

        self._worker_thread = threading.Thread(
            target=self._do_stage, args=(selected_paths, Path(staging), scan_root, cancel_event), daemon=True
        )
        self._worker_thread.start()

    def _do_stage(self, paths: list[Path], staging: Path, root: Path, cancel_event: threading.Event):
        staging.mkdir(parents=True, exist_ok=True)
        moved = 0

        for dupe in paths:
            if cancel_event.is_set():
                break
            rel = dupe.relative_to(root) if dupe.is_relative_to(root) else dupe.name
            dest = staging / rel
            dest.parent.mkdir(parents=True, exist_ok=True)

            if dest.exists():
                stem = dest.stem
                suffix = dest.suffix
                counter = 1
                while dest.exists():
                    dest = dest.parent / f"{stem}_{counter}{suffix}"
                    counter += 1

            try:
                shutil.move(str(dupe), str(dest))
                moved += 1
            except (OSError, shutil.Error) as e:
                self.root.after(0, lambda msg=f"Error moving {dupe}: {e}": self._log_message(msg))

        self.root.after(0, lambda: self._on_action_complete("Moved", moved))

    # ------------------------------------------------------------------
    # Export JSON
    # ------------------------------------------------------------------

    def _on_export(self):
        if not self._duplicates or not self._scan_root:
            messagebox.showwarning("Export", "No scan results to export.")
            return

        output_path = filedialog.asksaveasfilename(
            title="Export Results as JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="duplicate_report.json",
        )
        if not output_path:
            return

        try:
            import json
            report = dedup.json_report(self._duplicates, self._scan_root)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.status_var.set(f"Exported to {output_path}")
            messagebox.showinfo("Export Complete", f"Report saved to:\n{output_path}")
        except Exception as ex:
            messagebox.showerror("Export Error", str(ex))

    # ------------------------------------------------------------------
    # Clear results
    # ------------------------------------------------------------------

    def _on_clear_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._selected_items.clear()
        self._duplicates = {}
        self._scan_root = None
        self.summary_var.set("No results yet")
        self.progress_bar.configure(value=0)
        self.status_var.set("Results cleared")
        self._update_action_buttons()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _collect_selected_paths(self) -> list[Path]:
        """Collect file paths for selected tree items."""
        if not self._scan_root:
            return []
        paths = []
        for item_id in self._selected_items:
            values = self.tree.item(item_id, "values")
            if values and values[2]:
                file_path = self._scan_root / values[2]
                if file_path.exists():
                    paths.append(file_path)
        return paths

    def _on_action_complete(self, action: str, count: int):
        """Handle completion of delete/move action."""
        self.status_var.set(f"{action} {count} file(s).")
        self._set_running(False)
        # Re-scan to refresh results
        if messagebox.askyesno(
            "Action Complete",
            f"{action} {count} file(s).\n\nRe-scan the folder to refresh results?",
        ):
            self._on_scan()
        else:
            self._on_clear_results()

    def _set_running(self, running: bool):
        self._scan_running = running
        state = tk.DISABLED if running else tk.NORMAL
        cancel_state = tk.NORMAL if running else tk.DISABLED
        self.btn_scan.configure(state=state)
        self.btn_cancel.configure(state=cancel_state)
        self.btn_delete.configure(state=state if not running and self._selected_items else tk.DISABLED)
        self.btn_stage.configure(state=state if not running and self._selected_items else tk.DISABLED)
        self.btn_export.configure(state=state if not running and self._duplicates else tk.DISABLED)
        self.btn_clear.configure(state=state if not running and self.tree.get_children() else tk.DISABLED)
        self.root.update_idletasks()

    def _set_running_false(self):
        self._set_running(False)

    def _on_cancel(self):
        self._cancel_event.set()
        self.status_var.set("Cancelling…")

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------

    def _load_settings(self):
        saved = settings.load_settings()

        if saved.get("scan_path"):
            self.scan_path_var.set(saved["scan_path"])
        if saved.get("staging_path"):
            self.staging_path_var.set(saved["staging_path"])
        self.min_size_var.set(saved.get("min_size", 0))
        self.follow_symlinks_var.set(saved.get("follow_symlinks", False))
        self.no_default_skip_var.set(saved.get("no_default_skip", False))
        if saved.get("skip_dirs"):
            self.skip_dirs_var.set(saved["skip_dirs"])

        # Window geometry
        wx = saved.get("window_x")
        wy = saved.get("window_y")
        ww = saved.get("window_width", 820)
        wh = saved.get("window_height", 680)
        if wx is not None and wy is not None:
            self.root.geometry(f"{ww}x{wh}+{wx}+{wy}")
        else:
            self.root.geometry(f"{ww}x{wh}")

    def _save_current_settings(self):
        try:
            geo = self.root.geometry()
            parts = geo.replace("+", " ").replace("x", " ").split()
            ww, wh = int(parts[0]), int(parts[1])
            wx, wy = int(parts[2]), int(parts[3])
        except Exception:
            ww, wh, wx, wy = 820, 680, None, None

        settings.save_settings({
            "scan_path": self.scan_path_var.get().strip(),
            "staging_path": self.staging_path_var.get().strip(),
            "min_size": self.min_size_var.get(),
            "follow_symlinks": self.follow_symlinks_var.get(),
            "no_default_skip": self.no_default_skip_var.get(),
            "skip_dirs": self.skip_dirs_var.get().strip(),
            "window_x": wx,
            "window_y": wy,
            "window_width": ww,
            "window_height": wh,
        })

    def _on_close(self):
        self._save_current_settings()
        self.root.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_gui():
    """Launch the Duplicate File Detector GUI."""
    root = tk.Tk()
    app = DedupGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
