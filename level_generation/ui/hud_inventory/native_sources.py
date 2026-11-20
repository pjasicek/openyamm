"""Explicit source-location migration for archived original icons (never used by the game)."""
import functools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


@functools.lru_cache(maxsize=1)
def archive_records():
    manifest = HERE / 'runtime_install_20260926/source_archive.json'
    return json.loads(manifest.read_text())['files'] if manifest.exists() else {}


def native_source(path):
    path = Path(path)
    key = str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
    record = archive_records().get(key)
    # A declared migration is authoritative, not an existence-based fallback.
    return ROOT / (record['archive'] if record else key)
