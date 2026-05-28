#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def unquote_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return value


def read_manifest(path: Path) -> tuple[Path, Path, list[dict[str, str]]]:
    source_root: Path | None = None
    output_root: Path | None = None
    maps: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_maps = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "maps:":
            in_maps = True
            continue
        if not in_maps:
            if stripped.startswith("source_root:"):
                source_root = Path(unquote_yaml_scalar(stripped.split(":", 1)[1]))
            elif stripped.startswith("output_root:"):
                output_root = Path(unquote_yaml_scalar(stripped.split(":", 1)[1]))
            continue
        if stripped.startswith("- "):
            if current is not None:
                maps.append(current)
            current = {}
            stripped = stripped[2:].strip()
        if ":" not in stripped or current is None:
            continue
        key, value = stripped.split(":", 1)
        current[key.strip()] = unquote_yaml_scalar(value)

    if current is not None:
        maps.append(current)
    if source_root is None:
        raise ValueError(f"{path}: missing source_root")
    if output_root is None:
        raise ValueError(f"{path}: missing output_root")
    return source_root, output_root, maps


def run_command(args: list[str], keep_going: bool) -> bool:
    print("+ " + " ".join(args), flush=True)
    result = subprocess.run(args)
    if result.returncode == 0:
        return True
    if keep_going:
        print(f"warning: command failed with exit code {result.returncode}", file=sys.stderr, flush=True)
        return False
    raise subprocess.CalledProcessError(result.returncode, args)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate MM9 ODM/BLV imports from the MM9 map import manifest.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("assets_dev/worlds/mm9/maps/mm9_map_import.yml"),
    )
    parser.add_argument("--compile-tool", type=Path, default=Path("build/tools/mm9_compile_indoor_source"))
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--only-format", choices=("odm", "blv"))
    parser.add_argument("--only-map", action="append", default=[])
    parser.add_argument("--keep-going", action="store_true")
    args = parser.parse_args()

    source_root, output_root, maps = read_manifest(args.manifest)
    requested_maps = {value.lower() for value in args.only_map}
    selected_maps = [
        entry
        for entry in maps
        if (args.only_format is None or entry.get("target_format") == args.only_format)
        and (not requested_maps or entry.get("id", "").lower() in requested_maps)
    ]

    generated = 0
    failed = 0
    for entry in selected_maps:
        map_id = entry["id"]
        source_dat = source_root / entry["source_dat"]
        target_format = entry["target_format"]
        if target_format == "odm":
            command = [
                args.python,
                "tools/mm9_import_discovery/transcode_mm9_dat_to_odm.py",
                "--dat",
                str(source_dat),
                "--output-dir",
                str(output_root),
                "--name",
                map_id,
            ]
        elif target_format == "blv":
            command = [
                args.python,
                "tools/mm9_import_discovery/transcode_mm9_dat_to_blv.py",
                "--dat",
                str(source_dat),
                "--output-dir",
                str(output_root),
                "--name",
                map_id,
                "--compile-tool",
                str(args.compile_tool),
            ]
        else:
            raise ValueError(f"unknown target_format for {map_id}: {target_format}")

        if run_command(command, args.keep_going):
            generated += 1
        else:
            failed += 1

    print(f"generated={generated} failed={failed} selected={len(selected_maps)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
