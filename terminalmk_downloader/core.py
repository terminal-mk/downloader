"""
Core logic for the terminal.mk Downloader.

This module knows nothing about argparse or Tk -- it's the shared engine
that both the CLI (cli.py) and the future GUI import. It covers the two
ways a batch of files can reach this app, exactly as described in the
CF.js "Download All" handoff:

  1. A "lean" CSV with columns FilingID, Form, Date, AttachmentIndex, Link
     -- the fallback the website saves to Downloads when it can't reach
     this app directly.
  2. A `terminal.mk-dl://download?dz=<base64url zlib-deflated JSON>` (or,
     for very old website builds, `?d=<base64url JSON>` uncompressed) URI
     -- the direct handoff the website attempts first, via a custom
     protocol this app registers itself as the handler for.

     The payload is deflate-compressed (CF.js uses pako.deflate(), a JS
     port of zlib, matched here by Python's stdlib zlib module) because
     the raw JSON blows past safe custom-protocol URI lengths almost
     immediately -- a perfectly ordinary batch of ~40 attachments already
     produces a 7000+ character URI uncompressed, past CF.js's own
     MAX_PROTOCOL_URI_LENGTH safety cutoff. The payload is mostly
     repeated key names and similar-looking URLs, so it compresses
     extremely well (40 items: ~7KB -> well under 500 bytes), turning
     "silently falls back to CSV for almost any real batch" into "only
     truly enormous batches ever hit the cutoff".

Both paths resolve to the same thing: a batch name + a flat list of
DownloadItem, which get_batch() below fetches concurrently.
"""

from __future__ import annotations

import base64
import csv
import dataclasses
import json
import mimetypes
import re
import threading
import time
import urllib.parse
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

import requests

PROTOCOL_SCHEME = "terminal.mk-dl"
DEFAULT_CONCURRENCY = 6
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.5

USER_AGENT = "terminal.mk-dl/1.0 (+https://github.com/terminal-mk/downloader)"


@dataclasses.dataclass
class DownloadItem:
    filing_id: str
    attachment_index: str
    link: str
    form: str = ""
    date: str = ""

    @property
    def base_name(self) -> str:
        idx = self.attachment_index or "1"
        return f"{self.filing_id}_{idx}"


@dataclasses.dataclass
class DownloadResult:
    item: DownloadItem
    ok: bool
    path: Optional[Path] = None
    error: Optional[str] = None
    bytes_written: int = 0
    attempts: int = 0


@dataclasses.dataclass
class Batch:
    name: str
    items: list[DownloadItem]


# ---------------------------------------------------------------------
# Parsing: lean CSV
# ---------------------------------------------------------------------
def parse_lean_csv(path: str | Path) -> Batch:
    """Parse a FilingID,Form,Date,AttachmentIndex,Link CSV, as produced
    by the CF view's "Download All" fallback. Also tolerates the wider
    per-row export CSV (ID,Form,Title,Date,Time,Link,Attachment_1..N) by
    flattening its Attachment_* columns."""
    path = Path(path)
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    items: list[DownloadItem] = []

    if "AttachmentIndex" in fieldnames and "Link" in fieldnames:
        for row in rows:
            link = (row.get("Link") or "").strip()
            if not link:
                continue
            items.append(
                DownloadItem(
                    filing_id=(row.get("FilingID") or row.get("ID") or "").strip(),
                    attachment_index=(row.get("AttachmentIndex") or "1").strip(),
                    link=link,
                    form=(row.get("Form") or "").strip(),
                    date=(row.get("Date") or "").strip(),
                )
            )
    else:
        # Wide export format: Attachment_1, Attachment_2, ...
        attachment_cols = [c for c in fieldnames if re.match(r"^Attachment_\d+$", c)]
        for row in rows:
            filing_id = (row.get("ID") or row.get("FilingID") or "").strip()
            for col in attachment_cols:
                link = (row.get(col) or "").strip()
                if not link:
                    continue
                idx = col.split("_", 1)[1]
                items.append(
                    DownloadItem(
                        filing_id=filing_id,
                        attachment_index=idx,
                        link=link,
                        form=(row.get("Form") or "").strip(),
                        date=(row.get("Date") or "").strip(),
                    )
                )

    if not items:
        raise ValueError(f"No downloadable links found in {path}")

    return Batch(name=path.stem, items=items)


# ---------------------------------------------------------------------
# Parsing: terminal.mk-dl:// protocol URI
# ---------------------------------------------------------------------
def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def parse_protocol_uri(uri: str) -> Batch:
    """Parse terminal.mk-dl://download?dz=<base64url zlib-deflated JSON>
    (current) or the older, uncompressed
    terminal.mk-dl://download?d=<base64url JSON> (kept for backward
    compatibility with any site build still sending the old param).

    Payload shape (see CF.js buildProtocolPayload):
        {"n": "<output name>", "items": [{"f": filingId, "i": attIndex, "l": link}, ...]}
    """
    uri = uri.strip()
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme != PROTOCOL_SCHEME:
        raise ValueError(f"Not a {PROTOCOL_SCHEME}:// URI: {uri!r}")

    qs = urllib.parse.parse_qs(parsed.query)
    encoded_compressed = (qs.get("dz") or [None])[0]
    encoded_plain = (qs.get("d") or [None])[0]

    if encoded_compressed:
        try:
            raw = zlib.decompress(_b64url_decode(encoded_compressed))
        except zlib.error as exc:
            raise ValueError(f"Couldn't decompress 'dz' payload: {exc}") from exc
    elif encoded_plain:
        raw = _b64url_decode(encoded_plain)
    else:
        raise ValueError("URI is missing the 'dz' (or 'd') payload parameter")

    payload = json.loads(raw.decode("utf-8"))
    name = payload.get("n") or "terminalMkDownloader_download"
    raw_items = payload.get("items") or []

    items = [
        DownloadItem(
            filing_id=str(it.get("f", "")),
            attachment_index=str(it.get("i", "1")),
            link=str(it.get("l", "")),
        )
        for it in raw_items
        if it.get("l")
    ]
    if not items:
        raise ValueError("Payload contained no downloadable links")

    return Batch(name=name, items=items)


def load_batch(source: str) -> Batch:
    """Auto-detect a terminal.mk-dl:// URI vs a CSV file path and parse it."""
    if source.strip().lower().startswith(f"{PROTOCOL_SCHEME}://"):
        return parse_protocol_uri(source)
    return parse_lean_csv(source)


# ---------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------
def _safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name or "file"


def _extension_from_response(resp: requests.Response, link: str) -> str:
    cd = resp.headers.get("Content-Disposition", "")
    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd)
    if match:
        ext = Path(match.group(1)).suffix
        if ext:
            return ext
    path_ext = Path(urllib.parse.urlparse(link).path).suffix
    if path_ext:
        return path_ext
    ctype = resp.headers.get("Content-Type", "").split(";")[0].strip()
    guessed = mimetypes.guess_extension(ctype) if ctype else None
    return guessed or ".pdf"  # terminal.mk filings are overwhelmingly PDFs


def _download_one(
    item: DownloadItem,
    dest_dir: Path,
    session: requests.Session,
    cancel_event: Optional[threading.Event] = None,
) -> DownloadResult:
    if cancel_event is not None and cancel_event.is_set():
        return DownloadResult(item=item, ok=False, error="Cancelled", attempts=0)

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        if cancel_event is not None and cancel_event.is_set():
            return DownloadResult(item=item, ok=False, error="Cancelled", attempts=attempt)
        try:
            with session.get(item.link, timeout=REQUEST_TIMEOUT, stream=True) as resp:
                resp.raise_for_status()
                ext = _extension_from_response(resp, item.link)
                filename = _safe_filename(item.base_name) + ext
                dest_path = dest_dir / filename
                written = 0
                with open(dest_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        if cancel_event is not None and cancel_event.is_set():
                            f.close()
                            dest_path.unlink(missing_ok=True)
                            return DownloadResult(item=item, ok=False, error="Cancelled", attempts=attempt)
                        if chunk:
                            f.write(chunk)
                            written += len(chunk)
                return DownloadResult(item=item, ok=True, path=dest_path, bytes_written=written, attempts=attempt)
        except Exception as exc:  # noqa: BLE001 - report, don't crash the batch
            last_error = str(exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    return DownloadResult(item=item, ok=False, error=last_error, attempts=MAX_RETRIES)


def download_batch(
    batch: Batch,
    output_dir: str | Path,
    concurrency: int = DEFAULT_CONCURRENCY,
    on_progress: Optional[Callable[[DownloadResult, int, int], None]] = None,
    cancel_event: Optional[threading.Event] = None,
) -> list[DownloadResult]:
    """Download every item in `batch` into output_dir/<batch.name>/.

    Runs with a small thread pool (this is plain HTTP downloading, not
    the browser's popup-per-tab dance CF.js has to work around -- no
    tab/window limits apply here). on_progress, if given, is called
    after every completed file with (result, completed_count, total).

    If `cancel_event` is set (from another thread, e.g. a GUI Cancel
    button) partway through: in-flight files stop writing and are
    dropped, any not-yet-started files are skipped, and everything
    still queued is reported back as a "Cancelled" DownloadResult so
    the caller's progress/summary UI can show what did and didn't make
    it before the cancel.
    """
    dest_dir = Path(output_dir) / _safe_filename(batch.name)
    dest_dir.mkdir(parents=True, exist_ok=True)

    results: list[DownloadResult] = []
    total = len(batch.items)
    completed = 0

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        futures = {
            pool.submit(_download_one, item, dest_dir, session, cancel_event): item
            for item in batch.items
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            if on_progress:
                on_progress(result, completed, total)
            if cancel_event is not None and cancel_event.is_set():
                # Stop waiting on the rest; anything still pending in the
                # pool hasn't started yet and can be dropped outright.
                for f in futures:
                    f.cancel()
                break

    return results
