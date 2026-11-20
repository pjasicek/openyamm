#!/usr/bin/env python3
"""Suggest MM9 equipped-item anchors from the closest compatible MM6-MM8 silhouettes."""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

import yaml
from PIL import Image, ImageDraw


REFERENCE_IDS_BY_PROFILE = {
    "short_sword": range(1, 6),
    "two_handed_sword": range(6, 11),
    "broad_sword": range(11, 16),
    "scimitar": range(16, 21),
    # Item 25 is a three-pronged blade with a deliberately exceptional mid-sprite anchor. It is not a useful
    # reference for conventional MM9 daggers, including the throwing dagger.
    "dagger": [21, 22, 23, 24, 26, 27, 28, 29, 30],
    "one_handed_axe": range(31, 36),
    "two_handed_axe": range(36, 41),
    "spear": range(41, 46),
    "halberd": range(46, 56),
    "bow": range(56, 61),
    "crossbow": range(61, 66),
    "mace": [66, 68, 69, 70, 78],
    "flail": [67],
    "hammer": range(71, 76),
    "club": [76, 77],
    "staff": range(79, 84),
    "large_shield": range(99, 104),
    "small_shield": range(104, 109),
}

# Per raw item: ([x, y], reason) where silhouette detection cannot find the grip. None since the 2026-11-05 icons
# (Imperial Star's diagonal handle, the last entry, is upright now).
MANUAL_ANCHOR_OVERRIDES: dict[int, tuple[list[int], str]] = {}

# Icons are read from x2 packages and measured at the logical (x1) scale that Equip X/Y use.
ICON_SCALE = 2


@dataclass(frozen=True)
class ItemRow:
    item_id: int
    raw_mm9_id: int
    icon_name: str
    name: str
    equip_stat: str
    skill: str
    subtype: str
    equip_x: int
    equip_y: int


def parse_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def read_items(path: Path, mm9: bool) -> dict[int, ItemRow]:
    with path.open("r", encoding="utf-8" if mm9 else "cp1252", newline="") as source_file:
        source_rows = list(csv.reader(source_file, delimiter="\t"))
        header_index = next(
            index for index, row in enumerate(source_rows)
            if row and row[0] == "Item #"
        )
        rows = (
            dict(zip(source_rows[header_index], row))
            for row in source_rows[header_index + 1:]
        )
        result = {}

        for row in rows:
            item_id = parse_int(row.get("Item #", ""))

            if item_id <= 0:
                continue

            raw_mm9_id = parse_int(row.get("x_mm9_raw_item_id", "")) if mm9 else 0
            result[item_id] = ItemRow(
                item_id=item_id,
                raw_mm9_id=raw_mm9_id,
                icon_name=row.get("Pic File", ""),
                name=row.get("Name", ""),
                equip_stat=row.get("Equip Stat", ""),
                skill=row.get("Skill Group", ""),
                subtype=row.get("x_mm9_source_name_type", "") if mm9 else row.get("Not identified name", ""),
                equip_x=parse_int(row.get("Equip X", "")),
                equip_y=parse_int(row.get("Equip Y", "")),
            )

        return result


def find_icon(icon_root: Path, icon_name: str) -> Path:
    for extension in [".png", ".bmp", ".pcx"]:
        candidate = icon_root / f"{icon_name}{extension}"

        if candidate.is_file():
            return candidate

    raise ValueError(f"could not find icon {icon_name!r} under {icon_root}")


def item_mask(path: Path) -> Image.Image:
    """The item's opaque pixels at logical scale: the coverage of an x2 icon is halved, then thresholded."""
    source = Image.open(path).convert("RGBA")

    if path.suffix.casefold() == ".png":
        coverage = source.getchannel("A")
    else:
        coverage = Image.new("L", source.size, 0)
        source_pixels = source.load()
        coverage_pixels = coverage.load()

        for y in range(source.height):
            for x in range(source.width):
                red, green, blue, _alpha = source_pixels[x, y]
                is_cyan_key = red < 80 and green > 170 and blue > 170
                coverage_pixels[x, y] = 0 if is_cyan_key else 255

    if ICON_SCALE != 1:
        logical = tuple(-(-size // ICON_SCALE) for size in coverage.size)
        coverage = coverage.resize(logical, Image.Resampling.LANCZOS)

    return coverage.point(lambda alpha: 255 if alpha > 8 else 0)


def width_profile(mask: Image.Image, sample_count: int = 32) -> list[float]:
    bounds = mask.getbbox()

    if bounds is None:
        return [0.0] * sample_count

    left, top, right, bottom = bounds
    bound_width = max(1, right - left)
    bound_height = max(1, bottom - top)
    pixels = mask.load()
    result = []

    for sample_index in range(sample_count):
        source_y = top + min(
            bound_height - 1,
            int((sample_index + 0.5) * bound_height / sample_count),
        )
        occupied = sum(1 for x in range(left, right) if pixels[x, source_y] > 0)
        result.append(occupied / bound_width)

    return result


def silhouette_score(target: Image.Image, reference: Image.Image) -> float:
    target_bounds = target.getbbox()
    reference_bounds = reference.getbbox()

    if target_bounds is None or reference_bounds is None:
        return math.inf

    target_width = target_bounds[2] - target_bounds[0]
    target_height = target_bounds[3] - target_bounds[1]
    reference_width = reference_bounds[2] - reference_bounds[0]
    reference_height = reference_bounds[3] - reference_bounds[1]
    aspect_score = abs(math.log((target_width / target_height) / (reference_width / reference_height)))
    target_profile = width_profile(target)
    reference_profile = width_profile(reference)
    profile_score = sum(
        abs(left - right)
        for left, right in zip(target_profile, reference_profile)
    ) / len(target_profile)
    target_fill = sum(1 for value in target.getdata() if value > 0) / (target_width * target_height)
    reference_fill = sum(1 for value in reference.getdata() if value > 0) / (reference_width * reference_height)
    return aspect_score * 2.0 + profile_score + abs(target_fill - reference_fill) * 0.25


def profile_for_item(item: ItemRow) -> str:
    subtype = item.subtype.casefold()
    name = item.name.casefold()

    if item.equip_stat == "Shield":
        if "buckler" in subtype or "buckler" in name or "small shield" in subtype or "small shield" in name:
            return "small_shield"
        return "large_shield"
    if item.skill == "Sword":
        if item.equip_stat == "Weapon2" or "two-handed" in subtype:
            return "two_handed_sword"
        if "broad" in subtype:
            return "broad_sword"
        if "scimitar" in subtype:
            return "scimitar"
        return "short_sword"
    if item.skill == "Dagger" or item.skill == "Throwing" and "dagger" in subtype:
        return "dagger"
    if item.skill == "Axe" or item.skill == "Throwing" and "axe" in subtype:
        return "two_handed_axe" if item.equip_stat == "Weapon2" else "one_handed_axe"
    if item.skill == "Bow":
        return "crossbow" if any(token in subtype for token in ["crossbow", "arbalest", "cannon"]) else "bow"
    if item.skill == "Spear":
        return "halberd" if "halberd" in subtype else "spear"
    if item.skill == "Staff":
        return "staff"
    if item.skill == "Mace":
        if "flail" in subtype or "morning star" in subtype:
            return "flail"
        if "hammer" in subtype or "maul" in subtype:
            return "hammer"
        if "club" in subtype or subtype == "weapon":
            return "club"
        return "mace"

    raise ValueError(f"raw item {item.raw_mm9_id} has no equipment visual profile: {item}")


def nearest_reference(
    item: ItemRow,
    target_mask: Image.Image,
    engine_items: dict[int, ItemRow],
    engine_icons: Path,
) -> tuple[ItemRow, Image.Image]:
    profile = profile_for_item(item)
    candidates = []

    for reference_id in REFERENCE_IDS_BY_PROFILE[profile]:
        reference = engine_items.get(reference_id)

        if reference is None or reference.equip_x == 0 and reference.equip_y == 0:
            continue

        reference_mask = item_mask(find_icon(engine_icons, reference.icon_name))
        candidates.append((silhouette_score(target_mask, reference_mask), reference.item_id, reference, reference_mask))

    if not candidates:
        raise ValueError(f"raw item {item.raw_mm9_id} has no usable references for profile {profile}")

    _score, _item_id, reference, reference_mask = min(candidates, key=lambda candidate: candidate[:2])
    return reference, reference_mask


def local_grip_center_x(mask: Image.Image, anchor_y: int, fallback_x: int) -> int:
    pixels = mask.load()
    band_radius = max(2, mask.height // 50)
    occupied_x = []

    for y in range(max(0, anchor_y - band_radius), min(mask.height, anchor_y + band_radius + 1)):
        occupied_x.extend(x for x in range(mask.width) if pixels[x, y] > 0)

    return round(median(occupied_x)) if occupied_x else fallback_x


def long_vertical_handle_center_x(mask: Image.Image) -> int:
    pixels = mask.load()
    column_counts = [
        sum(1 for y in range(mask.height) if pixels[x, y] > 0)
        for x in range(mask.width)
    ]
    maximum_count = max(column_counts, default=0)

    if maximum_count == 0:
        return mask.width // 2

    strongest_columns = [
        x for x, count in enumerate(column_counts)
        if count >= maximum_count * 0.95
    ]
    return round(median(strongest_columns))


def derive_anchor(
    item: ItemRow,
    target_mask: Image.Image,
    reference: ItemRow,
    reference_mask: Image.Image,
) -> list[int]:
    equip_x = round(reference.equip_x * target_mask.width / reference_mask.width)
    equip_y = round(reference.equip_y * target_mask.height / reference_mask.height)
    profile = profile_for_item(item)

    if profile == "flail":
        equip_x = long_vertical_handle_center_x(target_mask)
    elif profile not in {"small_shield", "large_shield", "bow", "crossbow"}:
        equip_x = local_grip_center_x(target_mask, equip_y, equip_x)

    manual_override = MANUAL_ANCHOR_OVERRIDES.get(item.raw_mm9_id)

    if manual_override is not None:
        return list(manual_override[0])

    return [
        min(max(equip_x, 0), target_mask.width - 1),
        min(max(equip_y, 0), target_mask.height - 1),
    ]


def write_previews(
    preview_dir: Path,
    entries: list[tuple[ItemRow, Path, list[int], ItemRow]],
) -> None:
    preview_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[tuple[ItemRow, Path, list[int], ItemRow]]] = {}

    for entry in entries:
        grouped.setdefault(profile_for_item(entry[0]), []).append(entry)

    for profile, profile_entries in sorted(grouped.items()):
        cell_width = 180
        cell_height = 340
        column_count = min(5, len(profile_entries))
        row_count = math.ceil(len(profile_entries) / column_count)
        sheet = Image.new("RGBA", (cell_width * column_count, cell_height * row_count), (28, 28, 32, 255))
        draw = ImageDraw.Draw(sheet)

        for index, (item, icon_path, anchor, reference) in enumerate(profile_entries):
            source = Image.open(icon_path).convert("RGBA")
            logical = tuple(-(-size // ICON_SCALE) for size in source.size)
            source = source.convert("RGBa").resize(logical, Image.Resampling.LANCZOS).convert("RGBA")
            scale = min(3, max(1, min(240 // source.height, 140 // source.width)))
            shown = source.resize((source.width * scale, source.height * scale), Image.Resampling.NEAREST)
            cell_x = index % column_count * cell_width
            cell_y = index // column_count * cell_height
            image_x = cell_x + (cell_width - shown.width) // 2
            image_y = cell_y + 42
            sheet.alpha_composite(shown, (image_x, image_y))
            anchor_x = image_x + anchor[0] * scale
            anchor_y = image_y + anchor[1] * scale
            draw.line((anchor_x - 7, anchor_y, anchor_x + 7, anchor_y), fill=(255, 40, 40, 255), width=2)
            draw.line((anchor_x, anchor_y - 7, anchor_x, anchor_y + 7), fill=(255, 40, 40, 255), width=2)
            draw.text((cell_x + 5, cell_y + 5), f"{item.raw_mm9_id}: {item.name}", fill=(255, 255, 255, 255))
            draw.text(
                (cell_x + 5, cell_y + cell_height - 30),
                f"anchor {anchor[0]},{anchor[1]}  ref {reference.item_id}",
                fill=(210, 210, 215, 255),
            )

        sheet.save(preview_dir / f"{profile}.png")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mm9-items", type=Path, default=Path("assets_dev/worlds/mm9/data_tables/items.txt"))
    parser.add_argument("--mm9-icons", type=Path, default=Path("assets_dev/worlds/mm9/icons_x2"))
    parser.add_argument("--engine-items", type=Path, default=Path("assets_dev/engine/data_tables/items.txt"))
    parser.add_argument("--engine-icons", type=Path, default=Path("assets_dev/engine/icons_x2"))
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()

    mm9_items = read_items(args.mm9_items, True)
    engine_items = read_items(args.engine_items, False)
    definitions: dict[int, dict[str, Any]] = {}
    previews = []

    for item in mm9_items.values():
        if item.equip_stat not in {"Weapon", "Weapon2", "Missile", "Shield"}:
            continue

        icon_path = find_icon(args.mm9_icons, item.icon_name)
        target_mask = item_mask(icon_path)
        reference, reference_mask = nearest_reference(item, target_mask, engine_items, args.engine_icons)
        anchor = derive_anchor(item, target_mask, reference, reference_mask)
        profile = profile_for_item(item)
        method = (
            "reference_anchor_transfer"
            if profile in {"small_shield", "large_shield", "bow", "crossbow"}
            else "reference_grip_transfer"
        )
        if item.raw_mm9_id in MANUAL_ANCHOR_OVERRIDES:
            method = "manual_grip_review"
        definitions[item.raw_mm9_id] = {
            "equip_anchor": anchor,
            "reference_item_id": reference.item_id,
            "method": method,
            "review_status": "candidate",
        }
        manual_override = MANUAL_ANCHOR_OVERRIDES.get(item.raw_mm9_id)

        if manual_override is not None:
            definitions[item.raw_mm9_id]["notes"] = manual_override[1]
        previews.append((item, icon_path, anchor, reference))

    document = {
        "format_version": 1,
        "kind": "mm9_item_equipment_visual_overlay",
        "coordinate_space": "equipped_sprite_pixels_from_top_left",
        "items": definitions,
    }
    yaml.safe_dump(document, sys.stdout, sort_keys=False, allow_unicode=True, width=120)

    if args.preview_dir is not None:
        write_previews(args.preview_dir, previews)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
