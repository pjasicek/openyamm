#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


STATIC_ASSET_MAPPINGS = (
    ("SOUNDS/SOUNDS", "sounds"),
    ("DATA/DATA/PCVOICES", "voices/pcvoices"),
    ("TEXTURES/TEXTURES", "textures"),
    ("SKINS/SKINS", "skins"),
)


def normalizedPath(path: Path) -> Path:
    return Path(*[part.lower() for part in path.parts])


def syncTree(sourceRoot: Path, destinationRoot: Path, dryRun: bool) -> tuple[int, int]:
    files = [path for path in sourceRoot.rglob("*") if path.is_file()]
    overwritten = 0

    for sourcePath in files:
        destinationPath = destinationRoot / normalizedPath(sourcePath.relative_to(sourceRoot))
        if destinationPath.exists():
            overwritten += 1

        if not dryRun:
            destinationPath.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sourcePath, destinationPath)

    return len(files), overwritten


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copy MM9 static assets that can stay in their original format into OpenYAMM world roots."
    )
    parser.add_argument("--extracted-root", type=Path, default=Path("mm9/extracted"))
    parser.add_argument(
        "--world-root",
        type=Path,
        action="append",
        default=[],
        help="Destination world root. May be supplied multiple times.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    worldRoots = args.world_root or [
        Path("assets_dev/worlds/mm9"),
        Path("assets_editor_dev/worlds/mm9"),
    ]

    for sourceRel, destinationRel in STATIC_ASSET_MAPPINGS:
        sourceRoot = args.extracted_root / sourceRel
        if not sourceRoot.exists():
            raise FileNotFoundError(sourceRoot)

        for worldRoot in worldRoots:
            destinationRoot = worldRoot / destinationRel
            copied, overwritten = syncTree(sourceRoot, destinationRoot, args.dry_run)
            action = "would copy" if args.dry_run else "copied"
            print(f"{action} {copied} files to {destinationRoot} ({overwritten} existing)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
