#!/usr/bin/env python3
"""Cook the Enhanced sky's textures into GPU block-compressed .oytex files, one per source image.

Sources are assets_source/engine/rendering/sky/**/*.png, written by tools/sky/generate_cloud_layers.py (cloud
layers), tools/sky/prepare_sky_art.py (horizon ring, night sky, moon) and tools/sky/derive_legacy_skies.py
(legacy/<name>.png colour layers). Each cooks to the same relative path:

  desktop  BC7       assets_dev/engine/rendering/sky/<name>.oytex
  android  ASTC 4x4  assets_cooked/android/engine/rendering/sky/<name>.oytex

Cloud layers keep the full mip chain the runtime built at load (linear box filter, no cutout). The panoramas, every
texture sky.yml names under `horizon_ring` or `stars` and the moon, have one level: they wrap at the atan2 seam,
where mip selection would draw a visible line. The cooked files are committed, so a checkout without assets_source
runs and packages; the packager swaps in the android files for that profile.

  tools/cook_sky_textures.py                    cook new and changed textures for both profiles, remove orphans
  tools/cook_sky_textures.py --profile desktop  one profile
  tools/cook_sky_textures.py --plan             what would be cooked; writes nothing
  tools/cook_sky_textures.py --verify           fail on a missing, invalid, stale (when the sources are present)
                                                or orphaned cooked texture
  tools/cook_sky_textures.py --force            re-cook everything
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import yaml

from cook_surface_textures import file_stat, header_source_hash, sha256

ROOT = Path(__file__).resolve().parent.parent
SKY = "engine/rendering/sky"
SOURCES = ROOT / "assets_source" / SKY
PROFILES = {"desktop": ("bc7", ROOT / "assets_dev"), "android": ("astc_4x4", ROOT / "assets_cooked/android")}
# SkyRenderer draws the moon disc from this texture unless a preset names its own (moon_texture).
MOON = "moon"
# Bump when the cooker's output for the same inputs changes.
COOK_REVISION = 1


def panoramas(assets):
    """Texture names drawn without mips: every horizon_ring or stars texture in sky.yml, and the moons."""
    names = {MOON}

    def visit(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("horizon_ring", "stars") and isinstance(value, dict) and value.get("texture"):
                    names.add(value["texture"])
                if key == "moon_texture" and isinstance(value, str):
                    names.add(value)
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(yaml.safe_load((assets / SKY / "sky.yml").read_text()))
    return names


def sources():
    """{texture name: source path}; the name is the path below the sky folder without its extension."""
    return {path.relative_to(SOURCES).with_suffix("").as_posix(): path
            for path in sorted(SOURCES.rglob("*.png"))} if SOURCES.is_dir() else {}


def managed(output_root):
    root = output_root / SKY
    return set(root.rglob("*.oytex")) if root.is_dir() else set()


def receipts_path(profile):
    return ROOT / "assets_source/.cook-cache/sky_textures" / f"{profile}.json"


def cook(profile, cooker, force, plan, assets):
    codec, output_root = PROFILES[profile]
    found = sources()
    if not found:
        print(f"{profile}: no sky sources in {SOURCES.relative_to(ROOT)}; cooked files kept as committed")
        return
    unmipped = panoramas(assets)
    receipts_file = receipts_path(profile)
    receipts = {} if force or not receipts_file.is_file() else json.loads(receipts_file.read_text())
    pending, expected = [], set()
    for name, source in found.items():
        output = output_root / SKY / f"{name}.oytex"
        expected.add(output)
        mips = name not in unmipped
        settings = {"codec": codec, "revision": COOK_REVISION, "mips": mips}
        receipt = receipts.get(name)
        if receipt and output.is_file() and receipt["settings"] == settings:
            if receipt["stat"] == [file_stat(source), file_stat(output)]:
                continue
            if receipt["source_sha256"] == sha256(source) and receipt["output"] == sha256(output):
                receipt["stat"] = [file_stat(source), file_stat(output)]
                continue
        pending.append((name, source, output, settings))
    orphans = sorted(managed(output_root) - expected)
    print(f"{profile}: {len(expected)} sky textures, {len(pending)} to cook, {len(orphans)} orphaned", flush=True)
    if plan:
        for name, _, output, settings in pending:
            print(f"  {output.relative_to(ROOT)}{'' if settings['mips'] else ' (one level)'}")
        return
    for path in orphans:
        path.unlink()
        receipts.pop(path.relative_to(output_root / SKY).with_suffix("").as_posix(), None)
    failed = 0
    if pending:
        lines = []
        for name, source, output, settings in pending:
            output.parent.mkdir(parents=True, exist_ok=True)
            lines.append("\t".join((str(source), str(output), codec, "linear", "0", "1" if settings["mips"] else "0",
                                    "8192", "0", sha256(source)[:16], "model")) + "\n")
        with tempfile.TemporaryDirectory() as scratch:
            job_file = Path(scratch) / "jobs.tsv"
            job_file.write_text("".join(lines))
            result = subprocess.run([str(cooker), str(job_file)], text=True, capture_output=True)
        sys.stderr.write(result.stderr)
        done = {Path(line.split("\t")[1]) for line in result.stdout.splitlines() if line.startswith("cooked\t")}
        for name, source, output, settings in pending:
            if output not in done:
                failed += 1
                continue
            output.chmod(0o644)
            receipts[name] = {"settings": settings, "source_sha256": sha256(source), "output": sha256(output),
                              "stat": [file_stat(source), file_stat(output)]}
    receipts_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = receipts_file.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipts, indent=1, sort_keys=True) + "\n")
    os.replace(temporary, receipts_file)
    if failed:
        raise SystemExit(f"{failed} of {len(pending)} sky textures failed to cook for {profile}")


def verify(profile):
    _, output_root = PROFILES[profile]
    found = sources()
    problems = []
    if found:
        expected = {output_root / SKY / f"{name}.oytex": source for name, source in found.items()}
        for output, source in expected.items():
            if not output.is_file():
                problems.append(f"missing {output.relative_to(ROOT)}")
                continue
            try:
                source_hash = header_source_hash(output)
            except ValueError as error:
                problems.append(f"invalid {output.relative_to(ROOT)}: {error}")
                continue
            if source_hash != int(sha256(source)[:16], 16):
                problems.append(f"stale {output.relative_to(ROOT)}")
        problems += [f"orphaned {path.relative_to(ROOT)}" for path in sorted(managed(output_root) - set(expected))]
    else:
        for path in sorted(managed(output_root)):
            try:
                header_source_hash(path)
            except ValueError as error:
                problems.append(f"invalid {path.relative_to(ROOT)}: {error}")
    for problem in problems[:40]:
        print(problem)
    note = "" if found else " (no local sources, freshness not checked)"
    print(f"{profile}: {len(managed(output_root))} sky textures, {len(problems)} problems{note}")
    return not problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", choices=sorted(PROFILES), action="append")
    parser.add_argument("--assets", type=Path, default=ROOT / "assets_dev", help="where sky.yml lives")
    parser.add_argument("--cooker", type=Path, default=ROOT / "build/game/openyamm_model_texture_cook")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    profiles = args.profile or sorted(PROFILES)
    if args.verify:
        if not all([verify(profile) for profile in profiles]):
            raise SystemExit("run tools/cook_sky_textures.py")
        return
    lock_path = receipts_path("lock").with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for profile in profiles:
            cook(profile, args.cooker, args.force, args.plan, args.assets)


if __name__ == "__main__":
    main()
