#!/usr/bin/env python3
"""Cook HUD art into GPU block-compressed .oytex files, one set per profile.

| Profile | Output | Codec |
| desktop | assets_dev/engine/icons_x2 | BC7 |
| android | assets_cooked/android/engine/icons_x2 | ASTC 4x4 |

- Obsidian UI art: sources assets_source/engine/icons_x2/obsidian_*.png; one cooked file each, with mips (the
  UiIllustration profile). About 67 of them are loaded at the first gameplay map load of a session; cooked, nothing
  is decoded or mip-filtered there. Only the HUD uses this art, so assets_dev holds no PNG of it.
- Portrait face sets (pc01-01..pc01-56, girla01..girla56, ...): sources assets_dev/engine/icons_x2, which keeps the
  PNGs because menus and character creation read them. One atlas per set, faces_<set>.oytex, with faces_<set>.yml
  (in assets_dev, shared by both profiles) listing its frames. The HUD loads a whole set (a party member's portrait)
  on its first frame and cuts each frame out of the atlas blocks as its own texture, without decoding.

Both are of the HUD's own decode and edge bleed (GameplayHudCommon), padded by edge replication to whole 4x4 blocks
(the mipped Obsidian art to power-of-two sides: NVIDIA's OpenGL 3.3 driver samples a mipped non-power-of-two block
texture as black); the header records the content size and the HUD scales UVs to it. Without assets_source (a
checkout without the submodule) the Obsidian files are kept as committed and only the face sets are cooked.

  tools/cook_ui_textures.py [--profile android]   cook new and changed art, remove orphans
  tools/cook_ui_textures.py --plan                what would be cooked; writes nothing
  tools/cook_ui_textures.py --verify              fail on a missing, stale or orphaned cooked file
  tools/cook_ui_textures.py --force               re-cook everything
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import yaml
from PIL import Image

from cook_surface_textures import header_source_hash, file_stat, sha256

ROOT = Path(__file__).resolve().parent.parent
PROFILES = {"desktop": ("bc7", ROOT / "assets_dev"), "android": ("astc_4x4", ROOT / "assets_cooked/android")}
# Bump when the cooker's output for the same inputs changes (see cook_surface_textures.COOK_REVISION).
COOK_REVISION = 2
FACE_COLUMNS = 8
FACE_FRAME = re.compile(r"^([a-z]+(?:\d\d-)?)(\d\d)$")
MIN_FACE_FRAMES = 40


def face_sets(icons):
    """{set id: [frame paths in frame order]} for contiguous portrait sets of identical size."""
    groups = {}
    for path in icons.glob("*.png"):
        match = FACE_FRAME.match(path.stem.lower())
        if match:
            groups.setdefault(match.group(1), {})[int(match.group(2))] = path
    sets = {}
    for prefix, frames in groups.items():
        if len(frames) < MIN_FACE_FRAMES or sorted(frames) != list(range(1, len(frames) + 1)):
            continue
        ordered = [frames[index] for index in range(1, len(frames) + 1)]
        if len({Image.open(path).size for path in ordered}) == 1:
            sets[prefix.rstrip("-")] = ordered
    return sets


class Roots:
    """Where one profile's sources and outputs are: obsidian is None when assets_source is not checked out."""
    def __init__(self, assets, sources, output, profile):
        self.faces = assets / "engine/icons_x2"
        obsidian = sources / "engine/icons_x2"
        self.obsidian = obsidian if obsidian.is_dir() else None
        self.output = output
        self.icons = output / "engine/icons_x2"
        # The face set manifests live in assets_dev beside their sources; the android overlay holds only blocks.
        self.manifests = profile == "desktop"
        self.codec = PROFILES[profile][0]


def units(roots):
    """Cooked outputs: (output path, kind, sources, manifest or None)."""
    result = []
    for path in sorted(roots.obsidian.glob("obsidian_*.png")) if roots.obsidian else []:
        result.append((roots.icons / (path.stem + ".oytex"), "ui", [path], None))
    for name, frames in sorted(face_sets(roots.faces).items()):
        width, height = Image.open(frames[0]).size
        manifest = {"schema_version": 1, "frame_width": width, "frame_height": height, "columns": FACE_COLUMNS,
                    "frames": [path.stem.lower() for path in frames]}
        result.append((roots.icons / f"faces_{name}.oytex", "ui_atlas", frames, manifest))
    return result


def manifest_path(output):
    return output.with_suffix(".yml")


def managed_files(roots):
    """Cooked files this run owns; the Obsidian ones only when their sources are present."""
    icons = roots.icons
    managed = set(icons.glob("faces_*.oytex"))
    if roots.manifests:
        managed |= set(icons.glob("faces_*.yml"))
    if roots.obsidian:
        managed |= set(icons.glob("obsidian_*.oytex"))
    return managed


def combined_hash(sources):
    digest = hashlib.sha256()
    for source in sources:
        digest.update(sha256(source).encode())
    return digest.hexdigest()


def receipts_path(output):
    return ROOT / "assets_source/.cook-cache/ui_textures" / (
        output.resolve().as_posix().lstrip("/").replace("/", "__") + ".json")


def write_manifest(output, manifest):
    text = yaml.safe_dump(manifest, sort_keys=False, default_flow_style=None, width=120)
    path = manifest_path(output)
    if not path.is_file() or path.read_text() != text:
        temporary = path.with_suffix(".yml.tmp")
        temporary.write_text(text)
        os.replace(temporary, path)


def cook(roots, cooker, force, plan):
    receipts_file = receipts_path(roots.output)
    receipts = {} if force or not receipts_file.is_file() else json.loads(receipts_file.read_text())
    pending, expected = [], set()
    for output, kind, sources, manifest in units(roots):
        key = output.relative_to(roots.output).as_posix()
        expected.add(output)
        if manifest and roots.manifests:
            expected.add(manifest_path(output))
        settings = {"kind": kind, "codec": roots.codec, "revision": COOK_REVISION,
                    "sources": [source.name for source in sources]}
        stats = [file_stat(source) for source in sources]
        receipt = receipts.get(key)
        if receipt and output.is_file() and receipt["settings"] == settings:
            if receipt["stat"] == [stats, file_stat(output)]:
                continue
            if receipt["source_sha256"] == combined_hash(sources) and receipt["output"] == sha256(output):
                receipt["stat"] = [stats, file_stat(output)]
                continue
        pending.append((output, kind, sources, manifest, settings))
    orphans = sorted(managed_files(roots) - expected)
    print(f"{roots.output}: {len(expected)} cooked UI files, {len(pending)} to cook, {len(orphans)} orphaned"
          + ("" if roots.obsidian else " (no Obsidian sources: those cooked files are kept)"), flush=True)
    if plan:
        for output, kind, sources, _, _ in pending[:20]:
            print(f"  {kind} {output.relative_to(roots.output)} from {len(sources)} source(s)")
        return
    for path in orphans:
        path.unlink()
        receipts.pop(path.relative_to(roots.output).as_posix(), None)
    roots.icons.mkdir(parents=True, exist_ok=True)
    if pending:
        with tempfile.TemporaryDirectory() as scratch:
            lines = []
            for output, kind, sources, manifest, _ in pending:
                source_hash = combined_hash(sources)
                if kind == "ui_atlas":
                    listing = Path(scratch) / f"{output.stem}.frames"
                    listing.write_text(f"columns\t{FACE_COLUMNS}\n" + "".join(f"{path}\n" for path in sources))
                    source, mips = listing, "0"
                else:
                    source, mips = sources[0], "1"
                lines.append("\t".join((str(source), str(output), roots.codec, "linear", "0", mips, "8192", "0",
                                        source_hash[:16], kind)) + "\n")
            job_file = Path(scratch) / "jobs.tsv"
            job_file.write_text("".join(lines))
            result = subprocess.run([str(cooker), str(job_file)], text=True, capture_output=True)
        sys.stderr.write(result.stderr)
        done = {Path(line.split("\t")[1]) for line in result.stdout.splitlines() if line.startswith("cooked\t")}
        for output, kind, sources, manifest, settings in pending:
            if output not in done:
                continue
            if manifest and roots.manifests:
                write_manifest(output, manifest)
            receipts[output.relative_to(roots.output).as_posix()] = {
                "settings": settings, "source_sha256": combined_hash(sources), "output": sha256(output),
                "stat": [[file_stat(source) for source in sources], file_stat(output)]}
        failed = len(pending) - len(done)
    else:
        failed = 0
    receipts_file.parent.mkdir(parents=True, exist_ok=True)
    temporary = receipts_file.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipts, indent=1, sort_keys=True) + "\n")
    os.replace(temporary, receipts_file)
    if failed:
        raise SystemExit(f"{failed} of {len(pending)} UI textures failed to cook")


def verify(roots, profile):
    problems, expected = [], set()
    for output, kind, sources, manifest in units(roots):
        expected.add(output)
        if manifest and roots.manifests:
            expected.add(manifest_path(output))
            if not manifest_path(output).is_file() or yaml.safe_load(manifest_path(output).read_text()) != manifest:
                problems.append(f"stale {manifest_path(output).relative_to(roots.output)}")
        if not output.is_file():
            problems.append(f"missing {output.relative_to(roots.output)}")
            continue
        try:
            if header_source_hash(output) != int(combined_hash(sources)[:16], 16):
                problems.append(f"stale {output.relative_to(roots.output)}")
        except ValueError as error:
            problems.append(f"invalid {output.relative_to(roots.output)}: {error}")
    problems += [f"orphaned {path.relative_to(roots.output)}" for path in sorted(managed_files(roots) - expected)]
    for problem in problems[:40]:
        print(problem)
    print(f"{profile}: {len(expected)} cooked UI files, {len(problems)} problems"
          + ("" if roots.obsidian else " (no Obsidian sources: not checked)"))
    if problems:
        raise SystemExit(f"run tools/cook_ui_textures.py --profile {profile}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", choices=sorted(PROFILES), help="default: desktop; --verify alone checks both")
    parser.add_argument("--assets", type=Path, default=ROOT / "assets_dev", help="the runtime root (face sources)")
    parser.add_argument("--sources", type=Path, default=ROOT / "assets_source")
    parser.add_argument("--output", type=Path, help="default: --assets for desktop, assets_cooked/android")
    parser.add_argument("--cooker", type=Path, default=ROOT / "build/game/openyamm_model_texture_cook")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.verify and args.profile is None:
        failures = []
        for profile, (_, profile_output) in sorted(PROFILES.items()):
            output = args.assets if profile == "desktop" else profile_output
            try:
                verify(Roots(args.assets, args.sources, output, profile), profile)
            except SystemExit as failure:
                failures.append(str(failure))
        if failures:
            raise SystemExit("; ".join(failures))
        return
    args.profile = args.profile or "desktop"
    output = args.output or (args.assets if args.profile == "desktop" else PROFILES[args.profile][1])
    roots = Roots(args.assets, args.sources, output, args.profile)
    if args.verify:
        verify(roots, args.profile)
        return
    lock_path = receipts_path(output).with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cook(roots, args.cooker, args.force, args.plan)


if __name__ == "__main__":
    main()
