#!/usr/bin/env python3
"""Create the release content packs (index.json and packs/) with exactly one validated native sprite texture
profile; tools/packaging/packs.yml decides how packages split into packs."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import struct
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runtime_packs import PackConfig, build_packs, report, write_index, write_zip  # noqa: E402

# Bumped whenever a binary needs new content or content needs a new binary (packaging/UPDATER_PLAN.md, 7.1).
CONTENT_FORMAT = 1


def outdoor_lighting_dependencies(path):
    """(asset path, FNV-1a 64 content hash) of each source an installed outdoor .lighting file was baked from (its
    hash contract; none when the file records no dependency section), after validating the file's layout."""
    with path.open("rb") as stream:
        header = stream.read(96)
        if len(header) != 96 or header[:8] != b"OYMLIT1\0":
            raise ValueError(f"Invalid outdoor lighting header: {path}")
        version, header_size = struct.unpack_from("<II", header, 8)
        if version not in (3, 4, 5) or header_size != 96:
            raise ValueError(f"Unsupported outdoor lighting version: {path}")
        if not struct.unpack_from("<I", header, 76)[0] & 1:
            return []
        page_count = struct.unpack_from("<I", header, 32)[0]
        page_offset = struct.unpack_from("<I", header, 48)[0]
        pixel_end, file_size = struct.unpack_from("<II", header, 64)
        if page_offset != 96 or page_count > 65534 or file_size != path.stat().st_size:
            raise ValueError(f"Invalid outdoor lighting sections: {path}")
        for _ in range(page_count):
            record = stream.read(16)
            if len(record) != 16:
                raise ValueError(f"Truncated outdoor lighting page: {path}")
            _, _, offset, size = struct.unpack("<4I", record)
            if offset != pixel_end or size > file_size - offset:
                raise ValueError(f"Invalid outdoor lighting page: {path}")
            pixel_end += size
        stream.seek(pixel_end)
        extension = stream.read()
    counts_offset = 24 if version >= 4 else 0
    if len(extension) < counts_offset + 8:
        raise ValueError(f"Missing outdoor lighting dependencies: {path}")
    probes, dependencies = struct.unpack_from("<II", extension, counts_offset)
    found = []
    cursor = counts_offset + 8 + probes * (52 if version >= 4 else 36)
    for _ in range(dependencies):
        if cursor + 12 > len(extension):
            raise ValueError(f"Truncated outdoor lighting dependency: {path}")
        length, content_hash = struct.unpack_from("<IQ", extension, cursor)
        cursor += 12
        if not 0 < length <= 1024 or cursor + length > len(extension):
            raise ValueError(f"Invalid outdoor lighting dependency: {path}")
        found.append((extension[cursor:cursor + length].decode("utf-8"), content_hash))
        cursor += length
    if version >= 5:
        if cursor + 4 > len(extension):
            raise ValueError(f"Missing direct-sun lighting pages: {path}")
        direct_count = struct.unpack_from("<I", extension, cursor)[0]
        cursor += 4
        if direct_count * 2 != page_count:
            raise ValueError(f"Invalid direct-sun lighting page count: {path}")
        with path.open("rb") as stream:
            for index in range(direct_count):
                if cursor + 12 > len(extension):
                    raise ValueError(f"Truncated direct-sun lighting page: {path}")
                width, height, size = struct.unpack_from("<III", extension, cursor)
                cursor += 12
                stream.seek(page_offset + index * 32)
                dimensions = struct.unpack("<II", stream.read(8))
                if (width, height) != dimensions or size > len(extension) - cursor:
                    raise ValueError(f"Invalid direct-sun lighting page: {path}")
                cursor += size
    if cursor != len(extension):
        raise ValueError(f"Invalid outdoor lighting extension: {path}")
    return found


def indoor_lighting_dependencies(path):
    """(asset path, FNV-1a 64 content hash) of each source an installed indoor (BLV) .lighting file was baked from,
    after validating its layout (devdocs/INDOOR_BAKED_LIGHTING.md)."""
    data = path.read_bytes()
    if len(data) < 64 or data[:8] != b"OYILIT1\0":
        raise ValueError(f"Invalid indoor lighting header: {path}")
    version, header_size = struct.unpack_from("<II", data, 8)
    (face_count, sector_count, page_count, dependency_count, page_offset, face_offset, sector_offset,
     dependency_offset, pixel_offset, file_size) = struct.unpack_from("<10I", data, 24)
    # Version 2 pairs each lightmap page with its daylight page (devdocs/INDOOR_BAKED_LIGHTING.md); same sections.
    if version not in (1, 2) or header_size != 64:
        raise ValueError(f"Unsupported indoor lighting version: {path}")
    if (file_size != len(data) or page_offset != 64 or face_offset != page_offset + page_count * 16
            or sector_offset != face_offset + face_count * 36 or dependency_offset != sector_offset + sector_count * 12
            or not dependency_offset <= pixel_offset <= file_size):
        raise ValueError(f"Invalid indoor lighting sections: {path}")
    found = []
    cursor = dependency_offset
    for _ in range(dependency_count):
        if cursor + 12 > pixel_offset:
            raise ValueError(f"Truncated indoor lighting dependency: {path}")
        length, content_hash = struct.unpack_from("<IQ", data, cursor)
        cursor += 12
        if not 0 < length <= 1024 or cursor + length > pixel_offset:
            raise ValueError(f"Invalid indoor lighting dependency: {path}")
        found.append((data[cursor:cursor + length].decode("utf-8"), content_hash))
        cursor += length
    if cursor != pixel_offset:
        raise ValueError(f"Invalid indoor lighting dependency section: {path}")
    return found


def lighting_dependencies(path):
    """The recorded sources of an installed .lighting file of either kind: outdoor (ODM) or indoor (BLV)."""
    with path.open("rb") as stream:
        magic = stream.read(8)
    return indoor_lighting_dependencies(path) if magic == b"OYILIT1\0" else outdoor_lighting_dependencies(path)


def lighting_archive_dependencies(assets_root):
    """Retain only archived source files still required by the installed lighting's hash contract."""
    entries = {}
    for path in sorted((assets_root / "worlds").glob("*/maps/*.lighting")):
        for name, _ in lighting_dependencies(path):
            if name.startswith("_legacy/"):
                if not name.startswith("_legacy/sprites_original/") or ".." in name or "\\" in name or "\0" in name:
                    raise ValueError(f"Invalid archived lighting dependency: {name}")
                source = assets_root / name
                if not source.is_file() or source.is_symlink():
                    raise ValueError(f"Missing archived lighting dependency: {source}")
                entries[name] = source
    return entries


def sparse_files(root):
    """Files below root that a sparse checkout leaves out (git's skip-worktree entries), relative to root. The android
    content job checks out none of the desktop-only textures; their names still define what the profile replaces."""
    try:
        listing = subprocess.run(["git", "-C", str(root), "ls-files", "-t", "-z", "--", "."], capture_output=True,
                                 check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return set()
    return {item[2:].decode("utf-8") for item in listing.split(b"\0") if item.startswith(b"S ")}


def overlay_model_textures(entries, source, overlay):
    """Replace every packaged cooked model texture (models/textures/*.oytex), terrain material
    (terrain_materials/<id>/*.oytex), effect atlas (effects/authored/textures/*.oytex), sky texture
    (rendering/sky/**/*.oytex) and HUD art (icons_x2/obsidian_*.oytex, icons_x2/faces_*.oytex) with the
    profile's own encoding from overlay (assets_cooked/<profile>/<package>); the cooked GLBs, material library,
    sprite descriptors and face set manifests are shared by all profiles. The profile's set must match the cooked textures in source exactly."""
    def profiled(path):
        return ((path.parent.name == "textures" and path.parent.parent.name in ("models", "authored"))
                or path.parent.parent.name == "terrain_materials"
                or "rendering/sky" in path.parent.as_posix()
                or (path.parent.name == "icons_x2" and path.name.startswith(("obsidian_", "faces_"))))

    def cooked(root, sparse=frozenset()):
        if not root.is_dir():
            return set()
        names = {path.relative_to(root).as_posix() for path in root.rglob("*.oytex")} | sparse
        return {name for name in names if name.endswith(".oytex") and profiled(Path(name))}
    expected, available = cooked(source, sparse_files(source)), cooked(overlay)
    if expected != available:
        missing, stale = sorted(expected - available), sorted(available - expected)
        raise ValueError(f"Profile textures in {overlay} do not match the cooked textures in {source} "
                         f"({len(missing)} missing, e.g. {missing[:3]}; {len(stale)} stale, e.g. {stale[:3]}); "
                         f"run tools/cook_models.py, tools/terrain_materials.py cook, tools/cook_effect_textures.py, "
                         f"tools/cook_sky_textures.py or tools/cook_ui_textures.py for this profile")
    for name in expected & entries.keys():
        entries[name] = overlay / name


def select_surface_textures(entries, profile, android_world):
    """World surface textures (tools/cook_surface_textures.py). Every package keeps textures/ (the .act palettes; the
    original BMPs are source art in assets_source). Desktop ships the BC7 x4 tier (textures_x4/*.oytex); android
    ships its ASTC x2 tier from assets_cooked/android instead. MM9's native-only faces are cooked in the x1 folder
    (textures/*.oytex), BC7 in assets_dev and ASTC in the android overlay. Images that runtime code reads as images
    (hwsplat04.png) stay in their tier folder. The surface material maps of the x4 tier (tools/surface_materials.py)
    ship on desktop only."""
    keep_tier = "textures_x4/" if profile == "desktop" else "textures_x2/"
    for name in list(entries):
        if name.startswith("textures_x") and not name.startswith(keep_tier):
            del entries[name]
        elif name.startswith("surface_materials_x") and profile != "desktop":
            del entries[name]
        elif name.startswith("textures/") and name.endswith(".oytex") and profile != "desktop":
            del entries[name]
    if profile != "desktop" and android_world is not None:
        for tier in ("textures_x2", "textures"):
            overlay = android_world / tier
            for path in sorted(overlay.glob("*.oytex")) if overlay.is_dir() else []:
                entries[f"{tier}/{path.name}"] = path


def verify_surface_cook(assets_root, profile):
    """The selected profile's cooked surface textures match the current sources in assets_source. A checkout without
    the sources (CI) packages the committed cooked files as they are."""
    sources = assets_root.parent / "assets_source"
    if not (sources / "worlds").is_dir():
        print(f"No surface texture sources in {sources}: packaging the committed {profile} cook", flush=True)
        return
    from cook_surface_textures import WORLDS, verify
    output = assets_root if profile == "desktop" else assets_root.parent / "assets_cooked" / profile
    cooker = assets_root.parent / "build/game/openyamm_model_texture_cook"
    if verify(sources, output, profile, cooker, None, WORLDS, require_sources=True):
        raise ValueError(f"Cooked {profile} surface textures are missing or stale; "
                         f"run tools/cook_surface_textures.py --profile {profile}")


# The model manifests the game reads (ActorModelManifest, DecorationModelManifest, DecorationModelSet). Review and
# stress-test manifests selected through debug.actor_models_manifest stay out.
RUNTIME_MODEL_MANIFESTS = {
    "actors.yml", "decorations.yml", "indoor_decorations.yml", "decoration_overlays.yml", "projectiles.yml"
}


def release_model_file(relative):
    """Whether a package's models/ file ships: every GLB, the cooked textures and the runtime manifests (true for
    files outside models/)."""
    if relative.parts[0] != "models" or len(relative.parts) == 1:
        return True
    if len(relative.parts) == 2:
        return relative.suffix == ".glb" or relative.name in RUNTIME_MODEL_MANIFESTS
    return relative.parts[1] == "textures"


def collect_entries(source, *, sprites=None, profile=None, dependencies=None, model_textures=None,
                    surface_profile=None, surface_overlay=None):
    """The files one package (engine or a world) ships: {name inside the package: source path or bytes}."""
    if not source.is_dir():
        raise ValueError(f"Missing asset package: {source}")
    entries = {}
    # A sparse checkout's left-out files stay entries: a profile overlay or surface tier replaces them below, and any
    # other one fails when its pack is written.
    sparse = sparse_files(source)
    for path in sorted(set(source.rglob("*")) | {source / name for name in sparse}):
        relative = path.relative_to(source)
        if any(".cook-" in part or part.endswith(".previous") for part in relative.parts):
            raise ValueError(f"Finish/recover the sprite deployment before packaging: {path}")
        # Development model files, render fixtures and archived sources stay outside release bundles.
        if (not release_model_file(relative)
                or "_legacy" in relative.parts
                or (sprites is not None and relative.parts[0] == "sprites_new")):
            continue
        if path.is_symlink():
            raise ValueError(f"Resolve asset symlinks before packaging: {path}")
        if path.is_file() or relative.as_posix() in sparse:
            entries[relative.as_posix()] = path
    if sprites is not None:
        for path in sorted(sprites.rglob("*")):
            if path.is_file():
                entries["sprites_new/" + path.relative_to(sprites).as_posix()] = path
        entries["sprite_texture_profile.json"] = (
            json.dumps({"schema_version": 2, "texture_profile": profile}, sort_keys=True) + "\n").encode()
    if sprites is not None:
        entries["licenses/zstd.txt"] = Path(__file__).resolve().parents[1] / "packaging/licenses/zstd.txt"
    if model_textures is not None:
        overlay_model_textures(entries, source, model_textures)
    if surface_profile is not None:
        select_surface_textures(entries, surface_profile, surface_overlay)
    for name, path in (dependencies or {}).items():
        if name in entries and entries[name] != path:
            raise ValueError(f"Conflicting runtime dependency: {name}")
        entries[name] = path
    return entries


def collect_languages(languages_root, worlds):
    """The language packs of assets_dev/languages (devdocs/LOCALIZATION.md): ({name in the engine package: source} of
    their text, always installed; {language id: {name in the language folder: source}} of their optional fonts, sounds
    and videos). The templates folder is the translators' and ships nowhere, and neither does the text of a world the
    release leaves out (text/mm9.po when a release ships no MM9)."""
    text, overlays = {}, {}
    if not languages_root.is_dir():
        return text, overlays
    for folder in sorted(languages_root.iterdir()):
        if not folder.is_dir() or folder.name == "templates":
            continue
        if not (folder / "language.yml").is_file():
            raise ValueError(f"Language pack without language.yml: {folder}")
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(folder).as_posix()
            # A world's catalog is named after it (text/mm9.po); worlds/mm9 itself may be absent from the checkout.
            if relative.startswith("text/") and re.fullmatch(r"mm\d+", path.stem) and path.stem not in worlds:
                continue
            if relative == "language.yml" or relative.startswith("text/"):
                text[f"languages/{folder.name}/{relative}"] = path
            elif relative.startswith(("engine/", "worlds/")):
                overlays.setdefault(folder.name, {})[relative] = path
            else:
                raise ValueError(f"Language pack file in no shipped folder: {path}")
    return text, overlays


def package(source, output, **options):
    """One zip of a whole package; tests and tools that inspect a package's selection use it."""
    write_zip(collect_entries(source, **options), output)
    print(f"Packaged {output}: {output.stat().st_size:,} bytes", flush=True)


def sprite_families(root):
    """Family directories of a cooked sprite profile; an absent profile has none (every monster is a 3D model)."""
    return {p.name for p in root.iterdir() if p.is_dir()} if root.is_dir() else set()


def verify_sprite_profiles(installed, selected, profile, cooker):
    """Require the complete family set and identical animation/placement data across profiles."""
    installed_names = sprite_families(installed)
    selected_names = sprite_families(selected)
    if any(not re.fullmatch(r"[a-z0-9_-]{1,128}", name) for name in installed_names | selected_names):
        raise ValueError("Finish/recover the sprite deployment before packaging: invalid family directory")
    if installed_names != selected_names:
        raise ValueError("Selected texture profile does not cover exactly the installed sprite families")
    if not installed_names:
        return
    if installed.resolve() != selected.resolve():
        for name in sorted(installed_names):
            desktop = json.loads((installed / name / "manifest.json").read_text(encoding="utf-8"))
            mobile = json.loads((selected / name / "manifest.json").read_text(encoding="utf-8"))
            desktop.pop("texture_profile", None)
            mobile.pop("texture_profile", None)
            if desktop != mobile:
                raise ValueError(f"Sprite profile animation/placement metadata differs: {name}")
        subprocess.run([str(cooker), "--verify", str(installed), "desktop"], check=True)
    subprocess.run([str(cooker), "--verify", str(selected), profile], check=True)
    if installed.resolve() != selected.resolve():
        for name in sorted(installed_names):
            manifest = json.loads((installed / name / "manifest.json").read_text(encoding="utf-8"))
            for variant in manifest["variants"].values():
                if "lookup" in variant:
                    lookup = variant["lookup"]
                    if (installed / name / lookup).read_bytes() != (selected / name / lookup).read_bytes():
                        raise ValueError(f"Sprite profile palette lookup differs: {name}/{lookup}")


def published_packs(manifest, store):
    """{content_id: published pack file} from an earlier index or manifest and the folder holding its packs."""
    if manifest is None:
        return {}
    document = json.loads(Path(manifest).read_text(encoding="utf-8"))
    reuse = {}
    for record in document["packs"]:
        for candidate in (Path(store) / f"{record['sha256']}.zip", Path(store) / record["file"]):
            if candidate.is_file():
                reuse[record["content_id"]] = candidate
                break
    return reuse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-root", type=Path, default=Path("assets_dev"))
    parser.add_argument("--output", type=Path, default=Path("assets"),
                        help="Folder receiving index.json and packs/ (the packaged asset root)")
    parser.add_argument("--profile", choices=("desktop", "android"), required=True)
    parser.add_argument("--sprites", type=Path, help="Cooked profile override; replaces the entire sprites_new directory")
    parser.add_argument("--cooker", type=Path, default=Path("build/game/openyamm_sprite_atlas_cook" + (".exe" if os.name == "nt" else "")))
    parser.add_argument("--engine-only", action="store_true")
    parser.add_argument("--world", action="append", help="Include selected worlds (default: the worlds packs.yml ships)")
    parser.add_argument("--packs-config", type=Path, default=Path(__file__).resolve().parent / "packaging/packs.yml")
    parser.add_argument("--release", default="dev", help="Release name recorded in index.json")
    parser.add_argument("--build", default="dev", help="Build name recorded in index.json")
    parser.add_argument("--content-format", type=int, default=CONTENT_FORMAT)
    parser.add_argument("--reuse-manifest", type=Path,
                        help="Published index or manifest whose unchanged packs are reused byte for byte")
    parser.add_argument("--reuse-store", type=Path, help="Folder holding the packs of --reuse-manifest")
    parser.add_argument("--report", action="store_true", help="Print every pack's size")
    args = parser.parse_args()
    config = PackConfig.load(args.packs_config)
    installed = args.assets_root / "engine/sprites_new"
    sprites = args.sprites or (args.assets_root.parent / "assets_cooked/android/sprites_new"
                              if args.profile == "android" else installed)
    verify_sprite_profiles(installed, sprites, args.profile, args.cooker.resolve(strict=True))
    dependencies = lighting_archive_dependencies(args.assets_root)
    if not args.engine_only:
        verify_surface_cook(args.assets_root.resolve(), args.profile)
    # Desktop packages use the textures cooked into assets_dev; other profiles overlay their own encodings.
    profile_root = None if args.profile == "desktop" else args.assets_root.parent / "assets_cooked" / args.profile
    packages = {"engine": collect_entries(
        args.assets_root / "engine", sprites=sprites, profile=args.profile, dependencies=dependencies,
        model_textures=profile_root / "engine" if profile_root else None, surface_profile=args.profile)}
    # The rulesets the release offers (engine/rulesets, MAW) ship without their documentation.
    packages["engine"] = {name: source for name, source in packages["engine"].items()
                          if not (name.startswith("rulesets/") and name.endswith(".md"))}
    if not args.engine_only:
        worlds = args.assets_root / "worlds"
        for name in args.world or config.worlds:
            if not name or Path(name).name != name or name in (".", ".."):
                raise ValueError(f"Invalid world package: {name}")
            packages[name] = collect_entries(
                worlds / name, model_textures=profile_root / "worlds" / name if profile_root else None,
                surface_profile=args.profile,
                surface_overlay=args.assets_root.parent / "assets_cooked" / args.profile / "worlds" / name)
    language_text, language_overlays = collect_languages(args.assets_root / "languages", set(packages))
    packages["engine"].update(language_text)
    reuse = published_packs(args.reuse_manifest, args.reuse_store or Path("."))
    records = build_packs(packages, config, args.profile, args.output, reuse, language_overlays)
    write_index(args.output, records, profile=args.profile, release=args.release, build=args.build,
                content_format=args.content_format)
    reused = sum(1 for record in records if record["content_id"] in reuse)
    total = sum(record["size"] for record in records)
    print(f"Packaged {len(records)} packs ({total:,} bytes, {reused} reused) into {args.output}", flush=True)
    if args.report:
        print(report(records, config), flush=True)


if __name__ == "__main__":
    main()
