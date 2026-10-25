"""A small standard-library desktop UI for users who prefer not to use a terminal."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .models import ScanResult
from .packing import PackError, create_bundle
from .report import render_markdown, render_text
from .scanner import scan_project


class PushLensApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PushLens — GitHub upload preflight")
        self.root.geometry("860x620")
        self.root.minsize(680, 460)
        self.path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Choose a project folder to begin.")
        self.latest_result: ScanResult | None = None
        self._build()

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=22)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="PushLens", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="Check a project before it goes to GitHub. Everything stays on this computer.",
            wraplength=790,
        ).pack(anchor="w", pady=(4, 18))

        chooser = ttk.Frame(outer)
        chooser.pack(fill="x")
        self.path_entry = ttk.Entry(chooser, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True)
        self.browse_button = ttk.Button(chooser, text="Browse…", command=self._choose)
        self.browse_button.pack(side="left", padx=(8, 0))
        self.scan_button = ttk.Button(outer, text="Check project", command=self._scan)
        self.scan_button.pack(anchor="w", pady=12)

        self.notebook = ttk.Notebook(outer)
        self.notebook.pack(fill="both", expand=True)
        self.output = self._text_tab("Findings")
        self.files_output = self._text_tab("Files in the ZIP")
        ttk.Label(outer, textvariable=self.status_var).pack(anchor="w", pady=(10, 0))

        buttons = ttk.Frame(outer)
        buttons.pack(fill="x", pady=(10, 0))
        self.save_button = ttk.Button(buttons, text="Save report…", command=self._save_report, state="disabled")
        self.save_button.pack(side="left")
        self.pack_button = ttk.Button(buttons, text="Create clean ZIP…", command=self._pack, state="disabled")
        self.pack_button.pack(side="right")

    def _text_tab(self, label: str) -> tk.Text:
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=label)
        text = tk.Text(frame, wrap="none", state="disabled", font=("Consolas", 10))
        vertical = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        text.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return text

    def _choose(self) -> None:
        selected = filedialog.askdirectory(title="Choose the project folder")
        if selected:
            self.path_var.set(selected)
            self._scan()

    def _set_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")

    def _scan(self) -> None:
        path = self.path_var.get().strip()
        if not path:
            self._choose()
            return
        self.scan_button.configure(state="disabled")
        self.browse_button.configure(state="disabled")
        self.path_entry.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self.pack_button.configure(state="disabled")
        self.latest_result = None
        self.status_var.set("Scanning locally…")

        def worker() -> None:
            try:
                result = scan_project(path)
                error = None
            except Exception as exc:  # Surface filesystem errors in the UI thread.
                result, error = None, exc

            def finish() -> None:
                self.scan_button.configure(state="normal")
                self.browse_button.configure(state="normal")
                self.path_entry.configure(state="normal")
                if error is not None:
                    self.status_var.set("Scan could not be completed.")
                    messagebox.showerror("PushLens", str(error), parent=self.root)
                    return
                self.latest_result = result
                assert result is not None
                self.save_button.configure(state="normal")
                self._set_output(render_text(result))
                self._set_files("\n".join(result.files))
                self.status_var.set(f"{result.status} · {len(result.files):,} files inventoried")
                self.pack_button.configure(state="normal" if not result.blocked else "disabled")

            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def _set_files(self, text: str) -> None:
        self.files_output.configure(state="normal")
        self.files_output.delete("1.0", "end")
        self.files_output.insert("1.0", text or "No files will be included.")
        self.files_output.configure(state="disabled")

    def _save_report(self) -> None:
        if self.latest_result is None:
            messagebox.showinfo("PushLens", "Run a project check first.", parent=self.root)
            return
        target = filedialog.asksaveasfilename(
            title="Save report", defaultextension=".md", initialfile="pushlens-report.md",
            filetypes=(("Markdown", "*.md"), ("Text", "*.txt")),
        )
        if target:
            try:
                report_path = Path(target).resolve()
                if report_path.is_relative_to(self.latest_result.root):
                    messagebox.showerror("PushLens", "Save reports outside the scanned project so a report cannot overwrite source files.", parent=self.root)
                    return
                report = render_markdown(self.latest_result) if target.lower().endswith(".md") else render_text(self.latest_result)
                report_path.write_text(report, encoding="utf-8")
            except OSError as exc:
                messagebox.showerror("PushLens", f"The report could not be saved: {exc}", parent=self.root)
                return
            self.status_var.set(f"Report saved: {target}")

    def _pack(self) -> None:
        if self.latest_result is None or self.latest_result.blocked:
            return
        target = filedialog.asksaveasfilename(
            title="Create clean source ZIP", defaultextension=".zip",
            initialfile=f"{self.latest_result.root.name}-github-upload.zip",
            filetypes=(("ZIP archive", "*.zip"),),
        )
        if not target:
            return
        project_path = self.latest_result.root
        self.pack_button.configure(state="disabled")
        self.status_var.set("Creating ZIP…")

        def worker() -> None:
            try:
                output, _result = create_bundle(project_path, target, overwrite=Path(target).exists())
                error = None
            except (OSError, ValueError, PackError) as exc:
                output, error = None, exc

            def finish() -> None:
                self.pack_button.configure(state="normal" if self.latest_result and not self.latest_result.blocked else "disabled")
                if error:
                    self.status_var.set("Bundle could not be created.")
                    messagebox.showerror("PushLens", str(error), parent=self.root)
                    return
                messagebox.showinfo("PushLens", f"ZIP ready:\n{output}\n\nExtract it before uploading files in the GitHub browser.", parent=self.root)
                self.status_var.set(f"Bundle created: {output}")

            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()


def launch() -> None:
    root = tk.Tk()
    PushLensApp(root)
    root.mainloop()
