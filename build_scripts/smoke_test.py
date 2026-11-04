#!/usr/bin/env python3
"""End-to-end check of a built CLI binary, run by CI on every platform.

Usage: smoke_test.py <path-to-terminal.mk-dl-binary>

Everything is synthetic and stays on this machine: a throwaway HTTP server on
127.0.0.1 serves the files, and the CSV and URI below are made up here.
"""

from __future__ import annotations

import base64
import http.server
import json
import subprocess
import sys
import tempfile
import threading
import zlib
from pathlib import Path

BODY = b"%PDF-1.4 smoke test\n"


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

    def log_message(self, *args):
        pass


def run(binary: str, *args: str) -> None:
    result = subprocess.run([binary, "--no-color", *args], capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        sys.exit(f"{args[0]} exited {result.returncode}\n{result.stdout}\n{result.stderr}")


def check(folder: Path, *names: str) -> None:
    for name in names:
        path = folder / name
        if not path.is_file() or path.read_bytes() != BODY:
            sys.exit(f"Missing or wrong file: {path}")


def main() -> None:
    binary = str(Path(sys.argv[1]).resolve())
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)

        csv_path = out / "smoke_csv.csv"
        csv_path.write_text(
            "FilingID,Form,Date,AttachmentIndex,Link\n"
            f"A1,X,2026-01-01,1,{base}/a.pdf\n"
            f"A1,X,2026-01-01,2,{base}/b.pdf\n",
            encoding="utf-8",
        )
        run(binary, "csv", str(csv_path), "-o", str(out))
        check(out / "smoke_csv", "A1_1.pdf", "A1_2.pdf")

        payload = {"n": "smoke_uri", "items": [{"f": "B2", "i": "1", "l": f"{base}/c.pdf"}]}
        encoded = base64.urlsafe_b64encode(zlib.compress(json.dumps(payload).encode())).decode().rstrip("=")
        run(binary, "uri", f"terminal.mk-dl://download?dz={encoded}", "-o", str(out))
        check(out / "smoke_uri", "B2_1.pdf")

    server.shutdown()
    print("Smoke test passed")


if __name__ == "__main__":
    main()
