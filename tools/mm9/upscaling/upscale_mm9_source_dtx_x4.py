#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REALESRGAN_BIN = SCRIPT_DIR / "realesrgan-ncnn-vulkan"

ROOTS = {
    "textures": "textures_x4",
    "sprite_textures": "sprite_textures_x4",
    "skins": "skins_x4",
}

DEFAULT_POLICIES = {
    "textures": "texture",
    "sprite_textures": "default",
    "skins": "actor",
}


def dtx_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".dtx"),
        key=lambda path: path.as_posix().lower(),
    )


def output_path(source_root: Path, source_path: Path, destination_root: Path) -> Path:
    return destination_root / source_path.relative_to(source_root)


def selected_roots(args: argparse.Namespace) -> list[str]:
    if not args.only_root:
        return list(ROOTS)
    return args.only_root


def policy_for(root_name: str, args: argparse.Namespace) -> str:
    if root_name == "textures":
        return args.textures_policy
    if root_name == "sprite_textures":
        return args.sprite_policy
    if root_name == "skins":
        return args.skins_policy
    raise ValueError(root_name)


def build_command(args: argparse.Namespace, source_path: Path, output: Path, policy: str) -> list[str]:
    command = [
        sys.executable,
        (SCRIPT_DIR / "upscale_mm9_dtx.py").as_posix(),
        source_path.as_posix(),
        "--scale",
        str(args.scale),
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
    if not args.sidecars:
        command.append("--no-sidecar")
    return command


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Upscale assets_dev/worlds/mm9/source/{textures,sprite_textures,skins} DTX files to same-named "
            "x4 destination roots."
        ),
    )
    parser.add_argument("--source-root", type=Path, default=Path("assets_dev/worlds/mm9/source"))
    parser.add_argument("--scale", type=int, choices=(2, 3, 4), default=4)
    parser.add_argument("--only-root", action="append", choices=sorted(ROOTS), help="Limit to one source root.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--format", choices=("auto", "preserve", "rgba32"), default="auto")
    parser.add_argument("--mip-policy", choices=("full", "preserve"), default="full")
    parser.add_argument("--textures-policy", choices=("default", "texture", "surface-tile"), default="texture")
    parser.add_argument(
        "--sprite-policy",
        choices=("default", "object", "actor", "texture", "surface-tile"),
        default="default",
    )
    parser.add_argument("--skins-policy", choices=("default", "object", "actor"), default="actor")
    parser.add_argument(
        "--realesrgan-bin",
        default=os.environ.get("REALESRGAN_BIN", DEFAULT_REALESRGAN_BIN.as_posix()),
    )
    parser.add_argument("--model", default=os.environ.get("MODEL", "realesrgan-x4plus"))
    parser.add_argument("--no-sharpen", action="store_true")
    parser.add_argument("--sidecars", action="store_true", help="Write <file>.dtx.upscale.yml sidecars.")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validate_mm9_dtx_tree.py --check-counterparts after successful upscaling.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    entries: list[tuple[Path, Path, str]] = []

    for root_name in selected_roots(args):
        source_root = args.source_root / root_name
        destination_root = args.source_root / ROOTS[root_name]
        policy = policy_for(root_name, args)
        for source_path in dtx_files(source_root):
            entries.append((source_path, output_path(source_root, source_path, destination_root), policy))
            if args.limit is not None and len(entries) >= args.limit:
                break
        if args.limit is not None and len(entries) >= args.limit:
            break

    print(f"selected: {len(entries)}")
    if args.dry_run:
        for source_path, destination_path, policy in entries:
            print(f"{policy} {source_path} -> {destination_path}")
        return

    failures = 0
    for index, (source_path, destination_path, policy) in enumerate(entries, 1):
        print(f"[{index}/{len(entries)}] {source_path} -> {destination_path}")
        try:
            subprocess.run(build_command(args, source_path, destination_path, policy), check=True)
        except subprocess.CalledProcessError as error:
            failures += 1
            print(f"failed: {source_path}: {error}", file=sys.stderr)
            if not args.continue_on_error:
                raise

    if failures:
        raise RuntimeError(f"{failures} DTX upscales failed")

    if args.validate:
        subprocess.run(
            [
                sys.executable,
                (SCRIPT_DIR / "validate_mm9_dtx_tree.py").as_posix(),
                "--source-root",
                args.source_root.as_posix(),
                "--scale",
                str(args.scale),
                "--check-counterparts",
                "--decode",
            ],
            check=True,
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
