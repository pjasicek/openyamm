#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import struct
from dataclasses import dataclass
from pathlib import Path


MM9_TO_OPENYAMM_SCALE = 2.56

EXTERIOR_MAPS = {
    "drangheim",
    "drangheimcity",
    "frosgard",
    "frosgardcity",
    "guberland",
    "isleofashes",
    "lindisfarne",
    "sturmford",
    "sturmfordcity",
    "thjorgard",
    "thronheim",
    "thronheimcity",
    "yorwick",
}

SKIPPED_MAPS = {"greatgate"}


# MM9 picks a floor image by the player object's height, which is its body centre: the player model's
# static_model half height is 33 LT (devdocs/mm9_rework/MM9_PLAYER_SLOPE_RE.md). The catalog's bands are party foot
# heights, so the thresholds are lowered by that much.
PLAYER_HALF_HEIGHT_LT = 33.0


@dataclass(frozen=True)
class ImageVariant:
    suffix: str
    # Band of the player's centre height in LT: shown when minimum < y <= maximum. A floor whose band is split lists
    # its image once per range; the catalog takes the first variant that matches.
    minimum_source_y: float | None = None
    maximum_source_y: float | None = None


# The floor images, from MM9's map screen (cshell.dll 0x100208a0; thresholds at 0x100c051c-0x100c055c). Bands not
# listed fall to the last, unbounded variant.
FLOOR_VARIANTS = {
    "1000terrors": (
        ImageVariant("A", minimum_source_y=512.0, maximum_source_y=1728.0),
        ImageVariant("B", minimum_source_y=-256.0, maximum_source_y=512.0),
        ImageVariant("C"),
    ),
    "bathhouse": (
        ImageVariant("A", minimum_source_y=-384.0, maximum_source_y=400.0),
        ImageVariant("B"),
    ),
    "beethoven": (
        ImageVariant("A", minimum_source_y=-128.0, maximum_source_y=768.0),
        ImageVariant("B"),
    ),
    "drangheimprison": (
        ImageVariant("A", minimum_source_y=-416.0, maximum_source_y=176.0),
        ImageVariant("B", minimum_source_y=-1024.0, maximum_source_y=-416.0),
        ImageVariant("C"),
    ),
    "klusoshouse": (
        ImageVariant("A", minimum_source_y=-32.0, maximum_source_y=144.0),
        ImageVariant("B"),
    ),
    "lichlab": (
        ImageVariant("A", minimum_source_y=656.0, maximum_source_y=1448.0),
        ImageVariant("B", minimum_source_y=256.0, maximum_source_y=656.0),
        ImageVariant("C"),
    ),
    "traininghall": (
        ImageVariant("A", minimum_source_y=-105.0, maximum_source_y=1521.0),
        ImageVariant("B"),
    ),
}


def read_dat_horizontal_bounds(path: Path, scale: float) -> tuple[float, float, float, float]:
    data = path.read_bytes()
    if len(data) < 52:
        raise ValueError(f"DAT header is truncated: {path}")

    version = struct.unpack_from("<I", data, 0)[0]
    if version != 66:
        raise ValueError(f"expected LithTech DAT v66 in {path}, got {version}")

    offset = 12 + 8 * 4
    property_length = struct.unpack_from("<I", data, offset)[0]
    offset += 4 + property_length + 4
    min_x, _min_y, min_z, max_x, _max_y, max_z = struct.unpack_from("<ffffff", data, offset)

    # MM9 maps positions with abs(header minimum) + party position. This normally matches a conventional
    # minimum/maximum range, but several maps (including BootCamp) have a positive header minimum.
    return -abs(min_x) * scale, max_x * scale, -abs(min_z) * scale, max_z * scale


def read_pcx_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:128]
    if len(data) < 128 or data[0] != 10:
        raise ValueError(f"invalid PCX header: {path}")

    x_min, y_min, x_max, y_max = struct.unpack_from("<HHHH", data, 4)
    return x_max - x_min + 1, y_max - y_min + 1


def format_float(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def source_image_stem(map_stem: str, suffix: str) -> str:
    return map_stem.upper() + suffix


def build_catalog(
    dat_root: Path,
    source_image_root: Path,
    target_image_root: Path,
    scale: float,
) -> str:
    lines = [
        "format_version: 1",
        'kind: "world_map_presentation_catalog"',
        "maps:",
    ]

    image_by_stem = {path.stem.upper(): path for path in source_image_root.glob("*.pcx")}

    for dat_path in sorted(dat_root.glob("*.dat"), key=lambda path: path.stem.lower()):
        map_stem = dat_path.stem.lower()

        if map_stem in SKIPPED_MAPS:
            continue

        variants = FLOOR_VARIANTS.get(map_stem, (ImageVariant(""),))
        resolved_variants: list[tuple[ImageVariant, Path]] = []

        for variant in variants:
            image_path = image_by_stem.get(source_image_stem(map_stem, variant.suffix))
            if image_path is not None:
                resolved_variants.append((variant, image_path))

        if len(resolved_variants) != len(variants):
            expected = ", ".join(source_image_stem(map_stem, variant.suffix) + ".pcx" for variant in variants)
            raise FileNotFoundError(f"missing original MM9 map image for {map_stem}; expected {expected}")

        min_x, max_x, min_y, max_y = read_dat_horizontal_bounds(dat_path, scale)
        exterior = map_stem in EXTERIOR_MAPS
        lines.extend([
            f"  - map: {map_stem}",
            "    world_bounds:",
            f"      min_x: {format_float(min_x)}",
            f"      max_x: {format_float(max_x)}",
            f"      min_y: {format_float(min_y)}",
            f"      max_y: {format_float(max_y)}",
            f"    flip_u: {'true' if exterior else 'false'}",
            f"    flip_v: {'false' if exterior else 'true'}",
            "    reveal_entire_map: true",
            "    variants:",
        ])

        for variant, image_path in resolved_variants:
            target_name = image_path.name.lower()
            width, height = read_pcx_size(image_path)
            shutil.copy2(image_path, target_image_root / target_name)
            lines.extend([
                f"      - texture: ui/maps/{target_name}",
                f"        width: {width}",
                f"        height: {height}",
            ])

            if variant.minimum_source_y is not None:
                lines.append(f"        minimum_z: {format_float((variant.minimum_source_y - PLAYER_HALF_HEIGHT_LT) * scale)}")
            if variant.maximum_source_y is not None:
                lines.append(f"        maximum_z: {format_float((variant.maximum_source_y - PLAYER_HALF_HEIGHT_LT) * scale)}")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote original MM9 map PCX assets into the MM9 world package.")
    parser.add_argument("--dat-root", type=Path, default=Path("mm9/extracted/WORLDS/WORLDS"))
    parser.add_argument(
        "--source-image-root",
        type=Path,
        default=Path("mm9/extracted/ART/ART/INTERFACESCREENS/MAPSCREENS/MAPS"),
    )
    parser.add_argument("--world-root", type=Path, default=Path("assets_dev/worlds/mm9"))
    parser.add_argument("--editor-world-root", type=Path, default=Path("assets_editor_dev/worlds/mm9"))
    parser.add_argument("--scale", type=float, default=MM9_TO_OPENYAMM_SCALE)
    parser.add_argument("--no-editor-copy", action="store_true")
    args = parser.parse_args()

    target_root = args.world_root / "ui" / "maps"
    target_root.mkdir(parents=True, exist_ok=True)
    catalog = build_catalog(args.dat_root, args.source_image_root, target_root, args.scale)
    (target_root / "catalog.yml").write_text(catalog, encoding="utf-8")

    if not args.no_editor_copy:
        editor_target_root = args.editor_world_root / "ui" / "maps"
        editor_target_root.mkdir(parents=True, exist_ok=True)
        for path in target_root.iterdir():
            if path.is_file():
                shutil.copy2(path, editor_target_root / path.name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
