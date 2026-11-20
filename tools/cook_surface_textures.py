#!/usr/bin/env python3
"""Cook MM6-MM9 world surface textures (BLV/ODM face textures) into GPU block-compressed .oytex files.

Sources live in assets_source/worlds/<world>/textures_x2 and textures_x4 (Git LFS; tex.py install writes the x4
masters there). Each profile cooks one tier into the runtime tree:

  desktop  assets_source/worlds/<w>/textures_x4/*.png -> assets_dev/worlds/<w>/textures_x4/<stem>.oytex   BC7
  android  assets_source/worlds/<w>/textures_x2/*.png -> assets_cooked/android/worlds/<w>/textures_x2/... ASTC 4x4

Face textures with an x4 master but no x2 file (terrain tiles that also cover BModel faces, sky ceilings) cook for
Android from the x4 master without its largest level, which is the runtime's own half-size mip; packages carry no x1
or x4 surface textures to fall back to, so such faces would not draw at all.

MM9 (NATIVE_WORLDS) also cooks its native-only faces: a face texture with no x4 master draws its 1x native (fire,
slime, sky ceilings, invisible helpers, animated frame groups, ...), so each x1 source without an x4 master cooks at
its own size, in the profile's codec, into the x1 folder:

  desktop  assets_source/worlds/mm9/textures/<stem>.bmp -> assets_dev/worlds/mm9/textures/<stem>.oytex              BC7
  android  the same                                     -> assets_cooked/android/worlds/mm9/textures/<stem>.oytex  ASTC

The x1 tier's scale comes from its folder (assetScaleTierFromResolvedPath), so the faces keep their logical size, and
the runtime takes the x1 file when the preferred tier has none. MM6-MM8 have an x4 master for every face they draw;
their x1-only sources (terrain tiles, unused bitmaps) stay uncooked.

The map loader prefers the cooked file in each scale tier (Engine::findCookedOrImageAssetPath) and uploads its blocks
and stored mip chain directly, so nothing is decoded, keyed or filtered at load. The original x1 BMPs are source art
too, in assets_source/worlds/<w>/textures: the lighting bake reads them (bounce colour, cutout shadows) and records
their hashes, which tools/lighting/stale_bakes.py and the development stale check resolve there. Only the .act
palettes (and MM9's cooked x1 files) stay in assets_dev/worlds/<w>/textures. A few images read as images rather than
surfaces stay beside the cooked files in assets_dev (the blood splat decal, hwsplat04.png).

The cook reproduces the BModel upload exactly: the magenta key becomes transparent (MapAssetLoader's decode), mips are
the runtime's box filter on raw texel values (prepareBgraMipChain, no sRGB, no cutout coverage), and the texture keeps
its size. BC7 measured 45.9 dB on x4 masters (BC1 35.1, visibly blockier); ASTC 4x4 (medium) 46.7 dB on x2 sources.
The source's alpha use and mean colour go into the header (water tint, transparent batching).
Face textures that are liquids (engine/liquids/liquids.yml) are not cooked: the liquid shader draws them from their
liquid's colour, so the runtime never loads their art.

  tools/cook_surface_textures.py [--profile desktop|android]   cook new and changed textures, remove orphans
  tools/cook_surface_textures.py --plan                         what would be cooked; writes nothing
  tools/cook_surface_textures.py --verify                       fail on a missing, stale or orphaned cooked file
  tools/cook_surface_textures.py --force                        re-cook everything
  The desktop profile also cooks and verifies the surface material maps (tools/surface_materials.py).
  options: --only 'mm6/t1*'  --sources ROOT (default assets_source)  --output ROOT (default per profile)
           --world NAME (repeatable; default mm6 to mm9: a staged world such as hesper names itself)

A world whose source folder is missing (sources not pulled) is skipped: its cooked files are neither re-cooked nor
removed. Receipts: assets_source/.cook-cache/surface_textures/<output root path>.json. A texture re-cooks when its
source or the cook settings change, or COOK_REVISION is bumped; unchanged files are recognised by size and
modification time, so the incremental desktop cook the build runs (target openyamm_cook_surface_textures) costs about
a second. Android cooks on demand (tools/cook_android.sh).
"""
import argparse
import fcntl
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile

from PIL import Image
import yaml

import surface_materials

ROOT = Path(__file__).resolve().parent.parent
WORLDS = ("mm6", "mm7", "mm8", "mm9")
SOURCE_SUFFIXES = (".png", ".bmp", ".pcx")  # the runtime's candidate order (findImageAssetPath)
PROFILES = {
    # profile: (tier folder, codec, default output root)
    "desktop": ("textures_x4", "bc7", "assets_dev"),
    "android": ("textures_x2", "astc_4x4", "assets_cooked/android"),
}
# Cooker job columns after input/output and codec: semantic, alpha cutoff, mips, max size, linear channels; the
# source hash and the job kind follow per texture.
FULL_SIZE = 8192
# Worlds whose faces without an x4 master draw their 1x native, which therefore cooks in the x1 folder.
NATIVE_WORLDS = ("mm9",)
NATIVE_TIER = "textures"


def job_settings(max_size):
    return ("linear", "0", "1", str(max_size), "0")
# Bump when the cooker's output for the same settings changes (encoder, mip filter, decode or container); the
# cooker binary itself relinks with every engine change, so it cannot identify the cook.
COOK_REVISION = 2
HEADER_BYTES = 120
# engine/render/CookedTexture.h CookedTextureVersion.
COOKED_TEXTURE_VERSION = 3
HEADER_FIELDS = HEADER_BYTES // 8
MAGIC = 0x313030584554594F
LIQUIDS = ROOT / "assets_dev/engine/liquids/liquids.yml"


def liquid_face_matcher():
    """Whether a face texture name is a liquid (LiquidTable::findMatch for faces)."""
    names, prefixes = set(), []
    for liquid in yaml.safe_load(LIQUIDS.read_text())["liquids"]:
        if "face" in liquid["applies_to"]:
            names.update(name.lower() for name in liquid["match"].get("texture_names", []))
            prefixes += [prefix.lower() for prefix in liquid["match"].get("texture_prefixes", [])]
    return lambda stem: stem.lower() in names or stem.lower().startswith(tuple(prefixes))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def header_source_hash(path):
    data = path.read_bytes()[:HEADER_BYTES]
    if len(data) < HEADER_BYTES:
        raise ValueError("truncated header")
    fields = struct.unpack(f"<{HEADER_FIELDS}Q", data)
    if fields[0] != MAGIC or fields[1] != COOKED_TEXTURE_VERSION:
        raise ValueError(f"not a version {COOKED_TEXTURE_VERSION} cooked texture (version {fields[1]})")
    return fields[8]


def file_stat(path):
    stat = path.stat()
    return [stat.st_size, stat.st_mtime_ns]


def sources_by_stem(source_dir, is_liquid):
    """{lower-case stem: preferred source} in one tier folder (empty when it is missing)."""
    by_stem = {}
    if source_dir.is_dir():
        for path in source_dir.iterdir():
            if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES and not is_liquid(path.stem):
                by_stem.setdefault(path.stem.lower(), []).append(path)
    return {stem: min(paths, key=lambda path: SOURCE_SUFFIXES.index(path.suffix.lower()))
            for stem, paths in by_stem.items()}


def output_dirs(output_root, world, profile):
    """The folders whose cooked files the surface cook owns for one world: the profile's tier, and the x1 folder of
    NATIVE_WORLDS."""
    dirs = [output_root / "worlds" / world / PROFILES[profile][0]]
    if world in NATIVE_WORLDS:
        dirs.append(output_root / "worlds" / world / NATIVE_TIER)
    return dirs


def world_pairs(sources_root, output_root, profile, only, worlds):
    """{world: {cooked path: (source path, max size)}} for worlds whose source folder exists. Android adds the x4
    masters of face textures without an x2 file, capped at half their size. NATIVE_WORLDS add their x1 sources
    without an x4 master, cooked into the x1 folder."""
    tier = PROFILES[profile][0]
    is_liquid = liquid_face_matcher()
    result = {}
    for world in worlds:
        source_dir = sources_root / "worlds" / world / tier
        if not source_dir.is_dir():
            continue
        sources = {stem: (source, FULL_SIZE) for stem, source in sources_by_stem(source_dir, is_liquid).items()}
        if profile == "android":
            masters = sources_by_stem(sources_root / "worlds" / world / "textures_x4", is_liquid)
            for stem in masters.keys() - sources.keys():
                with Image.open(masters[stem]) as image:
                    sources[stem] = (masters[stem], max(image.size) // 2)
        pairs = {}
        for source, max_size in sources.values():
            if only and not any(fnmatch.fnmatch(f"{world}/{source.stem.lower()}", pattern) for pattern in only):
                continue
            pairs[output_root / "worlds" / world / tier / (source.stem + ".oytex")] = (source, max_size)
        if world in NATIVE_WORLDS:
            natives = sources_by_stem(sources_root / "worlds" / world / NATIVE_TIER, is_liquid)
            masters = sources_by_stem(sources_root / "worlds" / world / "textures_x4", is_liquid)
            for stem in sorted(natives.keys() - masters.keys()):
                if only and not any(fnmatch.fnmatch(f"{world}/{stem}", pattern) for pattern in only):
                    continue
                pairs[output_root / "worlds" / world / NATIVE_TIER / (natives[stem].stem + ".oytex")] = (
                    natives[stem], FULL_SIZE)
        result[world] = pairs
    return result


def receipts_path(output_root):
    try:
        name = output_root.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        name = output_root.resolve().as_posix().lstrip("/")
    return ROOT / "assets_source/.cook-cache/surface_textures" / (name.replace("/", "__") + ".json")


def save_receipts(output_root, receipts):
    path = receipts_path(output_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipts, indent=1, sort_keys=True) + "\n")
    os.replace(temporary, path)


def cook(sources_root, output_root, profile, cooker, only, force, plan, world_names):
    tier, codec, _ = PROFILES[profile]
    if not cooker.is_file() and not plan:
        raise SystemExit(f"Missing cooker {cooker}; cmake --build build --target openyamm_model_texture_cook")
    path = receipts_path(output_root)
    receipts = {} if force or not path.is_file() else json.loads(path.read_text())
    pending, current, orphans = [], 0, []
    worlds = world_pairs(sources_root, output_root, profile, only, world_names)
    for world in world_names:
        if world not in worlds:
            print(f"{world}: no sources in {sources_root / 'worlds' / world / tier}; its cooked files are kept",
                  flush=True)
    for world, pairs in worlds.items():
        for target, (source, max_size) in sorted(pairs.items()):
            current += 1
            key = target.relative_to(output_root).as_posix()
            receipt = receipts.get(key)
            settings_text = "\t".join((codec,) + job_settings(max_size) + ("surface",))
            settings = {"source": source.name, "settings": settings_text, "revision": COOK_REVISION}
            if receipt and target.is_file() and {k: receipt["inputs"].get(k) for k in settings} == settings:
                # Unchanged files are recognised by size and modification time; otherwise by content.
                if receipt.get("stat") == [file_stat(source), file_stat(target)]:
                    continue
                source_hash = sha256(source)
                if receipt["inputs"]["source_sha256"] == source_hash and receipt["output"] == sha256(target):
                    receipt["stat"] = [file_stat(source), file_stat(target)]
                    continue
            else:
                source_hash = sha256(source)
            pending.append((source, target, max_size, source_hash, {**settings, "source_sha256": source_hash}))
        for output_dir in output_dirs(output_root, world, profile) if not only else ():
            if output_dir.is_dir():
                orphans += sorted(set(output_dir.glob("*.oytex")) - set(pairs))
    print(f"{profile}: {current} surface textures, {len(pending)} to cook, {len(orphans)} orphaned cooked files",
          flush=True)
    if plan:
        for source, target, _, _, _ in pending[:20]:
            print(f"  cook {source.relative_to(sources_root)} -> {target.relative_to(output_root)}")
        for orphan in orphans[:20]:
            print(f"  remove {orphan.relative_to(output_root)}")
        return
    for orphan in orphans:
        orphan.unlink()
        receipts.pop(orphan.relative_to(output_root).as_posix(), None)
    save_receipts(output_root, receipts)
    failures = 0
    batch_size = 512
    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        with tempfile.TemporaryDirectory() as scratch:
            job_file = Path(scratch) / "jobs.tsv"
            job_file.write_text("".join("\t".join((str(source), str(target), codec, *job_settings(max_size),
                                                    source_hash[:16], "surface")) + "\n"
                                        for source, target, max_size, source_hash, _ in batch))
            result = subprocess.run([str(cooker), str(job_file)], text=True, capture_output=True)
        print(result.stderr, end="")
        done = {Path(line.split("\t")[1]) for line in result.stdout.splitlines() if line.startswith("cooked\t")}
        for source, target, _, _, inputs in batch:
            if target in done:
                receipts[target.relative_to(output_root).as_posix()] = {
                    "inputs": inputs, "output": sha256(target), "stat": [file_stat(source), file_stat(target)]}
            else:
                failures += 1
        save_receipts(output_root, receipts)
        print(f"  cooked {min(start + batch_size, len(pending))}/{len(pending)}", flush=True)
    if failures:
        raise SystemExit(f"{failures} of {len(pending)} surface textures failed to cook")


def verify(sources_root, output_root, profile, cooker, only, world_names, require_sources=False):
    """Every source has a cooked file made from its current bytes, in the profile's codec, and none is orphaned."""
    tier, codec, _ = PROFILES[profile]
    worlds = world_pairs(sources_root, output_root, profile, only, world_names)
    problems = []
    if require_sources:
        problems += [f"no sources for {world} ({sources_root / 'worlds' / world / tier})"
                     for world in world_names if world not in worlds]
    paths = []
    for world, pairs in worlds.items():
        for target, (source, _) in sorted(pairs.items()):
            if not target.is_file():
                problems.append(f"missing {target.relative_to(output_root)}")
                continue
            paths.append(target)
            try:
                if header_source_hash(target) != int(sha256(source)[:16], 16):
                    problems.append(f"stale {target.relative_to(output_root)} (source changed)")
            except ValueError as error:
                problems.append(f"invalid {target.relative_to(output_root)}: {error}")
        for output_dir in output_dirs(output_root, world, profile) if not only else ():
            if output_dir.is_dir():
                problems += [f"orphaned {path.relative_to(output_root)}"
                             for path in sorted(set(output_dir.glob("*.oytex")) - set(pairs))]
    for start in range(0, len(paths), 256):
        result = subprocess.run([str(cooker), "--verify", *map(str, paths[start:start + 256])],
                                text=True, capture_output=True)
        problems += [line for line in result.stderr.splitlines() if line.strip()]
        for line in result.stdout.splitlines():
            name, cooked_codec, semantic, cutoff, *_rest = line.split("\t")
            if (cooked_codec, semantic, cutoff) != (codec, "linear", "0") or _rest[-1] == "-":
                problems.append(f"{name}: cooked as {cooked_codec}/{semantic}/cutoff {cutoff}, not a {profile} "
                                f"surface texture")
    for problem in problems[:40]:
        print(problem)
    print(f"{profile}: {len(paths)} cooked surface textures checked, {len(problems)} problems")
    if profile == "desktop":
        problems += surface_materials.verify(sources_root, output_root, world_names)
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", choices=sorted(PROFILES), default="desktop")
    parser.add_argument("--sources", type=Path, default=ROOT / "assets_source")
    parser.add_argument("--output", type=Path, help="runtime root (default assets_dev / assets_cooked/android)")
    parser.add_argument("--cooker", type=Path, default=ROOT / "build/game/openyamm_model_texture_cook")
    parser.add_argument("--only", action="append", help="glob on '<world>/<stem>' (repeatable)")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--world", action="append", help="world to cook (repeatable; default mm6 to mm9)")
    args = parser.parse_args()
    world_names = tuple(args.world or WORLDS)
    output = args.output or ROOT / PROFILES[args.profile][2]
    if args.verify:
        if verify(args.sources, output, args.profile, args.cooker, args.only, world_names):
            raise SystemExit("run tools/cook_surface_textures.py --profile " + args.profile)
        return
    # Builds of several sessions may run the cook at once: one at a time per output root.
    lock_path = receipts_path(output).with_suffix(".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cook(args.sources, output, args.profile, args.cooker, args.only, args.force, args.plan, world_names)
        if args.profile == "desktop":
            surface_materials.cook(args.sources, output, args.cooker, args.only, args.force, args.plan, world_names)


if __name__ == "__main__":
    main()
