"""
terminal.mk-dl CLI

Usage:
    terminal.mk-dl open <csv-path-or-terminal.mk-dl:// URI> [-o DIR] [-j N]
    terminal.mk-dl csv <path> [-o DIR] [-j N]
    terminal.mk-dl uri "<terminal.mk-dl://...>" [-o DIR] [-j N]
    terminal.mk-dl register
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import core, protocol
from .protocol import DISPLAY_NAME
from .theme import Ansi

DEFAULT_OUTPUT_DIR = str(Path.home() / "Downloads" / "Terminal MK")


def _print_header(ansi: Ansi, batch_name: str, count: int) -> None:
    print(ansi.bold(ansi.orange(DISPLAY_NAME)))
    print(ansi.muted(f"Batch: {batch_name}  ·  {count} file(s)"))
    print()


def _run_download(source: str, output_dir: str, concurrency: int, no_color: bool) -> int:
    ansi = Ansi(enabled=not no_color and sys.stdout.isatty())

    try:
        batch = core.load_batch(source)
    except Exception as exc:  # noqa: BLE001
        print(ansi.wine(f"Could not read {source!r}: {exc}"))
        return 1

    _print_header(ansi, batch.name, len(batch.items))

    total = len(batch.items)
    ok_count = 0
    fail_count = 0

    def on_progress(result: core.DownloadResult, completed: int, total: int) -> None:
        nonlocal ok_count, fail_count
        bar_width = 28
        filled = int(bar_width * completed / total)
        bar = ansi.teal("#" * filled) + ansi.muted("-" * (bar_width - filled))
        if result.ok:
            ok_count += 1
            status = ansi.teal("OK  ")
            label = result.path.name if result.path else result.item.base_name
        else:
            fail_count += 1
            status = ansi.wine("FAIL")
            label = f"{result.item.base_name}  ({result.error})"
        print(f"[{bar}] {completed}/{total}  {status}  {label}")

    results = core.download_batch(
        batch, output_dir=output_dir, concurrency=concurrency, on_progress=on_progress
    )

    print()
    summary = f"Done: {ok_count}/{total} downloaded"
    if fail_count:
        summary += f", {fail_count} failed"
    print(ansi.bold(ansi.teal(summary) if not fail_count else ansi.wine(summary)))

    dest_dir = Path(output_dir) / batch.name
    print(ansi.muted(f"Saved to: {dest_dir}"))

    if fail_count:
        print()
        print(ansi.orange("Failed files:"))
        for r in results:
            if not r.ok:
                print(f"  - {r.item.base_name}: {r.item.link}  ({r.error})")
        return 2

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="terminal.mk-dl",
        description=(
            "Batch-downloads filing attachments handed off from terminal.mk's "
            "'Download All' button (CSV file or terminal.mk-dl:// link)."
        ),
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colour output")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to save files into (default: {DEFAULT_OUTPUT_DIR})",
    )
    common.add_argument(
        "-j", "--concurrency", type=int, default=core.DEFAULT_CONCURRENCY,
        help=f"Parallel downloads (default: {core.DEFAULT_CONCURRENCY})",
    )

    p_open = sub.add_parser(
        "open", parents=[common],
        help="Auto-detect a CSV path or terminal.mk-dl:// URI and download it",
    )
    p_open.add_argument("source", help="Path to a lean CF CSV, or a terminal.mk-dl:// URI")

    p_csv = sub.add_parser("csv", parents=[common], help="Download from a lean CF CSV file")
    p_csv.add_argument("path", help="Path to the CSV file")

    p_uri = sub.add_parser("uri", parents=[common], help="Download from a terminal.mk-dl:// URI")
    p_uri.add_argument("uri", help="The terminal.mk-dl://download?d=... URI")

    sub.add_parser(
        "register",
        help="Register this app as the OS handler for terminal.mk-dl:// links",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "register":
        print(protocol.register(for_gui=False))
        return 0

    if args.command == "open":
        return _run_download(args.source, args.output, args.concurrency, args.no_color)
    if args.command == "csv":
        return _run_download(args.path, args.output, args.concurrency, args.no_color)
    if args.command == "uri":
        return _run_download(args.uri, args.output, args.concurrency, args.no_color)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
