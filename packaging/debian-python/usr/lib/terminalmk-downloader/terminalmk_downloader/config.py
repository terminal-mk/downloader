from __future__ import annotations

import json
import sys
from pathlib import Path


def config_dir() -> Path:
    if sys.platform.startswith("win"):
        base = Path.home() / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    d = base / "terminalmk-downloader"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _config_path() -> Path:
    return config_dir() / "config.json"


def load() -> dict:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - corrupt config shouldn't crash the app
        return {}


def save(data: dict) -> None:
    _config_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def has_registered_before() -> bool:
    return bool(load().get("registered"))


def mark_registered(message: str) -> None:
    data = load()
    data["registered"] = True
    data["registration_message"] = message
    save(data)


def get_output_dir(default: str) -> str:
    return load().get("output_dir", default)


def set_output_dir(path: str) -> None:
    data = load()
    data["output_dir"] = path
    save(data)
