#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml

from convert_abc_model import decode_dtx


def output_path_for(source: Path, source_root: Path, output_root: Path, suffix: str) -> Path:
    relative = source.relative_to(source_root)
    return output_root / Path(*[part.lower() for part in relative.with_suffix(suffix).parts])


def convert_skin(
    source: Path,
    source_root: Path,
    output_root: Path,
    preview_root: Path,
    force: bool,
) -> tuple[Path, Path, str | None]:
    output = output_path_for(source, source_root, output_root, ".dtx")
    preview = output_path_for(source, source_root, preview_root, ".png")
    if output.exists() and preview.exists() and not force:
        return output, preview, None
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)
        preview.parent.mkdir(parents=True, exist_ok=True)
        image = decode_dtx(source)
        image.save(preview)
        return output, preview, None
    except Exception as error:
        return output, preview, str(error)


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy MM9 SKINS/SKINS DTX files and generate PNG previews.")
    parser.add_argument("--source-root", type=Path, default=Path("mm9/extracted/SKINS/SKINS"))
    parser.add_argument("--output-root", type=Path, default=Path("assets_dev/worlds/mm9/skins"))
    parser.add_argument("--preview-root", type=Path, default=Path("assets_dev/worlds/mm9/skins_preview"))
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("assets_dev/worlds/mm9/import/skin_library_report.yml"),
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    sources = sorted(path for path in args.source_root.rglob("*.dtx") if path.is_file())
    entries = []
    converted = 0
    errors = 0
    for source in sources:
        output, preview, error = convert_skin(source, args.source_root, args.output_root, args.preview_root, args.force)
        if error is None:
            converted += 1
        else:
            errors += 1
        entries.append(
            {
                "source": str(source),
                "output": str(output),
                "preview": str(preview),
                "error": error,
            }
        )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        yaml.safe_dump(
            {
                "schema": "openyamm.mm9SkinLibraryReport.v1",
                "summary": {
                    "sources": len(sources),
                    "convertedOrPresent": converted,
                    "errors": errors,
                },
                "skins": entries,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    print(f"{len(sources)} skins, {converted} copied/previewed/present, {errors} errors")
    print(f"report: {args.report}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
