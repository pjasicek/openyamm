#!/usr/bin/env python3
"""
Opaque variants of MM9 textures for the faces MM9 draws opaque (dungeon/rooms.py Glass.opaque: window glass, ice,
cloud backdrops without the Translucent flag, whose texture alpha is a translucency or glow mask, not a cut-out).

The scene's `opaque_faces` makes the engine ignore a face's texture alpha, which shows the 1x native's RGB cleanly. The
x4 and x2 tiers lose that RGB where the alpha is low: the x2 reduction and the cooked BC7 mips are filtered with
premultiplied alpha, so a texel at alpha 0-8 comes back black or as quantization noise (Bootcamp's stained glass
drangheimcityglass speckled all over, 2026-11-07), although the x4 master's RGB is clean. A face drawn opaque therefore
takes a variant of its texture with the alpha set to 255 in every tier: the native BMP, the x2 PNG and the cooked x4
from the master's RGB. Variant names keep the native's 10 characters: the first seven, then `OPQ`.

    python3 level_generation/projects/mm9r_common/opaque_textures.py ALIAS...   # into both review roots

The x4 and x2 sources also go to assets_source/worlds/mm9/textures_x4 and textures_x2, whose x4 tier the build cooks
into assets_dev (tools/cook_surface_textures.py); tex.py install keeps these `*opq` files. The native variant goes to
assets_source/worlds/mm9/textures as well (the lighting bake reads it there; without a master the surface cook cooks it
at x1), never as a BMP into assets_dev, which holds only cooked MM9 surfaces.

The converter (build.py faces) gives an opaque face the variant when the root holds its native BMP.
"""

from __future__ import annotations

import io
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

COMMON = Path(__file__).resolve().parent
ROOT = COMMON.parents[2]
sys.path.insert(0, str(COMMON))
sys.path.insert(0, str(ROOT / "tools"))
import review_root  # noqa: E402

MASTERS = ROOT / "level_generation/textures_x4/masters/mm9"
NATIVES = ROOT / "assets_source/worlds/mm9/textures"
SOURCES = ROOT / "assets_source/worlds/mm9"
COOKER = ROOT / "build/game/openyamm_model_texture_cook"
ROOTS = (("assets_dev", "owned.txt"), ("isleofashes_blv_root", "isleofashes_blv_owned.txt"))


def variant_name(alias: str) -> str:
    return alias[:7].upper() + "OPQ"


def native_bmp(alias: str) -> bytes:
    """The 1x native without its alpha (a 24-bit BMP)."""
    image = Image.open(NATIVES / f"{alias}.bmp").convert("RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="BMP")
    return buffer.getvalue()


def master_tiers(alias: str) -> tuple[bytes, bytes, bytes] | None:
    """The x4 tier cooked from the master's RGB (BC7, the desktop surface job), the x2 PNG and the x4 source PNG (the
    master's RGB, the bytes the cook hashed), or None without a master."""
    import cook_surface_textures as cook
    master = MASTERS / f"{alias.lower()}.png"
    if not master.exists():
        return None
    rgb = Image.open(master).convert("RGB")
    with tempfile.TemporaryDirectory() as work:
        source, target = Path(work) / f"{variant_name(alias).lower()}.png", Path(work) / "cooked.oytex"
        rgb.save(source)
        job = "\t".join((str(source), str(target), "bc7", *cook.job_settings(cook.FULL_SIZE),
                         cook.sha256(source)[:16], "surface")) + "\n"
        (Path(work) / "jobs.tsv").write_text(job)
        result = subprocess.run([str(COOKER), str(Path(work) / "jobs.tsv")], text=True, capture_output=True)
        if not target.exists():
            sys.exit(f"{alias}: cook failed\n{result.stdout}\n{result.stderr}")
        x4, x4_source = target.read_bytes(), source.read_bytes()
    buffer = io.BytesIO()
    rgb.resize((rgb.width // 2, rgb.height // 2), Image.LANCZOS).save(buffer, format="PNG")
    return x4, buffer.getvalue(), x4_source


def main(aliases: list[str]) -> int:
    if not COOKER.is_file():
        sys.exit(f"missing {COOKER}: cmake --build build --target openyamm_model_texture_cook")
    for alias in aliases:
        name = variant_name(alias)
        files = {Path("worlds/mm9/textures") / f"{name}.bmp": native_bmp(alias)}
        tiers = master_tiers(alias)
        if tiers:
            files[Path("worlds/mm9/textures_x4") / f"{name.lower()}.oytex"] = tiers[0]
            files[Path("worlds/mm9/textures_x2") / f"{name.lower()}.png"] = tiers[1]
        for directory, owned in ROOTS:
            review_root.ASSETS = review_root.REVIEW / directory
            review_root.OWNED = review_root.REVIEW / owned
            for relative, data in files.items():
                review_root.install(relative, data)
        native, native_data = NATIVES / f"{name}.bmp", files[Path("worlds/mm9/textures") / f"{name}.bmp"]
        if not (native.exists() and native.read_bytes() == native_data):
            temporary = native.with_name(native.name + ".tmp")
            temporary.write_bytes(native_data)
            temporary.replace(native)
        if tiers:
            # The tier sources in assets_source, as tex.py install writes the masters': the build's surface cook
            # (tools/cook_surface_textures.py) makes the same x4 file from them into assets_dev.
            for tier, data in (("textures_x4", tiers[2]), ("textures_x2", tiers[1])):
                target = SOURCES / tier / f"{name.lower()}.png"
                target.parent.mkdir(parents=True, exist_ok=True)
                if not (target.exists() and target.read_bytes() == data):
                    temporary = target.with_name(target.name + ".tmp")
                    temporary.write_bytes(data)
                    temporary.replace(target)
        print(f"{alias} -> {name}: {', '.join(sorted(p.parent.name for p in files))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
