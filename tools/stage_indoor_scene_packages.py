#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage indoor BLV + generated .scene.yml packages into assets_editor_dev/Data/games"
    )
    parser.add_argument(
        "--source-dir",
        default="assets_dev/Data/games",
        help="directory containing source .blv/.dlv pairs",
    )
    parser.add_argument(
        "--output-dir",
        default="assets_editor_dev/Data/games",
        help="directory receiving staged .blv + .scene.yml files",
    )
    parser.add_argument(
        "--keep-existing-scene-yml",
        action="store_true",
        help="do not overwrite existing staged .scene.yml files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    source_dir = (repo_root / args.source_dir).resolve()
    output_dir = (repo_root / args.output_dir).resolve()
    export_script = repo_root / "tools" / "export_indoor_scene_yml.py"

    if not source_dir.is_dir():
        print(f"missing source directory: {source_dir}", file=sys.stderr)
        return 1

    if not export_script.is_file():
        print(f"missing export script: {export_script}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    dlv_paths = sorted(source_dir.glob("*.dlv"))

    if not dlv_paths:
        print(f"no .dlv files found in {source_dir}", file=sys.stderr)
        return 1

    staged_count = 0

    for dlv_path in dlv_paths:
        blv_path = dlv_path.with_suffix(".blv")

        if not blv_path.is_file():
            print(f"skipping {dlv_path.name}: missing {blv_path.name}", file=sys.stderr)
            continue

        output_scene_path = output_dir / f"{dlv_path.stem}.scene.yml"
        output_blv_path = output_dir / blv_path.name

        if not args.keep_existing_scene_yml or not output_scene_path.exists():
            subprocess.run(
                [
                    sys.executable,
                    str(export_script),
                    "--blv",
                    str(blv_path),
                    "--dlv",
                    str(dlv_path),
                    "--output",
                    str(output_scene_path),
                ],
                check=True,
            )

        shutil.copy2(blv_path, output_blv_path)
        staged_count += 1

    print(f"staged {staged_count} indoor map packages into {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
