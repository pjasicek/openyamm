#!/usr/bin/env python3
"""
The MM9 rework's isolated review root: `output/mm9_rework/assets_dev`, a hard-linked mirror of `assets_dev` in which
remade MM9 maps replace the current ones. Nothing here writes into `assets_dev`.

Every file in the mirror starts as a hard link to its `assets_dev` original, so writing into an existing file would
change the original too. Remade content is therefore only ever placed with `install()` (write a temporary file, then
rename it over the link) and stale files are removed with `remove()` (unlinking a mirror entry leaves the original).

    python3 level_generation/projects/mm9r_common/review_root.py           # create the mirror, or refresh it
    python3 level_generation/projects/mm9r_common/review_root.py --fresh   # recreate it from the current assets_dev

The paths placed with install() are recorded in output/mm9_rework/owned.txt. refresh() links every other file
again to its current assets_dev original: files added to assets_dev after the mirror was made appear, and files
assets_dev replaced (a new inode) are picked up; owned paths are left alone.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "assets_dev"
REVIEW = ROOT / "output/mm9_rework"
ASSETS = REVIEW / "assets_dev"
OWNED = REVIEW / "owned.txt"


def create(fresh: bool) -> None:
    if ASSETS.exists() and not fresh:
        return
    if ASSETS.exists():
        assert ASSETS.resolve().parent == REVIEW.resolve() and ASSETS.name == "assets_dev"
        shutil.rmtree(ASSETS)
    REVIEW.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cp", "-al", str(SOURCE), str(ASSETS)], check=True)


def owned() -> set[str]:
    return set(OWNED.read_text().split("\n")) - {""} if OWNED.exists() else set()


def refresh() -> int:
    """Link every non-owned file again to its current assets_dev original; returns how many links changed."""
    keep = owned()
    changed = 0
    for source in SOURCE.rglob("*"):
        if not source.is_file() or source.is_symlink():
            continue
        relative = source.relative_to(SOURCE).as_posix()
        if relative in keep:
            continue
        target = ASSETS / relative
        if target.exists() and os.path.samestat(target.stat(), source.stat()):
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            target.unlink()
        os.link(source, target)
        changed += 1
    return changed


def mirror_path(relative: str | Path) -> Path:
    path = (ASSETS / relative).resolve()
    if ASSETS.resolve() not in path.parents:
        raise ValueError(f"{relative} is outside the review root")
    return path


def install(relative: str | Path, data: bytes) -> Path:
    """Place a file in the mirror without touching a hard-linked original."""
    target = mirror_path(relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
    with os.fdopen(handle, "wb") as stream:
        stream.write(data)
    os.chmod(temporary, 0o644)
    os.replace(temporary, target)
    own(target)
    return target


def own(target: Path) -> None:
    """Record a mirror path as ours (installed or removed), so refresh() leaves it alone."""
    relative = target.relative_to(ASSETS.resolve()).as_posix()
    if relative not in owned():
        with OWNED.open("a") as stream:
            stream.write(relative + "\n")


def install_file(relative: str | Path, source: Path) -> Path:
    return install(relative, source.read_bytes())


def remove(relative: str | Path) -> None:
    """Remove a mirror entry (a link or a file of ours); the assets_dev original stays."""
    target = mirror_path(relative)
    if target.is_symlink() or target.is_file():
        target.unlink()
    own(target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fresh", action="store_true", help="recreate the mirror from the current assets_dev")
    arguments = parser.parse_args()
    if ASSETS.exists() and not arguments.fresh:
        print(f"{refresh()} links refreshed")
    create(arguments.fresh)
    print(ASSETS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
