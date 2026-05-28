#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REALESRGAN_BIN = SCRIPT_DIR / "realesrgan-ncnn-vulkan"
DEFAULT_POLICY = Path("assets_dev/worlds/mm9/upscaling/mm9_dtx_upscale_policies.yml")

YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        loaded = yaml.load(stream, Loader=YAML_LOADER)
    return loaded if isinstance(loaded, dict) else {}


def is_ambiguous(source: str, manifest: dict[str, Any]) -> bool:
    ambiguous = manifest.get("ambiguous")
    return isinstance(ambiguous, dict) and source in ambiguous


def selected_entries(args: argparse.Namespace, manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    entries = manifest.get("entries")
    if not isinstance(entries, dict):
        return []

    requested_policies = set(args.only_policy.split(",")) if args.only_policy else set()
    requested_sources = set(args.only_source.split(",")) if args.only_source else set()

    result: list[tuple[str, dict[str, Any]]] = []
    for source, entry in sorted(entries.items()):
        if not isinstance(entry, dict):
            continue
        policy = str(entry.get("policy") or "")
        if requested_policies and policy not in requested_policies:
            continue
        if requested_sources and source not in requested_sources:
            continue
        if is_ambiguous(source, manifest) and not args.include_ambiguous:
            continue
        confidence = float(entry.get("confidence") or 0.0)
        if confidence < args.min_confidence and not args.include_ambiguous:
            continue
        result.append((source, entry))
        if args.limit is not None and len(result) >= args.limit:
            break
    return result


def output_path_for(source: str, entry: dict[str, Any], output_root: Path | None, scale: int) -> Path:
    configured = Path(str(entry.get("output") or ""))
    if output_root is None:
        return configured

    source_path = Path(source)
    parts = [part.lower() for part in source_path.parts]
    if "skins" in parts:
        indexes = [index for index, part in enumerate(parts) if part == "skins"]
        if len(indexes) >= 2:
            relative = Path(*source_path.parts[indexes[1] + 1:])
        else:
            relative = Path(*source_path.parts[indexes[0] + 1:])
        base = output_root / "skins" / relative
    elif "textures" in parts:
        indexes = [index for index, part in enumerate(parts) if part == "textures"]
        if len(indexes) >= 2:
            relative = Path(*source_path.parts[indexes[1] + 1:])
        else:
            relative = Path(*source_path.parts[indexes[0] + 1:])
        base = output_root / "textures" / relative
    else:
        base = output_root / source_path.name
    return base.with_name(f"{base.stem}_x{scale}{base.suffix}")


def command_for_entry(args: argparse.Namespace, source: str, entry: dict[str, Any], scale: int) -> list[str]:
    output = output_path_for(source, entry, args.output_root, scale)
    policy = str(entry.get("policy") or "object")
    command = [
        sys.executable,
        (SCRIPT_DIR / "upscale_mm9_dtx.py").as_posix(),
        source,
        "--scale",
        str(scale),
        "--type",
        policy,
        "--output",
        output.as_posix(),
        "--format",
        args.format,
        "--mip-policy",
        args.mip_policy,
        "--realesrgan-bin",
        args.realesrgan_bin,
        "--model",
        args.model,
    ]
    if args.force:
        command.append("--force")
    if args.no_sharpen:
        command.append("--no-sharpen")
    if args.no_sidecar:
        command.append("--no-sidecar")
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch upscale MM9 DTX files from a policy manifest.")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--output-root", type=Path, help="Override output root from the policy manifest.")
    parser.add_argument("--scale", type=int, help="Override scale from the policy manifest.")
    parser.add_argument("--only-policy", help="Comma-separated policy filter, e.g. actor,object,surface-tile.")
    parser.add_argument("--only-source", help="Comma-separated exact source DTX paths from the policy manifest.")
    parser.add_argument("--include-ambiguous", action="store_true")
    parser.add_argument("--min-confidence", type=float, default=0.67)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--format", choices=("auto", "preserve", "rgba32"), default="auto")
    parser.add_argument("--mip-policy", choices=("full", "preserve"), default="full")
    parser.add_argument(
        "--realesrgan-bin",
        default=os.environ.get("REALESRGAN_BIN", DEFAULT_REALESRGAN_BIN.as_posix()),
    )
    parser.add_argument("--model", default=os.environ.get("MODEL", "realesrgan-x4plus"))
    parser.add_argument("--no-sharpen", action="store_true")
    parser.add_argument("--no-sidecar", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = load_yaml(args.policy)
    scale = int(args.scale or manifest.get("scale") or 4)
    entries = selected_entries(args, manifest)

    print(f"policy: {args.policy}")
    print(f"selected: {len(entries)}")
    if args.dry_run:
        for source, entry in entries:
            output = output_path_for(source, entry, args.output_root, scale)
            print(f"{entry.get('policy')} {entry.get('confidence')} {source} -> {output}")
        return

    failures = 0
    for index, (source, entry) in enumerate(entries, 1):
        command = command_for_entry(args, source, entry, scale)
        print(f"[{index}/{len(entries)}] {source}")
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as error:
            failures += 1
            print(f"failed: {source}: {error}", file=sys.stderr)
            if not args.continue_on_error:
                raise

    if failures:
        raise RuntimeError(f"{failures} DTX upscales failed")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
