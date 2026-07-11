"""
terminal.mk Downloader -- GUI

Flow:
  1. Launched with a terminalmk-dl:// URI or a CSV path as argv[1]
     (that's what the protocol handler / file association passes in)
     -> straight to the review screen.
  2. Launched with no argument (plain double-click)
     -> blank screen: paste a link, or browse for a CSV.
  3. Review screen: flat list, one row per attachment, checkbox per row,
     Select All / Select None, then Download.
  4. Progress screen while downloading (threaded, UI stays responsive).
  5. Summary screen: counts + Open Folder.

macOS note: launching via a terminalmk-dl:// link (rather than double-
clicking the .app or opening a CSV) delivers the URL as a Cocoa
"open URL" Apple Event, not argv -- plain Tkinter doesn't see that. The
CSV/browse/paste paths below all work fine as-is; wiring up the Apple
Event needs a small platform hook at .app packaging time (e.g. via
pyobjc) and is tracked as follow-up work, not blocking this build.
"""

from __future__ import annotations

import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import config, core, protocol
from .theme import ACCENT_ORANGE, ACCENT_TEAL, ACCENT_WINE, BG, BG_PANEL, BG_SECONDARY, TEXT, TEXT_MUTED

CHECK_ON = "\u2611"   # ☑
CHECK_OFF = "\u2610"  # ☐

DEFAULT_OUTPUT_DIR = str(Path.home() / "Downloads" / "terminalmk")


def open_in_file_manager(path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            import os
            os.startfile(str(path))  # noqa: S606
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception:  # noqa: BLE001 - opening a folder is a nicety, never fatal
        pass


class App(tk.Tk):
    def __init__(self, source: str | None = None):
        super().__init__()
        self.title("terminal.mk Downloader")
        self.geometry("900x600")
        self.minsize(700, 480)
        self.configure(bg=BG)

        self._apply_theme()
        self._ensure_registered()

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)
        self.current_screen: tk.Frame | None = None

        if source:
            self._load_source(source)
        else:
            self.show(BlankScreen(self.container, self))

    # ------------------------------------------------------------------
    def _apply_theme(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background=BG, foreground=TEXT, fieldbackground=BG_PANEL,
                         font=("Segoe UI", 10))
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=BG_SECONDARY)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Muted.TLabel", background=BG, foreground=TEXT_MUTED)
        style.configure("Title.TLabel", background=BG, foreground=ACCENT_ORANGE,
                         font=("Segoe UI", 16, "bold"))
        style.configure("Subtitle.TLabel", background=BG, foreground=TEXT_MUTED, font=("Segoe UI", 10))

        style.configure("TEntry", fieldbackground=BG_PANEL, foreground=TEXT, insertcolor=TEXT)

        style.configure("Teal.TButton", background=ACCENT_TEAL, foreground=BG,
                         borderwidth=0, focusthickness=0, padding=8, font=("Segoe UI", 10, "bold"))
        style.map("Teal.TButton", background=[("active", "#20877d")])

        style.configure("Orange.TButton", background=ACCENT_ORANGE, foreground=BG_SECONDARY,
                         borderwidth=0, focusthickness=0, padding=8, font=("Segoe UI", 10, "bold"))
        style.map("Orange.TButton", background=[("active", "#cc7000")])

        style.configure("Wine.TButton", background=ACCENT_WINE, foreground=TEXT,
                         borderwidth=0, focusthickness=0, padding=8, font=("Segoe UI", 10, "bold"))
        style.map("Wine.TButton", background=[("active", "#86213f")])

        style.configure("Plain.TButton", background=BG_PANEL, foreground=TEXT,
                         borderwidth=0, focusthickness=0, padding=8)
        style.map("Plain.TButton", background=[("active", "#46608a")])

        style.configure("Treeview", background=BG_SECONDARY, fieldbackground=BG_SECONDARY,
                         foreground=TEXT, rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading", background=BG_PANEL, foreground=TEXT,
                         borderwidth=0, font=("Segoe UI", 9, "bold"))
        style.map("Treeview.Heading", background=[("active", "#46608a")])
        style.map("Treeview", background=[("selected", "#3b4e6e")], foreground=[("selected", TEXT)])

        style.configure("TProgressbar", background=ACCENT_TEAL, troughcolor=BG_PANEL, borderwidth=0)

    def _ensure_registered(self) -> None:
        if config.has_registered_before():
            return

        def do_register() -> None:
            try:
                msg = protocol.register(for_gui=True)
            except Exception as exc:  # noqa: BLE001
                msg = f"Registration failed: {exc}"
            config.mark_registered(msg)

        threading.Thread(target=do_register, daemon=True).start()

    # ------------------------------------------------------------------
    def show(self, screen: tk.Frame) -> None:
        if self.current_screen is not None:
            self.current_screen.destroy()
        self.current_screen = screen
        screen.pack(fill="both", expand=True)

    def _load_source(self, source: str) -> None:
        try:
            batch = core.load_batch(source)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("terminal.mk Downloader", f"Couldn't read that:\n\n{exc}")
            self.show(BlankScreen(self.container, self))
            return
        self.show(ReviewScreen(self.container, self, batch))


# =============================================================================
# Blank / drop screen
# =============================================================================
class BlankScreen(ttk.Frame):
    def __init__(self, parent: tk.Widget, app: App):
        super().__init__(parent, style="TFrame")
        self.app = app

        wrap = ttk.Frame(self, style="TFrame")
        wrap.place(relx=0.5, rely=0.42, anchor="center")

        ttk.Label(wrap, text="terminal.mk Downloader", style="Title.TLabel").pack(pady=(0, 4))
        ttk.Label(
            wrap,
            text="Paste a terminalmk-dl:// link from the site, or open a filings CSV.",
            style="Subtitle.TLabel",
        ).pack(pady=(0, 20))

        link_row = ttk.Frame(wrap, style="TFrame")
        link_row.pack(fill="x", pady=(0, 10))
        self.link_var = tk.StringVar()
        entry = ttk.Entry(link_row, textvariable=self.link_var, width=54)
        entry.pack(side="left", padx=(0, 8), ipady=4)
        entry.bind("<Return>", lambda e: self._load_link())
        ttk.Button(link_row, text="Load link", style="Teal.TButton", command=self._load_link).pack(side="left")

        ttk.Label(wrap, text="or", style="Muted.TLabel").pack(pady=4)

        ttk.Button(wrap, text="Browse for CSV…", style="Orange.TButton", command=self._browse_csv).pack(pady=(4, 0))

        footer = ttk.Frame(self, style="TFrame")
        footer.pack(side="bottom", fill="x", pady=14, padx=16)
        ttk.Label(footer, text=f"terminalmk-dl:// {'registered' if config.has_registered_before() else 'not registered yet'}",
                   style="Muted.TLabel").pack(side="left")
        ttk.Button(footer, text="Re-register app", style="Plain.TButton", command=self._reregister).pack(side="right")

    def _load_link(self) -> None:
        uri = self.link_var.get().strip()
        if not uri:
            return
        self.app._load_source(uri)

    def _browse_csv(self) -> None:
        path = filedialog.askopenfilename(title="Choose a CF filings CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.app._load_source(path)

    def _reregister(self) -> None:
        msg = protocol.register(for_gui=True)
        config.mark_registered(msg)
        messagebox.showinfo("terminal.mk Downloader", msg)
        self.app.show(BlankScreen(self.app.container, self.app))


# =============================================================================
# Review screen -- flat list, checkbox per row
# =============================================================================
class ReviewScreen(ttk.Frame):
    def __init__(self, parent: tk.Widget, app: App, batch: core.Batch):
        super().__init__(parent, style="TFrame")
        self.app = app
        self.batch = batch
        self.checked: dict[str, bool] = {}

        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=16, pady=(16, 8))
        ttk.Label(header, text=batch.name, style="Title.TLabel").pack(side="left")
        self.count_label = ttk.Label(header, text="", style="Subtitle.TLabel")
        self.count_label.pack(side="right")

        toolbar = ttk.Frame(self, style="TFrame")
        toolbar.pack(fill="x", padx=16, pady=(0, 8))
        ttk.Button(toolbar, text="Select all", style="Plain.TButton", command=self._select_all).pack(side="left")
        ttk.Button(toolbar, text="Select none", style="Plain.TButton", command=self._select_none).pack(side="left", padx=(8, 0))

        ttk.Label(toolbar, text="Save to:", style="Muted.TLabel").pack(side="left", padx=(24, 6))
        self.output_var = tk.StringVar(value=config.get_output_dir(DEFAULT_OUTPUT_DIR))
        ttk.Entry(toolbar, textvariable=self.output_var, width=36).pack(side="left")
        ttk.Button(toolbar, text="…", style="Plain.TButton", width=3, command=self._browse_output).pack(side="left", padx=(4, 0))

        self.download_btn = ttk.Button(toolbar, text="Download selected", style="Teal.TButton", command=self._start_download)
        self.download_btn.pack(side="right")

        # ---- table -------------------------------------------------
        table_frame = ttk.Frame(self, style="TFrame")
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        columns = ("sel", "filing", "att", "form", "date", "link")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="none")
        self.tree.heading("sel", text="")
        self.tree.heading("filing", text="Filing ID")
        self.tree.heading("att", text="#")
        self.tree.heading("form", text="Form")
        self.tree.heading("date", text="Date")
        self.tree.heading("link", text="Link")
        self.tree.column("sel", width=34, anchor="center", stretch=False)
        self.tree.column("filing", width=90, anchor="w", stretch=False)
        self.tree.column("att", width=40, anchor="center", stretch=False)
        self.tree.column("form", width=110, anchor="w", stretch=False)
        self.tree.column("date", width=100, anchor="w", stretch=False)
        self.tree.column("link", width=420, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("checked", background=BG_PANEL)
        self.tree.tag_configure("unchecked", background=BG_SECONDARY, foreground=TEXT_MUTED)

        for i, item in enumerate(batch.items):
            iid = str(i)
            self.checked[iid] = True
            self.tree.insert("", "end", iid=iid, values=(
                CHECK_ON, item.filing_id, item.attachment_index, item.form, item.date, item.link,
            ), tags=("checked",))

        self.tree.bind("<Button-1>", self._on_row_click)
        self._refresh_count()

    # ------------------------------------------------------------------
    def _on_row_click(self, event: tk.Event) -> None:
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return
        self._toggle(row_id)

    def _toggle(self, row_id: str) -> None:
        self.checked[row_id] = not self.checked[row_id]
        values = list(self.tree.item(row_id, "values"))
        values[0] = CHECK_ON if self.checked[row_id] else CHECK_OFF
        self.tree.item(row_id, values=values, tags=("checked" if self.checked[row_id] else "unchecked",))
        self._refresh_count()

    def _select_all(self) -> None:
        for row_id in self.tree.get_children():
            self.checked[row_id] = True
            values = list(self.tree.item(row_id, "values"))
            values[0] = CHECK_ON
            self.tree.item(row_id, values=values, tags=("checked",))
        self._refresh_count()

    def _select_none(self) -> None:
        for row_id in self.tree.get_children():
            self.checked[row_id] = False
            values = list(self.tree.item(row_id, "values"))
            values[0] = CHECK_OFF
            self.tree.item(row_id, values=values, tags=("unchecked",))
        self._refresh_count()

    def _refresh_count(self) -> None:
        n_selected = sum(1 for v in self.checked.values() if v)
        self.count_label.configure(text=f"{n_selected} of {len(self.batch.items)} selected")

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="Choose a download folder", initialdir=self.output_var.get())
        if path:
            self.output_var.set(path)

    def _start_download(self) -> None:
        selected_items = [self.batch.items[int(iid)] for iid, ok in self.checked.items() if ok]
        if not selected_items:
            messagebox.showinfo("terminal.mk Downloader", "Select at least one file first.")
            return
        output_dir = self.output_var.get().strip() or DEFAULT_OUTPUT_DIR
        config.set_output_dir(output_dir)

        sub_batch = core.Batch(name=self.batch.name, items=selected_items)
        self.app.show(ProgressScreen(self.app.container, self.app, sub_batch, output_dir))


# =============================================================================
# Progress screen
# =============================================================================
class ProgressScreen(ttk.Frame):
    def __init__(self, parent: tk.Widget, app: App, batch: core.Batch, output_dir: str):
        super().__init__(parent, style="TFrame")
        self.app = app
        self.batch = batch
        self.output_dir = output_dir
        self.results: list[core.DownloadResult] = []
        self.queue: queue.Queue = queue.Queue()

        wrap = ttk.Frame(self, style="TFrame")
        wrap.pack(fill="both", expand=True, padx=24, pady=24)

        ttk.Label(wrap, text=f"Downloading {batch.name}", style="Title.TLabel").pack(anchor="w")
        self.status_label = ttk.Label(wrap, text=f"0 of {len(batch.items)}", style="Subtitle.TLabel")
        self.status_label.pack(anchor="w", pady=(4, 12))

        self.progress = ttk.Progressbar(wrap, orient="horizontal", mode="determinate",
                                         maximum=max(1, len(batch.items)), style="TProgressbar")
        self.progress.pack(fill="x", pady=(0, 12))

        log_frame = ttk.Frame(wrap, style="Panel.TFrame")
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Listbox(log_frame, bg=BG_SECONDARY, fg=TEXT, borderwidth=0,
                               highlightthickness=0, selectbackground=BG_PANEL)
        self.log.pack(fill="both", expand=True, padx=8, pady=8)

        threading.Thread(target=self._run, daemon=True).start()
        self.after(80, self._poll)

    def _run(self) -> None:
        def on_progress(result: core.DownloadResult, completed: int, total: int) -> None:
            self.queue.put(("progress", result, completed, total))

        core.download_batch(self.batch, output_dir=self.output_dir, on_progress=on_progress)
        self.queue.put(("done", None, None, None))

    def _poll(self) -> None:
        try:
            while True:
                kind, result, completed, total = self.queue.get_nowait()
                if kind == "progress":
                    self.results.append(result)
                    self.progress["value"] = completed
                    self.status_label.configure(text=f"{completed} of {total}")
                    label = result.item.base_name if result.ok else f"{result.item.base_name} ({result.error})"
                    prefix = "OK   " if result.ok else "FAIL "
                    self.log.insert("end", f"{prefix}{label}")
                    self.log.see("end")
                elif kind == "done":
                    self._finish()
                    return
        except queue.Empty:
            pass
        self.after(80, self._poll)

    def _finish(self) -> None:
        dest_dir = Path(self.output_dir) / self.batch.name
        self.app.show(SummaryScreen(self.app.container, self.app, self.results, dest_dir))


# =============================================================================
# Summary screen
# =============================================================================
class SummaryScreen(ttk.Frame):
    def __init__(self, parent: tk.Widget, app: App, results: list[core.DownloadResult], dest_dir: Path):
        super().__init__(parent, style="TFrame")
        self.app = app
        self.dest_dir = dest_dir

        ok_count = sum(1 for r in results if r.ok)
        fail_count = len(results) - ok_count

        wrap = ttk.Frame(self, style="TFrame")
        wrap.place(relx=0.5, rely=0.38, anchor="center")

        style_name = "Title.TLabel"
        title = f"Downloaded {ok_count} of {len(results)} file(s)"
        label = ttk.Label(wrap, text=title, style=style_name)
        label.configure(foreground=ACCENT_TEAL if not fail_count else ACCENT_WINE)
        label.pack(pady=(0, 6))

        if fail_count:
            ttk.Label(wrap, text=f"{fail_count} failed -- see list below", style="Subtitle.TLabel").pack(pady=(0, 12))

        ttk.Label(wrap, text=f"Saved to: {self.dest_dir}", style="Muted.TLabel").pack(pady=(0, 16))

        btn_row = ttk.Frame(wrap, style="TFrame")
        btn_row.pack()
        ttk.Button(btn_row, text="Open folder", style="Teal.TButton",
                   command=lambda: open_in_file_manager(self.dest_dir)).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Done", style="Plain.TButton",
                   command=lambda: self.app.show(BlankScreen(self.app.container, self.app))).pack(side="left", padx=4)

        if fail_count:
            fail_frame = ttk.Frame(self, style="Panel.TFrame")
            fail_frame.place(relx=0.5, rely=0.78, anchor="center", relwidth=0.8)
            box = tk.Listbox(fail_frame, bg=BG_SECONDARY, fg=TEXT_MUTED, borderwidth=0,
                              highlightthickness=0, height=6)
            box.pack(fill="both", expand=True, padx=8, pady=8)
            for r in results:
                if not r.ok:
                    box.insert("end", f"{r.item.base_name}: {r.item.link}  ({r.error})")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    source = argv[0] if argv else None
    app = App(source=source)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
