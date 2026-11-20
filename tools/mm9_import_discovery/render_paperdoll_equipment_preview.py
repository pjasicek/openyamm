#!/usr/bin/env python3
"""Render table-driven paperdoll previews for body equipment.

The runtime mode intentionally mirrors OpenYAMM's current equipped-item suffix
selection.  The complete mode uses the full MMerge convention (v1 through v5,
plus the alternate ``a`` armor pose) so missing body-equipment art is visible
before it is wired into the engine.

Icons come from the packages declared in ``engine/icon_packages.txt`` with their
scale tiers, and previews are composited at the physical scale the engine's
native paperdoll composite uses (``PHYSICAL_SCALE`` times the logical 175x378
doll): a lower-tier layer is enlarged with nearest-neighbour sampling and every
table point is a logical pixel.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ENGINE_TABLE_ROOT = REPOSITORY_ROOT / "assets_dev/engine/data_tables"
ICON_PACKAGES = REPOSITORY_ROOT / "assets_dev/engine/icon_packages.txt"
ENGINE_ICON_ROOT = REPOSITORY_ROOT / "assets_dev/engine/icons_x2"
MM9_TABLE_ROOT = REPOSITORY_ROOT / "assets_dev/worlds/mm9/data_tables"
MM9_ICON_ROOT = REPOSITORY_ROOT / "assets_dev/worlds/mm9/icons"
BODY_EQUIPMENT = {"Armor", "Boots", "Helm", "Belt", "Cloak"}
CAN_EQUIP_COLUMN = {"Armor": 2, "Helm": 3, "Belt": 4, "Boots": 5, "Cloak": 6}
BODY_Z_INDEX = 60
HAND_Z_INDEX = 65
# character.yml: the cloak hangs behind the body; armor, helm, belt and boots cover the hands.
ITEM_Z_INDEX = {"Armor": 66, "Boots": 67, "Helm": 66, "Belt": 67, "Cloak": 52}
PAPERDOLL_WIDTH = 175
PAPERDOLL_HEIGHT = 378
PHYSICAL_SCALE = 2


@dataclass(frozen=True)
class CharacterDoll:
    id: int
    doll_type: int
    body_x: int
    body_y: int
    background_asset: str
    body_asset: str
    left_hand_closed_asset: str
    left_hand_hold_asset: str
    left_hand_open_asset: str
    right_hand_fingers_asset: str
    right_hand_open_asset: str
    right_hand_hold_asset: str


@dataclass(frozen=True)
class DollType:
    id: int
    can_equip: dict[str, bool]
    right_hand_open: tuple[int, int]
    right_hand_closed: tuple[int, int]
    right_hand_fingers: tuple[int, int]
    left_hand_closed: tuple[int, int]
    left_hand_open: tuple[int, int]
    left_hand_fingers: tuple[int, int]


@dataclass(frozen=True)
class Item:
    id: int
    icon_name: str
    name: str
    equip_stat: str
    source: str


@dataclass(frozen=True)
class PreviewDiagnostic:
    item_id: int
    item_name: str
    equip_stat: str
    doll_type: int
    character_id: int
    eligible: bool
    selection_mode: str
    selected_asset: str
    selected_asset_path: str
    selected_suffix: str
    expected_primary_asset: str
    expected_primary_exists: bool
    complex_picture_base_offset: tuple[int, int] | None
    portrait_picture_adjustment: tuple[int, int]
    complex_picture_offset: tuple[int, int] | None
    issues: tuple[str, ...]


class AssetIndex:
    """Icon lookup over roots, each a path or a (path, scale tier) pair; earlier roots win, as a higher-priority
    package does. A bare path's tier comes from its name (icons_x2 is tier 2)."""

    def __init__(self, roots: Iterable[Path | tuple[Path, int]]):
        self._paths: dict[str, Path] = {}
        self._tiers: dict[Path, int] = {}

        for entry in roots:
            root, tier = entry if isinstance(entry, tuple) else (entry, 2 if entry.name.endswith("_x2") else 1)

            if not root.is_dir():
                continue

            for path in root.iterdir():
                if path.is_file() and path.suffix.casefold() in {".bmp", ".pcx", ".png"}:
                    if path.stem.casefold() not in self._paths:
                        self._paths[path.stem.casefold()] = path
                        self._tiers[path] = tier

    def find(self, asset_name: str) -> Path | None:
        return self._paths.get(asset_name.casefold())

    def tier(self, path: Path) -> int:
        return self._tiers.get(path, 1)


def declared_icon_roots(packages_path: Path = ICON_PACKAGES) -> list[tuple[Path, int]]:
    """The icon roots of engine/icon_packages.txt, worlds before the engine, with their scale tiers."""
    roots: list[tuple[Path, int]] = []

    for line in packages_path.read_text(encoding="utf-8").splitlines():
        fields = line.split("#", 1)[0].split()

        if len(fields) != 2:
            continue

        package, tier_name = fields
        tier = int(tier_name.removeprefix("x"))
        directory = "icons" if tier == 1 else f"icons_{tier_name}"
        roots.append((packages_path.parents[1] / package / directory, tier))

    return [root for root in roots if root[0] != ENGINE_ICON_ROOT] + [
        root for root in roots if root[0] == ENGINE_ICON_ROOT
    ]


def parse_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def read_tsv(path: Path, encoding: str = "utf-8") -> list[list[str]]:
    with path.open("r", encoding=encoding, newline="") as source_file:
        return list(csv.reader(source_file, delimiter="\t"))


def normalize_asset_name(value: str) -> str:
    normalized = value.strip().casefold()
    return "none" if normalized in {"", "null"} else normalized


def read_character_dolls(path: Path) -> dict[int, CharacterDoll]:
    result: dict[int, CharacterDoll] = {}

    for row in read_tsv(path)[1:]:
        if len(row) < 24:
            continue

        character_id = parse_int(row[0])

        if character_id <= 0:
            continue

        result[character_id] = CharacterDoll(
            id=character_id,
            doll_type=parse_int(row[1]),
            body_x=parse_int(row[6]),
            # CharacterDollTable negates the authored legacy Y value.
            body_y=-parse_int(row[7]),
            background_asset=normalize_asset_name(row[8]),
            body_asset=normalize_asset_name(row[9]),
            left_hand_closed_asset=normalize_asset_name(row[11]),
            left_hand_hold_asset=normalize_asset_name(row[12]),
            left_hand_open_asset=normalize_asset_name(row[13]),
            right_hand_fingers_asset=normalize_asset_name(row[14]),
            right_hand_open_asset=normalize_asset_name(row[17]),
            right_hand_hold_asset=normalize_asset_name(row[18]),
        )

    return result


def legacy_point(row: list[str], x_column: int) -> tuple[int, int]:
    # CharacterDollTable negates all authored doll-type Y values.
    return parse_int(row[x_column]), -parse_int(row[x_column + 1])


def read_doll_types(path: Path) -> dict[int, DollType]:
    result: dict[int, DollType] = {}

    for row in read_tsv(path)[1:]:
        if len(row) < 28:
            continue

        doll_type_id = parse_int(row[0], -1)

        if doll_type_id < 0:
            continue

        result[doll_type_id] = DollType(
            id=doll_type_id,
            can_equip={slot: row[column].strip().casefold() == "x" for slot, column in CAN_EQUIP_COLUMN.items()},
            right_hand_open=legacy_point(row, 8),
            right_hand_closed=legacy_point(row, 10),
            right_hand_fingers=legacy_point(row, 12),
            left_hand_closed=legacy_point(row, 14),
            left_hand_open=legacy_point(row, 16),
            left_hand_fingers=legacy_point(row, 18),
        )

    return result


def read_items(path: Path, source: str) -> dict[int, Item]:
    rows = read_tsv(path, "utf-8" if source == "mm9" else "cp1252")
    header_index = next(index for index, row in enumerate(rows) if row and row[0] == "Item #")
    header = rows[header_index]
    result: dict[int, Item] = {}

    for values in rows[header_index + 1:]:
        row = dict(zip(header, values))
        item_id = parse_int(row.get("Item #", ""))

        if item_id <= 0:
            continue

        result[item_id] = Item(
            id=item_id,
            icon_name=row.get("Pic File", "").strip(),
            name=row.get("Name", "").strip(),
            equip_stat=row.get("Equip Stat", "").strip(),
            source=source,
        )

    return result


def read_complex_picture_offsets(path: Path) -> dict[int, tuple[tuple[int, int], ...]]:
    result: dict[int, tuple[tuple[int, int], ...]] = {}

    for row in read_tsv(path, "cp1252"):
        if len(row) < 6 or not row[0].strip().isdigit() or not row[1].strip().isdigit():
            continue

        item_id = parse_int(row[1])
        points = []

        for doll_type in range(6):
            x_column = 4 + doll_type * 2
            x = parse_int(row[x_column]) if x_column < len(row) else 0
            y = parse_int(row[x_column + 1]) if x_column + 1 < len(row) else 0
            points.append((x, y))

        result[item_id] = tuple(points)

    return result


def read_portrait_picture_adjustments(path: Path) -> dict[tuple[int, int], tuple[int, int]]:
    result: dict[tuple[int, int], tuple[int, int]] = {}

    for row in read_tsv(path, "cp1252")[1:]:
        if len(row) < 4 or not row[0].strip().isdigit() or not row[1].strip().isdigit():
            continue

        result[(parse_int(row[0]), parse_int(row[1]))] = (parse_int(row[2]), parse_int(row[3]))

    return result


def representative_dolls(dolls: dict[int, CharacterDoll]) -> dict[int, CharacterDoll]:
    result: dict[int, CharacterDoll] = {}

    for doll in sorted(dolls.values(), key=lambda value: value.id):
        if doll.doll_type not in result and doll.body_asset != "none" and doll.background_asset != "none":
            result[doll.doll_type] = doll

    return result


def expected_suffixes(item: Item, doll_type: int, has_right_hand_weapon: bool) -> list[str]:
    if item.equip_stat == "Cloak":
        return runtime_suffixes(item, doll_type, has_right_hand_weapon)

    primary = f"v{doll_type + 1}"

    if item.equip_stat == "Armor":
        alternate = f"{primary}a"
        return [primary, alternate] if has_right_hand_weapon else [alternate, primary]

    return [primary]


def runtime_suffixes(item: Item, doll_type: int, has_right_hand_weapon: bool) -> list[str]:
    if doll_type >= 5:
        return []

    variant_number = 1 if item.equip_stat == "Cloak" and doll_type in {2, 3} else doll_type + 1
    primary = f"v{variant_number}"

    if item.equip_stat == "Armor":
        alternate = f"{primary}a"
        return [primary, alternate] if has_right_hand_weapon else [alternate, primary]

    if item.equip_stat == "Cloak":
        return [f"{primary}a"]

    return [primary]


def resolve_item_asset(
    item: Item,
    doll_type: int,
    has_right_hand_weapon: bool,
    mode: str,
    assets: AssetIndex,
) -> tuple[str, Path | None, str]:
    suffixes = (
        runtime_suffixes(item, doll_type, has_right_hand_weapon)
        if mode == "runtime"
        else expected_suffixes(item, doll_type, has_right_hand_weapon)
    )

    for suffix in suffixes:
        asset_name = f"{item.icon_name}{suffix}"
        path = assets.find(asset_name)

        if path is not None:
            return asset_name, path, suffix

    return item.icon_name, assets.find(item.icon_name), ""


def load_layer(path: Path, color_key: bool, tier: int | None = None) -> Image.Image:
    """The layer as stored, or with a scale tier, at physical scale (a lower tier enlarged nearest-neighbour)."""
    image = Image.open(path).convert("RGBA")

    if tier is not None and tier != PHYSICAL_SCALE:
        factor = PHYSICAL_SCALE // tier
        image = image.resize((image.width * factor, image.height * factor), Image.Resampling.NEAREST)

    if not color_key or path.suffix.casefold() == ".png":
        return image

    pixels = image.load()

    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = pixels[x, y]

            is_cyan_key = red < 80 and green > 170 and blue > 170
            is_magenta_key = red > 170 and green < 100 and blue > 170

            if is_cyan_key or is_magenta_key:
                pixels[x, y] = red, green, blue, 0
            elif alpha == 0:
                pixels[x, y] = red, green, blue, 255

    return image


def composite_asset(canvas: Image.Image, assets: AssetIndex, asset_name: str, point: tuple[int, int]) -> None:
    if asset_name in {"", "none", "null"}:
        return

    path = assets.find(asset_name)

    if path is None:
        return

    layer = load_layer(path, color_key=True, tier=assets.tier(path))
    canvas.alpha_composite(layer, physical(point))


def physical(point: tuple[int, int]) -> tuple[int, int]:
    return point[0] * PHYSICAL_SCALE, point[1] * PHYSICAL_SCALE


def render_preview(
    item: Item,
    doll: CharacterDoll,
    doll_type: DollType,
    base_offset: tuple[int, int] | None,
    portrait_adjustment: tuple[int, int],
    has_right_hand_weapon: bool,
    mode: str,
    assets: AssetIndex,
) -> tuple[Image.Image, PreviewDiagnostic]:
    background_path = assets.find(doll.background_asset)
    width = PAPERDOLL_WIDTH * PHYSICAL_SCALE
    height = PAPERDOLL_HEIGHT * PHYSICAL_SCALE
    canvas = (
        load_layer(background_path, color_key=False, tier=assets.tier(background_path))
        if background_path is not None
        else Image.new("RGBA", (width, height), (20, 20, 20, 255))
    )
    canvas = canvas.crop((0, 0, width, height))

    selected_name, selected_path, selected_suffix = resolve_item_asset(
        item, doll_type.id, has_right_hand_weapon, mode, assets
    )
    expected_suffix = expected_suffixes(item, doll_type.id, has_right_hand_weapon)[0]
    expected_name = f"{item.icon_name}{expected_suffix}"
    eligible = doll_type.can_equip.get(item.equip_stat, False)
    issues = []

    if not eligible:
        issues.append("slot is disabled for this doll type")
    if base_offset is None:
        issues.append("missing complex-item-picture row")
    if selected_path is None:
        issues.append("selected asset is missing")
    if selected_suffix == "":
        issues.append("fell back to inventory icon")
    if assets.find(expected_name) is None:
        issues.append(f"missing intended fitted asset {expected_name}")

    item_point = (
        (base_offset[0] + portrait_adjustment[0], base_offset[1] + portrait_adjustment[1])
        if base_offset is not None
        else (0, 0)
    )

    item_layer = (
        load_layer(selected_path, color_key=True, tier=assets.tier(selected_path))
        if selected_path is not None
        else None
    )

    if item_layer is not None and ITEM_Z_INDEX[item.equip_stat] < BODY_Z_INDEX:
        canvas.alpha_composite(item_layer, physical(item_point))

    composite_asset(canvas, assets, doll.body_asset, (doll.body_x, doll.body_y))

    if item_layer is not None and BODY_Z_INDEX <= ITEM_Z_INDEX[item.equip_stat] < HAND_Z_INDEX:
        canvas.alpha_composite(item_layer, physical(item_point))

    if has_right_hand_weapon:
        composite_asset(canvas, assets, doll.right_hand_hold_asset, doll_type.right_hand_closed)
    else:
        composite_asset(canvas, assets, doll.right_hand_open_asset, doll_type.right_hand_open)

    composite_asset(canvas, assets, doll.left_hand_open_asset, doll_type.left_hand_fingers)

    if item_layer is not None and ITEM_Z_INDEX[item.equip_stat] >= HAND_Z_INDEX:
        canvas.alpha_composite(item_layer, physical(item_point))

    if has_right_hand_weapon:
        composite_asset(canvas, assets, doll.right_hand_fingers_asset, doll_type.right_hand_fingers)

    diagnostic = PreviewDiagnostic(
        item_id=item.id,
        item_name=item.name,
        equip_stat=item.equip_stat,
        doll_type=doll_type.id,
        character_id=doll.id,
        eligible=eligible,
        selection_mode=mode,
        selected_asset=selected_name,
        selected_asset_path=str(selected_path) if selected_path is not None else "",
        selected_suffix=selected_suffix,
        expected_primary_asset=expected_name,
        expected_primary_exists=assets.find(expected_name) is not None,
        complex_picture_base_offset=base_offset,
        portrait_picture_adjustment=portrait_adjustment,
        complex_picture_offset=item_point if base_offset is not None else None,
        issues=tuple(issues),
    )
    return canvas, diagnostic


def draw_contact_sheet(
    previews: list[tuple[Item, CharacterDoll, Image.Image, PreviewDiagnostic]],
    item_ids: list[int],
    character_ids: list[int],
    output_path: Path,
) -> None:
    label_height = 39
    cell_width = PAPERDOLL_WIDTH * PHYSICAL_SCALE
    cell_height = PAPERDOLL_HEIGHT * PHYSICAL_SCALE + label_height
    sheet = Image.new(
        "RGBA",
        (cell_width * len(character_ids), cell_height * len(item_ids)),
        (28, 28, 30, 255),
    )
    draw = ImageDraw.Draw(sheet)

    for item, doll, preview, diagnostic in previews:
        column = character_ids.index(doll.id)
        row = item_ids.index(item.id)
        x = column * cell_width
        y = row * cell_height
        sheet.alpha_composite(preview, (x, y + label_height))
        status = "OK" if not diagnostic.issues else " / ".join(diagnostic.issues[:2])
        draw.text((x + 3, y + 2), f"{item.id} {item.name[:20]}", fill=(245, 245, 245, 255))
        draw.text(
            (x + 3, y + 14),
            f"char {doll.id}/type {doll.doll_type}: {diagnostic.selected_asset}",
            fill=(180, 220, 255, 255),
        )
        draw.text(
            (x + 3, y + 26),
            status[:27],
            fill=(140, 240, 160, 255) if not diagnostic.issues else (255, 170, 120, 255),
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(output_path)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-id", action="append", type=int, help="item id; may be repeated")
    parser.add_argument("--all-mm9-armor", action="store_true", help="preview every imported MM9 armor")
    parser.add_argument("--all-mm9-equipment", action="store_true", help="preview all imported MM9 body equipment")
    parser.add_argument("--category", choices=sorted(BODY_EQUIPMENT), help="filter --all-mm9-equipment")
    parser.add_argument("--doll-types", default="0,1,2,3,4", help="comma-separated paperdoll type ids")
    parser.add_argument(
        "--character-ids",
        help="comma-separated character_data ids; overrides --doll-types and checks portrait-specific adjustments",
    )
    parser.add_argument("--mode", choices=["runtime", "complete"], default="runtime")
    parser.add_argument("--right-hand-weapon", action="store_true", help="use the armor/hand weapon pose")
    parser.add_argument("--output", type=Path, required=True, help="output contact-sheet PNG")
    parser.add_argument("--report", type=Path, help="optional JSON diagnostic report")
    parser.add_argument("--extra-icon-root", type=Path, help="higher-priority fitted-asset directory")
    parser.add_argument("--extra-icon-scale", type=int, default=1, help="scale tier of --extra-icon-root (1 or 2)")
    parser.add_argument(
        "--extra-items-table",
        type=Path,
        help="additional items.txt rows (a world contribution such as Hesper's staged table)",
    )
    parser.add_argument("--fail-on-issues", action="store_true", help="return failure when a supported render has issues")
    parser.add_argument(
        "--extra-complex-picture-table",
        type=Path,
        help="additional item placement rows, used after the engine table",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    dolls = read_character_dolls(ENGINE_TABLE_ROOT / "character_data.txt")
    doll_types = read_doll_types(ENGINE_TABLE_ROOT / "doll_types.txt")
    representatives = representative_dolls(dolls)
    items = read_items(ENGINE_TABLE_ROOT / "items.txt", "engine")
    mm9_items = read_items(MM9_TABLE_ROOT / "items.txt", "mm9")
    items.update(mm9_items)

    if arguments.extra_items_table is not None:
        items.update(read_items(arguments.extra_items_table, "mm9"))

    complex_offsets = read_complex_picture_offsets(ENGINE_TABLE_ROOT / "complex_item_pictures.txt")
    mm9_complex_picture_table = MM9_TABLE_ROOT / "complex_item_pictures.txt"

    if mm9_complex_picture_table.is_file():
        complex_offsets.update(read_complex_picture_offsets(mm9_complex_picture_table))

    if arguments.extra_complex_picture_table is not None:
        complex_offsets.update(read_complex_picture_offsets(arguments.extra_complex_picture_table))

    portrait_adjustments = read_portrait_picture_adjustments(
        ENGINE_TABLE_ROOT / "complex_item_picture_offsets.txt"
    )
    icon_roots = declared_icon_roots()

    if arguments.extra_icon_root is not None:
        icon_roots.insert(0, (arguments.extra_icon_root, arguments.extra_icon_scale))

    assets = AssetIndex(icon_roots)
    doll_type_ids = [parse_int(value, -1) for value in arguments.doll_types.split(",")]
    selected_dolls = (
        [dolls[parse_int(value, -1)] for value in arguments.character_ids.split(",")]
        if arguments.character_ids
        else [representatives[doll_type_id] for doll_type_id in doll_type_ids]
    )
    previews: list[tuple[Item, CharacterDoll, Image.Image, PreviewDiagnostic]] = []
    item_ids = list(arguments.item_id or [])

    if arguments.all_mm9_armor:
        item_ids.extend(item.id for item in mm9_items.values() if item.equip_stat == "Armor")
    if arguments.all_mm9_equipment:
        item_ids.extend(
            item.id
            for item in mm9_items.values()
            if item.equip_stat in BODY_EQUIPMENT
            and (arguments.category is None or item.equip_stat == arguments.category)
        )

    item_ids = list(dict.fromkeys(item_ids))

    if not item_ids:
        raise ValueError("at least one --item-id, --all-mm9-armor, or --all-mm9-equipment is required")

    for item_id in item_ids:
        item = items.get(item_id)

        if item is None:
            raise ValueError(f"unknown item id {item_id}")
        if item.equip_stat not in BODY_EQUIPMENT:
            raise ValueError(f"item {item_id} is {item.equip_stat!r}, not supported body equipment")

        for doll in selected_dolls:
            doll_type_id = doll.doll_type
            doll_type = doll_types.get(doll_type_id)

            if doll_type is None:
                raise ValueError(f"no representative character for doll type {doll_type_id}")
            if arguments.all_mm9_equipment and not doll_type.can_equip.get(item.equip_stat, False):
                continue

            points = complex_offsets.get(item_id)
            base_offset = points[doll_type_id] if points is not None and doll_type_id < len(points) else None
            # MMerge's portrait IDs are zero-based; character_data's StatsUI IDs are one-based.
            portrait_adjustment = portrait_adjustments.get((doll.id - 1, item_id), (0, 0))
            preview, diagnostic = render_preview(
                item,
                doll,
                doll_type,
                base_offset,
                portrait_adjustment,
                arguments.right_hand_weapon,
                arguments.mode,
                assets,
            )
            previews.append((item, doll, preview, diagnostic))

    draw_contact_sheet(previews, item_ids, [doll.id for doll in selected_dolls], arguments.output)
    diagnostics = [asdict(preview[3]) for preview in previews]

    if arguments.report is not None:
        arguments.report.parent.mkdir(parents=True, exist_ok=True)
        arguments.report.write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")

    for diagnostic in diagnostics:
        issues = "; ".join(diagnostic["issues"]) or "ok"
        print(
            f"{diagnostic['item_id']}\tt{diagnostic['doll_type']}\t"
            f"{diagnostic['selected_asset']}\t{diagnostic['complex_picture_offset']}\t{issues}"
        )

    if arguments.fail_on_issues and any(diagnostic["issues"] for diagnostic in diagnostics):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
