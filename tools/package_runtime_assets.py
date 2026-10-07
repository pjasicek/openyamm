#!/usr/bin/env python3
"""Create release ZIPs with exactly one validated native sprite texture profile."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import struct
import tempfile
import zipfile


def lighting_archive_dependencies(assets_root):
    """Retain only archived source files still required by the installed lighting's hash contract."""
    entries = {}
    for path in sorted((assets_root / "worlds").glob("*/maps/*.lighting")):
        with path.open("rb") as stream:
            header = stream.read(96)
            if len(header) != 96 or header[:8] != b"OYMLIT1\0":
                raise ValueError(f"Invalid outdoor lighting header: {path}")
            version, header_size = struct.unpack_from("<II", header, 8)
            if version not in (3, 4, 5) or header_size != 96:
                raise ValueError(f"Unsupported outdoor lighting version: {path}")
            if not struct.unpack_from("<I", header, 76)[0] & 1:
                continue
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
        cursor = counts_offset + 8 + probes * (52 if version >= 4 else 36)
        for _ in range(dependencies):
            if cursor + 12 > len(extension):
                raise ValueError(f"Truncated outdoor lighting dependency: {path}")
            length = struct.unpack_from("<I", extension, cursor)[0]
            cursor += 12
            if not 0 < length <= 1024 or cursor + length > len(extension):
                raise ValueError(f"Invalid outdoor lighting dependency: {path}")
            name = extension[cursor:cursor + length].decode("utf-8")
            cursor += length
            if name.startswith("_legacy/"):
                if not name.startswith("_legacy/sprites_original/") or ".." in name or "\\" in name or "\0" in name:
                    raise ValueError(f"Invalid archived lighting dependency: {name}")
                source = assets_root / name
                if not source.is_file() or source.is_symlink():
                    raise ValueError(f"Missing archived lighting dependency: {source}")
                entries[name] = source
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
    return entries


def package(source, output, *, sprites=None, profile=None, dependencies=None):
    if not source.is_dir():
        raise ValueError(f"Missing asset package: {source}")
    entries = {}
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(".cook-" in part or part.endswith(".previous") for part in relative.parts):
            raise ValueError(f"Finish/recover the sprite deployment before packaging: {path}")
        # Development actor payloads/bindings and render fixtures stay outside release bundles.
        if (relative.parts[0] == "models" or "_legacy" in relative.parts
                or (sprites is not None and relative.parts[0] == "sprites_new")):
            continue
        if path.is_symlink():
            raise ValueError(f"Resolve asset symlinks before packaging: {path}")
        if path.is_file():
            entries[relative.as_posix()] = path
    if sprites is not None:
        for path in sorted(sprites.rglob("*")):
            if path.is_file():
                entries["sprites_new/" + path.relative_to(sprites).as_posix()] = path
        entries["sprite_texture_profile.json"] = (
            json.dumps({"schema_version": 2, "texture_profile": profile}, sort_keys=True) + "\n").encode()
    if sprites is not None:
        entries["licenses/zstd.txt"] = Path(__file__).resolve().parents[1] / "packaging/licenses/zstd.txt"
    for name, path in (dependencies or {}).items():
        if name in entries and entries[name] != path:
            raise ValueError(f"Conflicting runtime dependency: {name}")
        entries[name] = path
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=output.name + ".", suffix=".tmp", dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
    try:
        with zipfile.ZipFile(temporary, "w", allowZip64=True) as archive:
            for name, source_file in sorted(entries.items()):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.external_attr = 0o100644 << 16
                # Cooked GPU pages already contain Zstandard; avoid a second decompression layer.
                info.compress_type = zipfile.ZIP_STORED if name.endswith((".oyatlas", ".ogv")) else zipfile.ZIP_DEFLATED
                with archive.open(info, "w", force_zip64=True) as target:
                    if isinstance(source_file, bytes):
                        target.write(source_file)
                    else:
                        with source_file.open("rb") as source_stream:
                            while block := source_stream.read(1024 * 1024):
                                target.write(block)
        temporary.chmod(0o644)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Packaged {output}: {output.stat().st_size:,} bytes", flush=True)


def verify_sprite_profiles(installed, selected, profile, cooker):
    """Require the complete family set and identical animation/placement data across profiles."""
    for root in (installed, selected):
        if not root.is_dir():
            raise ValueError(f"Missing prebuilt sprite profile: {root}")
    installed_names = {p.name for p in installed.iterdir() if p.is_dir()}
    selected_names = {p.name for p in selected.iterdir() if p.is_dir()}
    if any(not re.fullmatch(r"[a-z0-9_-]{1,128}", name) for name in installed_names | selected_names):
        raise ValueError("Finish/recover the sprite deployment before packaging: invalid family directory")
    if installed_names != selected_names:
        raise ValueError("Selected texture profile does not cover exactly the installed sprite families")
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-root", type=Path, default=Path("assets_dev"))
    parser.add_argument("--output", type=Path, default=Path("assets"))
    parser.add_argument("--profile", choices=("desktop", "android"), required=True)
    parser.add_argument("--sprites", type=Path, help="Cooked profile override; replaces the entire sprites_new directory")
    parser.add_argument("--cooker", type=Path, default=Path("build/game/openyamm_sprite_atlas_cook" + (".exe" if os.name == "nt" else "")))
    parser.add_argument("--engine-only", action="store_true")
    parser.add_argument("--world", action="append", help="Include selected worlds (default: all installed worlds)")
    args = parser.parse_args()
    installed = args.assets_root / "engine/sprites_new"
    sprites = args.sprites or (args.assets_root.parent / "assets_cooked/android/sprites_new"
                              if args.profile == "android" else installed)
    verify_sprite_profiles(installed, sprites, args.profile, args.cooker.resolve(strict=True))
    dependencies = lighting_archive_dependencies(args.assets_root)
    package(args.assets_root / "engine", args.output / "engine.zip", sprites=sprites, profile=args.profile,
            dependencies=dependencies)
    if not args.engine_only:
        worlds = args.assets_root / "worlds"
        selected = args.world or sorted(p.name for p in worlds.iterdir() if p.is_dir())
        for name in selected:
            if not name or Path(name).name != name or name in (".", ".."):
                raise ValueError(f"Invalid world package: {name}")
            package(worlds / name, args.output / "worlds" / f"{name}.zip")


if __name__ == "__main__":
    main()
