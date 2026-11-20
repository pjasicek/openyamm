#!/usr/bin/env python3
"""Audit and repair MM9 armor weapon/empty-hand pose pairs.

Native MM7/MM8 armor keeps one shared design and changes only the
right-hand weapon-side arm. This tool derives that permitted arm region from
the mapped native pair and audited target alpha, locks every other pixel to a
reviewed canonical member, renders pair evidence, and promotes complete armor
families atomically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image, ImageDraw

import generate_mm9_equipment_variants as equipment
import render_paperdoll_equipment_preview as paperdoll


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = Path(__file__).resolve().with_name("mm9_equipment_generated_art.yml")
DEFAULT_STAGING_ROOT = Path(__file__).resolve().with_name("armor_pose_pair_staging")
DEFAULT_GENERATED_ROOT = Path(__file__).resolve().with_name("generated_equipment_art")
DEFAULT_WORLD_ICON_ROOT = REPOSITORY_ROOT / "assets_dev/worlds/mm9/icons"
DEFAULT_GOAL = REPOSITORY_ROOT / "devdocs/mm9/MM9_ARMOR_POSE_PAIR_CONSISTENCY_GOAL.md"
PAIR_SUFFIXES = tuple((f"v{index}", f"v{index}a") for index in range(1, 6))
REQUIRED_IN_GAME_REVIEWS = {
    "dark_plate_weapon": (10115, "weapon"),
    "dark_plate_empty": (10115, "empty"),
    "broderick_hauberk_weapon": (10225, "weapon"),
    "broderick_hauberk_empty": (10225, "empty"),
}
REFERENCE_RGB_THRESHOLD = 32
REFERENCE_NEAR_SEED_RADIUS = 6
POSE_SEAM_RADIUS = 2
MIN_INTERNAL_ARM_COMPONENT_PIXELS = 4


@dataclass(frozen=True)
class PairAnalysis:
    raw_id: int
    item_id: int
    item_name: str
    doll_type: int
    weapon_suffix: str
    empty_suffix: str
    canonical_suffix: str
    canonical_reason: str
    allowed_pixels: int
    common_pixels: int
    changed_pixels: int
    changed_inside_allowed: int
    changed_outside_allowed: int
    target_alpha_changed_outside_allowed: int
    common_rgba_exact: bool
    status: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as source_file:
        while chunk := source_file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def sha256_mask(mask: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(mask, dtype=np.uint8).tobytes()).hexdigest()


def image_array(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("RGBA"), dtype=np.uint8).copy()


def alpha_mask(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("RGBA").getchannel("A"), dtype=np.uint8) > 0


def binary_dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius < 0:
        raise ValueError("dilation radius cannot be negative")

    result = np.asarray(mask, dtype=bool).copy()

    for _ in range(radius):
        padded = np.pad(result, 1, mode="constant", constant_values=False)
        expanded = np.zeros_like(result)

        for y_offset in range(3):
            for x_offset in range(3):
                expanded |= padded[
                    y_offset:y_offset + result.shape[0],
                    x_offset:x_offset + result.shape[1],
                ]

        result = expanded

    return result


def material_difference_mask(
    first: Image.Image,
    second: Image.Image,
    threshold: int = REFERENCE_RGB_THRESHOLD,
) -> np.ndarray:
    if first.size != second.size:
        raise ValueError("pose-pair images must have the same dimensions")
    if threshold < 0 or threshold > 255:
        raise ValueError("RGB difference threshold must be between 0 and 255")

    first_pixels = image_array(first)
    second_pixels = image_array(second)
    first_alpha = first_pixels[:, :, 3] > 0
    second_alpha = second_pixels[:, :, 3] > 0
    alpha_difference = first_alpha != second_alpha
    rgb_difference = np.max(
        np.abs(first_pixels[:, :, :3].astype(np.int16) - second_pixels[:, :, :3].astype(np.int16)),
        axis=2,
    ) > threshold
    return alpha_difference | (rgb_difference & first_alpha & second_alpha)


def connected_components(mask: np.ndarray) -> list[np.ndarray]:
    source = np.asarray(mask, dtype=bool)
    visited = np.zeros_like(source)
    components: list[np.ndarray] = []

    for start_y, start_x in np.argwhere(source):
        if visited[start_y, start_x]:
            continue

        component = np.zeros_like(source)
        pending = [(int(start_y), int(start_x))]
        visited[start_y, start_x] = True

        while pending:
            y, x = pending.pop()
            component[y, x] = True

            for adjacent_y in range(max(0, y - 1), min(source.shape[0], y + 2)):
                for adjacent_x in range(max(0, x - 1), min(source.shape[1], x + 2)):
                    if source[adjacent_y, adjacent_x] and not visited[adjacent_y, adjacent_x]:
                        visited[adjacent_y, adjacent_x] = True
                        pending.append((adjacent_y, adjacent_x))

        components.append(component)

    return components


def weapon_arm_components(
    difference: np.ndarray,
    alpha_union: np.ndarray,
) -> np.ndarray:
    coordinates = np.argwhere(alpha_union)

    if coordinates.size == 0:
        return np.zeros_like(alpha_union)

    y_min, x_min = np.min(coordinates, axis=0)
    y_max, x_max = np.max(coordinates, axis=0) + 1
    spatial = np.zeros_like(alpha_union)
    x_limit = int(x_min + (x_max - x_min) * 0.55)
    y_limit = int(y_min + (y_max - y_min) * 0.65)
    spatial[int(y_min):max(int(y_min) + 1, y_limit), int(x_min):max(int(x_min) + 1, x_limit)] = True
    candidate = difference & spatial
    result = np.zeros_like(candidate)

    for component in connected_components(candidate):
        if np.count_nonzero(component) >= MIN_INTERNAL_ARM_COMPONENT_PIXELS:
            result |= component

    return result


def validate_weapon_arm_mask(mask: np.ndarray, alpha_union: np.ndarray, source: str) -> None:
    """Reject a derived or authored mask that escapes the weapon-side upper arm."""
    mask = np.asarray(mask, dtype=bool)
    alpha_union = np.asarray(alpha_union, dtype=bool)

    if mask.shape != alpha_union.shape:
        raise ValueError(f"{source} pose-change mask dimensions do not match the armor")
    if not np.any(mask):
        return

    armor_coordinates = np.argwhere(alpha_union)

    if armor_coordinates.size == 0:
        raise ValueError(f"{source} pose-change mask cannot be used with an empty armor mask")

    mask_coordinates = np.argwhere(mask)
    y_min, x_min = np.min(armor_coordinates, axis=0)
    y_max, x_max = np.max(armor_coordinates, axis=0) + 1
    width = max(1, int(x_max - x_min))
    height = max(1, int(y_max - y_min))
    right_limit = int(x_min + width * 0.55)
    bottom_limit = int(y_min + height * 0.70)
    maximum_pixels = max(1, int(np.count_nonzero(alpha_union) * 0.20))

    if int(np.max(mask_coordinates[:, 1])) >= right_limit:
        raise ValueError(f"{source} pose-change mask reaches the chest or opposite arm")
    if int(np.max(mask_coordinates[:, 0])) >= bottom_limit:
        raise ValueError(f"{source} pose-change mask reaches the waist or legs")
    if int(np.count_nonzero(mask)) > maximum_pixels:
        raise ValueError(f"{source} pose-change mask is broader than a weapon-side arm edit")


def derive_pose_change_mask(
    weapon_reference: Image.Image,
    empty_reference: Image.Image,
    weapon_target: Image.Image,
    empty_target: Image.Image,
) -> np.ndarray:
    images = (weapon_reference, empty_reference, weapon_target, empty_target)

    if len({image.size for image in images}) != 1:
        raise ValueError("reference and target pose-pair images must have matching dimensions")

    target_alpha_union = alpha_mask(weapon_target) | alpha_mask(empty_target)
    target_difference = alpha_mask(weapon_target) != alpha_mask(empty_target)
    pose_geometry = weapon_arm_components(target_difference, target_alpha_union)
    reference_difference = material_difference_mask(weapon_reference, empty_reference)

    if not np.any(pose_geometry):
        reference_alpha = alpha_mask(weapon_reference) | alpha_mask(empty_reference)
        internal_difference = weapon_arm_components(reference_difference, reference_alpha)

        if np.any(internal_difference):
            return binary_dilate(internal_difference, POSE_SEAM_RADIUS)

        return internal_difference

    near_pose_geometry = binary_dilate(pose_geometry, REFERENCE_NEAR_SEED_RADIUS)
    semantic_arm_difference = reference_difference & near_pose_geometry
    allowed = pose_geometry | semantic_arm_difference
    return binary_dilate(allowed, POSE_SEAM_RADIUS)


def derive_validated_pose_change_mask(
    weapon_reference: Image.Image,
    empty_reference: Image.Image,
    weapon_target: Image.Image,
    empty_target: Image.Image,
) -> np.ndarray:
    allowed = derive_pose_change_mask(
        weapon_reference,
        empty_reference,
        weapon_target,
        empty_target,
    )
    validate_weapon_arm_mask(
        allowed,
        alpha_mask(weapon_target) | alpha_mask(empty_target),
        "derived",
    )
    return allowed


def rgba_difference_mask(first: Image.Image, second: Image.Image) -> np.ndarray:
    if first.size != second.size:
        raise ValueError("pose-pair images must have the same dimensions")

    return np.any(image_array(first) != image_array(second), axis=2)


def transparent_rgb_count(image: Image.Image) -> int:
    pixels = image_array(image)
    transparent = pixels[:, :, 3] == 0
    return int(np.count_nonzero(np.any(pixels[:, :, :3] != 0, axis=2) & transparent))


def common_region_mask(
    weapon_target: Image.Image,
    empty_target: Image.Image,
    allowed: np.ndarray,
) -> np.ndarray:
    return alpha_mask(weapon_target) & alpha_mask(empty_target) & ~allowed


def palette_histogram(image: Image.Image) -> np.ndarray:
    pixels = image_array(image)
    opaque = pixels[:, :, 3] > 0

    if not np.any(opaque):
        return np.zeros(512, dtype=np.float64)

    quantized = (pixels[:, :, :3][opaque] // 32).astype(np.int32)
    indices = quantized[:, 0] * 64 + quantized[:, 1] * 8 + quantized[:, 2]
    histogram = np.bincount(indices, minlength=512).astype(np.float64)
    return histogram / np.sum(histogram)


def choose_canonical_suffix(
    weapon_suffix: str,
    empty_suffix: str,
    weapon: Image.Image,
    empty: Image.Image,
    inventory: Image.Image,
) -> tuple[str, str]:
    inventory_histogram = palette_histogram(inventory)
    weapon_distance = float(np.sum(np.abs(palette_histogram(weapon) - inventory_histogram)))
    empty_distance = float(np.sum(np.abs(palette_histogram(empty) - inventory_histogram)))

    if weapon_distance <= empty_distance:
        suffix = weapon_suffix
        distance = weapon_distance
        alternate = empty_distance
    else:
        suffix = empty_suffix
        distance = empty_distance
        alternate = weapon_distance

    reason = (
        "selected by smaller quantized-palette distance to the promoted MM9 inventory icon "
        f"({distance:.6f} versus {alternate:.6f}); retained only after pair visual review"
    )
    return suffix, reason


def lock_common_region(
    weapon: Image.Image,
    empty: Image.Image,
    weapon_target: Image.Image,
    empty_target: Image.Image,
    allowed: np.ndarray,
    canonical_suffix: str,
    weapon_suffix: str,
    empty_suffix: str,
) -> tuple[Image.Image, Image.Image]:
    if len({image.size for image in (weapon, empty, weapon_target, empty_target)}) != 1:
        raise ValueError("repair inputs must have matching dimensions")
    if canonical_suffix not in {weapon_suffix, empty_suffix}:
        raise ValueError("canonical suffix is not a member of the pose pair")

    weapon_pixels = image_array(weapon)
    empty_pixels = image_array(empty)
    weapon_alpha = alpha_mask(weapon_target)
    empty_alpha = alpha_mask(empty_target)
    common = weapon_alpha & empty_alpha & ~allowed
    canonical = weapon_pixels if canonical_suffix == weapon_suffix else empty_pixels

    weapon_pixels[common] = canonical[common]
    empty_pixels[common] = canonical[common]
    weapon_pixels[:, :, 3] = np.where(weapon_alpha, 255, 0).astype(np.uint8)
    empty_pixels[:, :, 3] = np.where(empty_alpha, 255, 0).astype(np.uint8)
    weapon_pixels[~weapon_alpha, :3] = 0
    empty_pixels[~empty_alpha, :3] = 0

    return Image.fromarray(weapon_pixels, "RGBA"), Image.fromarray(empty_pixels, "RGBA")


def normalize_target_pair(
    weapon_target: Image.Image,
    empty_target: Image.Image,
    allowed: np.ndarray,
    canonical_suffix: str,
    weapon_suffix: str,
    empty_suffix: str,
) -> tuple[Image.Image, Image.Image]:
    if weapon_target.size != empty_target.size:
        raise ValueError("target pose-pair images must have matching dimensions")
    if canonical_suffix not in {weapon_suffix, empty_suffix}:
        raise ValueError("canonical suffix is not a member of the target pose pair")

    weapon_pixels = image_array(weapon_target)
    empty_pixels = image_array(empty_target)
    canonical = weapon_pixels if canonical_suffix == weapon_suffix else empty_pixels
    shared = ~allowed
    weapon_pixels[shared] = canonical[shared]
    empty_pixels[shared] = canonical[shared]
    weapon_pixels[weapon_pixels[:, :, 3] == 0, :3] = 0
    empty_pixels[empty_pixels[:, :, 3] == 0, :3] = 0
    return Image.fromarray(weapon_pixels, "RGBA"), Image.fromarray(empty_pixels, "RGBA")


def analyze_pair(
    raw_id: int,
    item: equipment.EquipmentItem,
    weapon_suffix: str,
    empty_suffix: str,
    weapon: Image.Image,
    empty: Image.Image,
    weapon_target: Image.Image,
    empty_target: Image.Image,
    allowed: np.ndarray,
    canonical_suffix: str,
    canonical_reason: str,
) -> PairAnalysis:
    difference = rgba_difference_mask(weapon, empty)
    target_difference = alpha_mask(weapon_target) != alpha_mask(empty_target)
    common = common_region_mask(weapon_target, empty_target, allowed)
    outside_difference = difference & ~allowed
    common_difference = difference & common
    outside_target_difference = target_difference & ~allowed
    accepted = not np.any(outside_difference) and not np.any(outside_target_difference)

    return PairAnalysis(
        raw_id=raw_id,
        item_id=item.item_id,
        item_name=item.name,
        doll_type=int(weapon_suffix[1]) - 1,
        weapon_suffix=weapon_suffix,
        empty_suffix=empty_suffix,
        canonical_suffix=canonical_suffix,
        canonical_reason=canonical_reason,
        allowed_pixels=int(np.count_nonzero(allowed)),
        common_pixels=int(np.count_nonzero(common)),
        changed_pixels=int(np.count_nonzero(difference)),
        changed_inside_allowed=int(np.count_nonzero(difference & allowed)),
        changed_outside_allowed=int(np.count_nonzero(outside_difference)),
        target_alpha_changed_outside_allowed=int(np.count_nonzero(outside_target_difference)),
        common_rgba_exact=not np.any(common_difference),
        status="reviewed" if accepted else "failed",
    )


def save_binary_mask(mask: np.ndarray, path: Path, color: tuple[int, int, int]) -> None:
    pixels = np.zeros((*mask.shape, 4), dtype=np.uint8)
    pixels[mask, :3] = color
    pixels[mask, 3] = 255
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels, "RGBA").save(path, optimize=False)


def checkerboard(size: tuple[int, int], cell_size: int = 8) -> Image.Image:
    width, height = size
    y_indices, x_indices = np.indices((height, width))
    pattern = ((x_indices // cell_size + y_indices // cell_size) % 2).astype(np.uint8)
    colors = np.where(pattern[:, :, None] == 0, 70, 105).astype(np.uint8)
    rgb = np.repeat(colors, 3, axis=2)
    alpha = np.full((height, width, 1), 255, dtype=np.uint8)
    return Image.fromarray(np.concatenate([rgb, alpha], axis=2), "RGBA")


def labelled_side_by_side(
    first: Image.Image,
    second: Image.Image,
    first_label: str,
    second_label: str,
    scale: int = 1,
) -> Image.Image:
    label_height = 18
    cell_width = max(first.width, second.width) * scale
    cell_height = max(first.height, second.height) * scale
    result = Image.new("RGBA", (cell_width * 2, cell_height + label_height), (35, 35, 38, 255))
    draw = ImageDraw.Draw(result)

    for index, (image, label) in enumerate(((first, first_label), (second, second_label))):
        background = checkerboard(image.size)
        background.alpha_composite(image)
        if scale != 1:
            background = background.resize(
                (background.width * scale, background.height * scale),
                Image.Resampling.NEAREST,
            )
        x = index * cell_width + (cell_width - background.width) // 2
        result.alpha_composite(background, (x, label_height))
        draw.text((index * cell_width + 3, 3), label, fill=(245, 245, 245, 255))

    return result


def mask_review_image(difference: np.ndarray, allowed: np.ndarray, scale: int = 3) -> Image.Image:
    outside = difference & ~allowed
    difference_pixels = np.zeros((*difference.shape, 4), dtype=np.uint8)
    difference_pixels[difference & allowed] = (255, 190, 0, 255)
    difference_pixels[outside] = (255, 0, 0, 255)
    allowed_pixels = np.zeros((*allowed.shape, 4), dtype=np.uint8)
    allowed_pixels[allowed] = (80, 190, 255, 255)
    return labelled_side_by_side(
        Image.fromarray(difference_pixels, "RGBA"),
        Image.fromarray(allowed_pixels, "RGBA"),
        "difference: amber allowed / red forbidden",
        "allowed weapon-side arm region",
        scale,
    )


def seam_review_image(
    weapon: Image.Image,
    empty: Image.Image,
    allowed: np.ndarray,
    scale: int = 4,
) -> Image.Image:
    coordinates = np.argwhere(allowed)

    if coordinates.size == 0:
        bounds = (0, 0, weapon.width, min(weapon.height, max(1, weapon.height // 2)))
    else:
        y_min, x_min = np.min(coordinates, axis=0)
        y_max, x_max = np.max(coordinates, axis=0) + 1
        margin = 6
        bounds = (
            max(0, int(x_min) - margin),
            max(0, int(y_min) - margin),
            min(weapon.width, int(x_max) + margin),
            min(weapon.height, int(y_max) + margin),
        )

    return labelled_side_by_side(
        weapon.crop(bounds),
        empty.crop(bounds),
        "weapon-side seam",
        "empty-hand seam",
        scale,
    )


def render_equipped_pair(
    item: equipment.EquipmentItem,
    doll_type_id: int,
    icon_root: Path,
) -> tuple[Image.Image, Image.Image]:
    dolls = paperdoll.read_character_dolls(paperdoll.ENGINE_TABLE_ROOT / "character_data.txt")
    doll_types = paperdoll.read_doll_types(paperdoll.ENGINE_TABLE_ROOT / "doll_types.txt")
    representative = paperdoll.representative_dolls(dolls)[doll_type_id]
    doll_type = doll_types[doll_type_id]
    offsets = paperdoll.read_complex_picture_offsets(
        paperdoll.MM9_TABLE_ROOT / "complex_item_pictures.txt"
    )
    assets = paperdoll.AssetIndex([icon_root, paperdoll.MM9_ICON_ROOT, paperdoll.ENGINE_ICON_ROOT])
    preview_item = paperdoll.Item(
        id=item.item_id,
        icon_name=item.icon_name,
        name=item.name,
        equip_stat=item.category,
        source="mm9",
    )
    base_offset = offsets[item.item_id][doll_type_id]
    weapon, weapon_diagnostic = paperdoll.render_preview(
        preview_item,
        representative,
        doll_type,
        base_offset,
        (0, 0),
        True,
        "runtime",
        assets,
    )
    empty, empty_diagnostic = paperdoll.render_preview(
        preview_item,
        representative,
        doll_type,
        base_offset,
        (0, 0),
        False,
        "runtime",
        assets,
    )

    if weapon_diagnostic.issues or empty_diagnostic.issues:
        raise ValueError(
            f"failed to render item {item.item_id} doll {doll_type_id}: "
            f"{weapon_diagnostic.issues}, {empty_diagnostic.issues}"
        )

    return weapon, empty


def weapon_name(item: equipment.EquipmentItem, suffix: str) -> str:
    return f"{item.icon_name}{suffix}"


def save_pair_evidence(
    root: Path,
    item: equipment.EquipmentItem,
    analysis: PairAnalysis,
    weapon: Image.Image,
    empty: Image.Image,
    allowed: np.ndarray,
    common: np.ndarray,
    icon_root: Path,
) -> dict[str, Path]:
    pair_name = f"{weapon_name(item, analysis.weapon_suffix)}_{analysis.empty_suffix}"
    mask_root = root / "masks"
    review_root = root / "reviews"
    allowed_path = mask_root / f"{pair_name}_allowed.png"
    common_path = mask_root / f"{pair_name}_common.png"
    isolated_path = review_root / f"{pair_name}_isolated.png"
    equipped_path = review_root / f"{pair_name}_equipped.png"
    blink_path = review_root / f"{pair_name}_blink.gif"
    difference_path = review_root / f"{pair_name}_difference.png"
    seam_path = review_root / f"{pair_name}_seam.png"

    save_binary_mask(allowed, allowed_path, (80, 190, 255))
    save_binary_mask(common, common_path, (150, 150, 150))
    isolated = labelled_side_by_side(
        weapon,
        empty,
        f"{analysis.weapon_suffix} weapon",
        f"{analysis.empty_suffix} empty",
        2,
    )
    isolated_path.parent.mkdir(parents=True, exist_ok=True)
    isolated.save(isolated_path, optimize=False)
    equipped_weapon, equipped_empty = render_equipped_pair(item, analysis.doll_type, icon_root)
    equipped = labelled_side_by_side(
        equipped_weapon,
        equipped_empty,
        f"{analysis.weapon_suffix} weapon",
        f"{analysis.empty_suffix} empty",
    )
    equipped.save(equipped_path, optimize=False)
    equipped_weapon.convert("P", palette=Image.Palette.ADAPTIVE).save(
        blink_path,
        save_all=True,
        append_images=[equipped_empty.convert("P", palette=Image.Palette.ADAPTIVE)],
        duration=650,
        loop=0,
        disposal=2,
    )
    mask_review_image(rgba_difference_mask(weapon, empty), allowed).save(difference_path, optimize=False)
    seam_review_image(weapon, empty, allowed).save(seam_path, optimize=False)

    return {
        "allowed_change_mask": allowed_path,
        "common_region_mask": common_path,
        "isolated_review": isolated_path,
        "equipped_review": equipped_path,
        "blink_review": blink_path,
        "difference_review": difference_path,
        "seam_review": seam_path,
    }


def save_family_contact_sheet(
    item: equipment.EquipmentItem,
    inventory: Image.Image,
    equipped_pair_paths: list[Path],
    output_path: Path,
) -> None:
    if len(equipped_pair_paths) != 5:
        raise ValueError(f"armor {item.item_id} must have five equipped pair reviews")

    row_width = 350
    row_height = 198
    header_height = 82
    sheet = Image.new("RGBA", (row_width, header_height + row_height * 5), (30, 30, 33, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((82, 10), f"{item.item_id} {item.name}", fill=(245, 245, 245, 255))
    draw.text((82, 28), "weapon pose / empty-hand pose", fill=(180, 220, 255, 255))
    draw.text((82, 46), "shared body locked; weapon-side arm may differ", fill=(170, 230, 180, 255))
    inventory_preview = checkerboard((72, 72), 6)
    inventory.thumbnail((68, 68), Image.Resampling.LANCZOS)
    inventory_preview.alpha_composite(
        inventory,
        ((inventory_preview.width - inventory.width) // 2, (inventory_preview.height - inventory.height) // 2),
    )
    sheet.alpha_composite(inventory_preview, (4, 4))

    for row, path in enumerate(equipped_pair_paths):
        review = Image.open(path).convert("RGBA")
        review = review.resize((row_width, row_height), Image.Resampling.LANCZOS)
        sheet.alpha_composite(review, (0, header_height + row * row_height))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(output_path, optimize=False)


def save_catalogue_pages(
    family_paths: list[Path],
    output_root: Path,
    families_per_page: int = 5,
) -> list[Path]:
    if families_per_page <= 0:
        raise ValueError("families per catalogue page must be positive")

    result: list[Path] = []

    for page_index, first_family in enumerate(range(0, len(family_paths), families_per_page), start=1):
        page_paths = family_paths[first_family:first_family + families_per_page]
        images = [Image.open(path).convert("RGBA") for path in page_paths]
        page = Image.new(
            "RGBA",
            (sum(image.width for image in images), max(image.height for image in images)),
            (25, 25, 28, 255),
        )
        x = 0

        for image in images:
            page.alpha_composite(image, (x, 0))
            x += image.width

        output_path = output_root / f"mm9_armor_pose_pairs_catalogue_{page_index:02d}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        page.convert("RGB").save(output_path, optimize=False)
        result.append(output_path)

    return result


def save_detail_catalogue_pages(
    entries: list[tuple[str, Path]],
    output_root: Path,
    name: str,
    entries_per_page: int = 12,
) -> list[Path]:
    cell_width = 400
    cell_height = 300
    columns = 4
    result: list[Path] = []

    for page_index, first_entry in enumerate(range(0, len(entries), entries_per_page), start=1):
        page_entries = entries[first_entry:first_entry + entries_per_page]
        rows = (len(page_entries) + columns - 1) // columns
        page = Image.new("RGBA", (cell_width * columns, cell_height * rows), (25, 25, 28, 255))
        draw = ImageDraw.Draw(page)

        for index, (label, path) in enumerate(page_entries):
            image = Image.open(path).convert("RGBA")
            image.thumbnail((cell_width, cell_height - 20), Image.Resampling.LANCZOS)
            x = (index % columns) * cell_width
            y = (index // columns) * cell_height
            page.alpha_composite(image, (x + (cell_width - image.width) // 2, y + 20))
            draw.text((x + 3, y + 3), label, fill=(245, 245, 245, 255))

        output_path = output_root / f"mm9_armor_pose_pairs_{name}_{page_index:02d}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        page.convert("RGB").save(output_path, optimize=False)
        result.append(output_path)

    return result


def read_yaml(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(document, dict):
        raise ValueError(f"{path} does not contain a YAML mapping")

    return document


def write_yaml(path: Path, document: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.pose-pair-new")
    temporary_path.write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )
    os.replace(temporary_path, path)


def copy_file_atomically(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise ValueError(f"atomic promotion source is missing: {source}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_name(f".{destination.name}.pose-pair-new")
    shutil.copyfile(source, temporary_path)
    os.replace(temporary_path, destination)


def copy_family_files_atomically(replacements: list[tuple[Path, Path]]) -> None:
    destinations = [destination for _source, destination in replacements]

    if len(destinations) != len(set(destinations)):
        raise ValueError("atomic family promotion contains duplicate destinations")

    for source, _destination in replacements:
        if not source.is_file():
            raise ValueError(f"atomic family promotion source is missing: {source}")

    prepared: list[tuple[Path, Path]] = []

    try:
        for source, destination in replacements:
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = destination.with_name(f".{destination.name}.pose-pair-new")
            shutil.copyfile(source, temporary_path)
            prepared.append((temporary_path, destination))

        for temporary_path, destination in prepared:
            os.replace(temporary_path, destination)
    finally:
        for temporary_path, _destination in prepared:
            temporary_path.unlink(missing_ok=True)


def armor_items(*, allow_stale_goal_hash: bool = False) -> tuple[
    dict[int, equipment.EquipmentItem],
    dict[int, equipment.EquipmentMapping],
    dict[tuple[int, str], equipment.AuthoredEquipmentVariant],
]:
    items = equipment.read_equipment_items(paperdoll.MM9_TABLE_ROOT / "items.txt")
    mappings = equipment.load_mappings(equipment.DEFAULT_MAPPING, items)
    authored = equipment.load_authored_art_manifest(
        DEFAULT_MANIFEST,
        items,
        allow_stale_pose_pair_goal_hash=allow_stale_goal_hash,
    )
    return (
        {raw_id: item for raw_id, item in items.items() if item.category == "Armor"},
        mappings,
        authored,
    )


def foot_exclusion_masks() -> dict[int, np.ndarray]:
    engine_items = paperdoll.read_items(paperdoll.ENGINE_TABLE_ROOT / "items.txt", "engine")
    engine_assets = paperdoll.AssetIndex([paperdoll.ENGINE_ICON_ROOT])
    offsets = paperdoll.read_complex_picture_offsets(
        paperdoll.ENGINE_TABLE_ROOT / "complex_item_pictures.txt"
    )
    dolls = paperdoll.read_character_dolls(paperdoll.ENGINE_TABLE_ROOT / "character_data.txt")
    definitions = equipment.load_foot_exclusions(equipment.DEFAULT_FOOT_EXCLUSIONS)
    return equipment.build_foot_exclusion_masks(definitions, engine_items, engine_assets, offsets, dolls)


def load_pair_inputs(
    raw_id: int,
    item: equipment.EquipmentItem,
    weapon_suffix: str,
    empty_suffix: str,
    mappings: dict[int, equipment.EquipmentMapping],
    authored: dict[tuple[int, str], equipment.AuthoredEquipmentVariant],
) -> tuple[Image.Image, Image.Image, Image.Image, Image.Image, Image.Image, Image.Image, Image.Image]:
    weapon_variant = authored[(raw_id, weapon_suffix)]
    empty_variant = authored[(raw_id, empty_suffix)]
    weapon = Image.open(weapon_variant.asset_path).convert("RGBA")
    empty = Image.open(empty_variant.asset_path).convert("RGBA")
    weapon_target = Image.open(weapon_variant.target_mask_path).convert("RGBA")
    empty_target = Image.open(empty_variant.target_mask_path).convert("RGBA")
    weapon_reference = paperdoll.load_layer(weapon_variant.reference_asset_path, color_key=True)
    empty_reference = paperdoll.load_layer(empty_variant.reference_asset_path, color_key=True)
    inventory = Image.open(weapon_variant.inventory_asset_path).convert("RGBA")

    if mappings[raw_id].reference_item_id <= 0:
        raise ValueError(f"armor {item.item_id} has no mapped native reference")

    return (
        weapon,
        empty,
        weapon_target,
        empty_target,
        weapon_reference,
        empty_reference,
        inventory,
    )


def selected_raw_ids(requested_item_ids: list[int] | None, items: dict[int, equipment.EquipmentItem]) -> list[int]:
    requested = set(requested_item_ids or [])
    by_item_id = {item.item_id: raw_id for raw_id, item in items.items()}
    unknown = requested - set(by_item_id)

    if unknown:
        raise ValueError(f"unknown MM9 armor item ids: {sorted(unknown)}")

    return sorted(by_item_id[item_id] for item_id in requested) if requested else sorted(items)


def stage_repairs(arguments: argparse.Namespace) -> int:
    items, mappings, authored = armor_items(allow_stale_goal_hash=True)
    raw_ids = selected_raw_ids(arguments.item_id, items)
    staging_root = arguments.staging_root
    icon_root = staging_root / "icons"
    target_root = staging_root / "targets"
    pair_root = staging_root / "pose_pairs"
    analyses: list[PairAnalysis] = []
    baseline_failures = 0
    pair_records: dict[int, dict[str, Any]] = {}
    family_equipped_reviews: dict[int, list[Path]] = {raw_id: [] for raw_id in raw_ids}
    seam_review_entries: list[tuple[str, Path]] = []
    difference_review_entries: list[tuple[str, Path]] = []

    if staging_root.exists():
        if not arguments.replace_staging:
            raise ValueError(f"staging root already exists: {staging_root}; use --replace-staging")
        shutil.rmtree(staging_root)

    icon_root.mkdir(parents=True)

    for raw_id in raw_ids:
        item = items[raw_id]
        pair_records[raw_id] = {}

        for weapon_suffix, empty_suffix in PAIR_SUFFIXES:
            inputs = load_pair_inputs(
                raw_id,
                item,
                weapon_suffix,
                empty_suffix,
                mappings,
                authored,
            )
            weapon, empty, weapon_target, empty_target = inputs[:4]
            allowed = derive_validated_pose_change_mask(inputs[4], inputs[5], weapon_target, empty_target)
            canonical_suffix, canonical_reason = choose_canonical_suffix(
                weapon_suffix,
                empty_suffix,
                weapon,
                empty,
                inputs[6],
            )
            weapon_target, empty_target = normalize_target_pair(
                weapon_target,
                empty_target,
                allowed,
                canonical_suffix,
                weapon_suffix,
                empty_suffix,
            )
            baseline = analyze_pair(
                raw_id,
                item,
                weapon_suffix,
                empty_suffix,
                weapon,
                empty,
                weapon_target,
                empty_target,
                allowed,
                canonical_suffix,
                canonical_reason,
            )
            baseline_transparent_rgb_pixels = (
                transparent_rgb_count(weapon) + transparent_rgb_count(empty)
            )
            repair_required = baseline.status != "reviewed" or baseline_transparent_rgb_pixels != 0
            baseline_failures += int(repair_required)
            repaired_weapon, repaired_empty = lock_common_region(
                weapon,
                empty,
                weapon_target,
                empty_target,
                allowed,
                canonical_suffix,
                weapon_suffix,
                empty_suffix,
            )
            analysis = analyze_pair(
                raw_id,
                item,
                weapon_suffix,
                empty_suffix,
                repaired_weapon,
                repaired_empty,
                weapon_target,
                empty_target,
                allowed,
                canonical_suffix,
                canonical_reason,
            )

            if analysis.status != "reviewed":
                raise ValueError(
                    f"deterministic pair lock failed for {item.item_id} {weapon_suffix}/{empty_suffix}: "
                    f"{analysis.changed_outside_allowed} forbidden changed pixels"
                )

            weapon_asset_path = icon_root / f"{item.icon_name}{weapon_suffix}.png"
            empty_asset_path = icon_root / f"{item.icon_name}{empty_suffix}.png"
            weapon_target_path = target_root / f"{item.icon_name}{weapon_suffix}_target.png"
            empty_target_path = target_root / f"{item.icon_name}{empty_suffix}_target.png"
            weapon_target_path.parent.mkdir(parents=True, exist_ok=True)

            if repair_required:
                repaired_weapon.save(weapon_asset_path, optimize=False)
                repaired_empty.save(empty_asset_path, optimize=False)
                weapon_target.save(weapon_target_path, optimize=False)
                empty_target.save(empty_target_path, optimize=False)
            else:
                shutil.copyfile(authored[(raw_id, weapon_suffix)].asset_path, weapon_asset_path)
                shutil.copyfile(authored[(raw_id, empty_suffix)].asset_path, empty_asset_path)
                shutil.copyfile(authored[(raw_id, weapon_suffix)].target_mask_path, weapon_target_path)
                shutil.copyfile(authored[(raw_id, empty_suffix)].target_mask_path, empty_target_path)

            analyses.append(analysis)
            common = common_region_mask(weapon_target, empty_target, allowed)
            pair_records[raw_id][f"{weapon_suffix}_{empty_suffix}"] = {
                **asdict(analysis),
                "allowed_change_mask_sha256_raw": sha256_mask(allowed),
                "common_region_sha256_raw": sha256_mask(common),
                "baseline_changed_outside_allowed": baseline.changed_outside_allowed,
                "baseline_common_rgba_exact": baseline.common_rgba_exact,
                "baseline_transparent_rgb_pixels": baseline_transparent_rgb_pixels,
                "repair_required": repair_required,
                "weapon_target_sha256": sha256_file(weapon_target_path),
                "empty_target_sha256": sha256_file(empty_target_path),
                "review_status": "pending",
            }

    for analysis in analyses:
        item = items[analysis.raw_id]
        weapon_path = icon_root / f"{item.icon_name}{analysis.weapon_suffix}.png"
        empty_path = icon_root / f"{item.icon_name}{analysis.empty_suffix}.png"
        weapon = Image.open(weapon_path).convert("RGBA")
        empty = Image.open(empty_path).convert("RGBA")
        inputs = load_pair_inputs(
            analysis.raw_id,
            item,
            analysis.weapon_suffix,
            analysis.empty_suffix,
            mappings,
            authored,
        )
        weapon_target = Image.open(
            target_root / f"{item.icon_name}{analysis.weapon_suffix}_target.png"
        ).convert("RGBA")
        empty_target = Image.open(
            target_root / f"{item.icon_name}{analysis.empty_suffix}_target.png"
        ).convert("RGBA")
        allowed = derive_validated_pose_change_mask(inputs[4], inputs[5], weapon_target, empty_target)
        common = common_region_mask(weapon_target, empty_target, allowed)
        evidence = save_pair_evidence(
            pair_root,
            item,
            analysis,
            weapon,
            empty,
            allowed,
            common,
            icon_root,
        )
        record = pair_records[analysis.raw_id][f"{analysis.weapon_suffix}_{analysis.empty_suffix}"]

        for field, path in evidence.items():
            record[field] = path.relative_to(staging_root).as_posix()
            record[f"{field}_sha256"] = sha256_file(path)

        record["weapon_asset_sha256"] = sha256_file(weapon_path)
        record["empty_asset_sha256"] = sha256_file(empty_path)
        family_equipped_reviews[analysis.raw_id].append(evidence["equipped_review"])

        if analysis.allowed_pixels > 0:
            label = f"{item.item_id} {analysis.weapon_suffix}/{analysis.empty_suffix}"
            seam_review_entries.append((label, evidence["seam_review"]))
            difference_review_entries.append((label, evidence["difference_review"]))

    family_reviews: dict[int, dict[str, str]] = {}
    family_paths: list[Path] = []

    for raw_id in raw_ids:
        item = items[raw_id]
        inventory_path = authored[(raw_id, "v1")].inventory_asset_path
        family_path = pair_root / "reviews" / f"{item.icon_name}_all_pose_pairs.png"
        save_family_contact_sheet(
            item,
            Image.open(inventory_path).convert("RGBA"),
            family_equipped_reviews[raw_id],
            family_path,
        )
        family_paths.append(family_path)
        family_reviews[raw_id] = {
            "contact_sheet": family_path.relative_to(staging_root).as_posix(),
            "contact_sheet_sha256": sha256_file(family_path),
        }

    catalogue_paths = save_catalogue_pages(family_paths, pair_root / "reviews")
    seam_catalogue_paths = save_detail_catalogue_pages(
        seam_review_entries,
        pair_root / "reviews",
        "seams",
    )
    difference_catalogue_paths = save_detail_catalogue_pages(
        difference_review_entries,
        pair_root / "reviews",
        "differences",
    )

    report = {
        "format_version": 1,
        "kind": "mm9_armor_pose_pair_staging",
        "goal": DEFAULT_GOAL.relative_to(REPOSITORY_ROOT).as_posix(),
        "goal_sha256": sha256_file(DEFAULT_GOAL),
        "manifest": DEFAULT_MANIFEST.name,
        "manifest_sha256_before_repair": sha256_file(DEFAULT_MANIFEST),
        "item_count": len(raw_ids),
        "pair_count": len(analyses),
        "baseline_failed_pair_count": baseline_failures,
        "preserved_pair_count": len(analyses) - baseline_failures,
        "review_status": "pending",
        "items": pair_records,
        "family_reviews": family_reviews,
        "catalogues": [
            {
                "asset": path.relative_to(staging_root).as_posix(),
                "asset_sha256": sha256_file(path),
            }
            for path in catalogue_paths + seam_catalogue_paths + difference_catalogue_paths
        ],
    }
    write_yaml(staging_root / "pose_pair_review.yml", report)
    (staging_root / "pose_pair_report.json").write_text(
        json.dumps([asdict(analysis) for analysis in analyses], indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"staged {len(raw_ids)} MM9 armor families and {len(analyses)} pose pairs for review")
    return 0


def approve_staged(arguments: argparse.Namespace) -> int:
    review_path = arguments.staging_root / "pose_pair_review.yml"
    document = read_yaml(review_path)

    if document.get("review_status") != "pending":
        raise ValueError("staged pose pairs are not awaiting review")
    if not arguments.reviewer_note.strip():
        raise ValueError("--reviewer-note must describe the completed visual review")

    items = document.get("items")

    if not isinstance(items, dict):
        raise ValueError("staged pose-pair document has invalid items")

    for pairs in items.values():
        if not isinstance(pairs, dict):
            raise ValueError("staged pose-pair document has invalid pair records")
        for pair in pairs.values():
            if not isinstance(pair, dict) or pair.get("status") != "reviewed":
                raise ValueError("cannot approve a pair which failed deterministic verification")
            pair["review_status"] = "reviewed"
            pair["reviewer_note"] = arguments.reviewer_note.strip()

    document["review_status"] = "reviewed"
    document["reviewer_note"] = arguments.reviewer_note.strip()
    write_yaml(review_path, document)
    print(f"approved {document['pair_count']} staged pose pairs after visual review")
    return 0


def manifest_relative(path: Path) -> str:
    return path.relative_to(DEFAULT_MANIFEST.parent).as_posix()


def update_variant_manifest(
    variant: dict[str, Any],
    asset_path: Path,
    equipped_preview_path: Path,
    canonical_suffix: str,
) -> None:
    image = Image.open(asset_path).convert("RGBA")
    content_hash = sha256_file(asset_path)
    variant["asset_sha256"] = content_hash
    variant["content_sha256"] = content_hash
    variant["alpha_sha256"] = hashlib.sha256(image.getchannel("A").tobytes()).hexdigest()
    variant["equipped_preview_sha256"] = sha256_file(equipped_preview_path)
    suffix_note = f"; pose-pair common region locked deterministically to {canonical_suffix}"
    if suffix_note not in str(variant["postprocess"]):
        variant["postprocess"] = str(variant["postprocess"]) + suffix_note


def promoted_evidence_path(staging_root: Path, staged_path: Path) -> Path:
    return DEFAULT_GENERATED_ROOT / "pose_pairs" / staged_path.relative_to(staging_root / "pose_pairs")


def validate_staged(arguments: argparse.Namespace) -> int:
    staging_root = arguments.staging_root
    review_document = read_yaml(staging_root / "pose_pair_review.yml")

    if review_document.get("review_status") != "reviewed":
        raise ValueError("staged pose pairs must be visually reviewed")

    items, mappings, authored = armor_items(allow_stale_goal_hash=True)
    expected_raw_ids = selected_raw_ids(arguments.item_id, items)
    staged_items = review_document.get("items")
    family_reviews = review_document.get("family_reviews")
    catalogues = review_document.get("catalogues")

    if not isinstance(staged_items, dict) or {int(value) for value in staged_items} != set(expected_raw_ids):
        raise ValueError("staged armor selection does not match the requested validation")
    if not isinstance(family_reviews, dict) or {int(value) for value in family_reviews} != set(expected_raw_ids):
        raise ValueError("staged family-review selection does not match the requested validation")
    if not isinstance(catalogues, list) or not catalogues:
        raise ValueError("staged pose-pair catalogues are missing")

    validated_pairs = 0

    for raw_id in expected_raw_ids:
        item = items[raw_id]
        staged_pairs = staged_items[raw_id] if raw_id in staged_items else staged_items[str(raw_id)]

        if not isinstance(staged_pairs, dict) or set(staged_pairs) != {
            f"{weapon}_{empty}" for weapon, empty in PAIR_SUFFIXES
        }:
            raise ValueError(f"armor {item.item_id} does not have the exact five staged pose pairs")

        for weapon_suffix, empty_suffix in PAIR_SUFFIXES:
            pair_key = f"{weapon_suffix}_{empty_suffix}"
            pair = staged_pairs[pair_key]

            if pair.get("review_status") != "reviewed" or pair.get("status") != "reviewed":
                raise ValueError(f"armor {item.item_id} {pair_key} has not passed review")

            weapon_path = staging_root / "icons" / f"{item.icon_name}{weapon_suffix}.png"
            empty_path = staging_root / "icons" / f"{item.icon_name}{empty_suffix}.png"
            weapon_target_path = staging_root / "targets" / f"{item.icon_name}{weapon_suffix}_target.png"
            empty_target_path = staging_root / "targets" / f"{item.icon_name}{empty_suffix}_target.png"
            hashed_paths = (
                (weapon_path, "weapon_asset_sha256"),
                (empty_path, "empty_asset_sha256"),
                (weapon_target_path, "weapon_target_sha256"),
                (empty_target_path, "empty_target_sha256"),
            )

            for path, hash_field in hashed_paths:
                if not path.is_file() or sha256_file(path) != str(pair[hash_field]):
                    raise ValueError(f"armor {item.item_id} {pair_key} staged {hash_field} mismatch")

            inputs = load_pair_inputs(
                raw_id,
                item,
                weapon_suffix,
                empty_suffix,
                mappings,
                authored,
            )
            weapon = Image.open(weapon_path).convert("RGBA")
            empty = Image.open(empty_path).convert("RGBA")
            weapon_target = Image.open(weapon_target_path).convert("RGBA")
            empty_target = Image.open(empty_target_path).convert("RGBA")
            allowed = derive_validated_pose_change_mask(inputs[4], inputs[5], weapon_target, empty_target)
            analysis = analyze_pair(
                raw_id,
                item,
                weapon_suffix,
                empty_suffix,
                weapon,
                empty,
                weapon_target,
                empty_target,
                allowed,
                str(pair["canonical_suffix"]),
                str(pair["canonical_reason"]),
            )

            if analysis.status != "reviewed":
                raise ValueError(f"armor {item.item_id} {pair_key} fails deterministic pair validation")
            if weapon.getchannel("A").tobytes() != weapon_target.getchannel("A").tobytes():
                raise ValueError(f"armor {item.item_id} {weapon_suffix} staged alpha mismatch")
            if empty.getchannel("A").tobytes() != empty_target.getchannel("A").tobytes():
                raise ValueError(f"armor {item.item_id} {empty_suffix} staged alpha mismatch")

            for evidence_field in (
                "allowed_change_mask",
                "common_region_mask",
                "isolated_review",
                "equipped_review",
                "blink_review",
                "difference_review",
                "seam_review",
            ):
                evidence_path = staging_root / str(pair[evidence_field])

                if not evidence_path.is_file() or sha256_file(evidence_path) != str(
                    pair[f"{evidence_field}_sha256"]
                ):
                    raise ValueError(f"armor {item.item_id} {pair_key} staged {evidence_field} mismatch")

            render_equipped_pair(item, int(weapon_suffix[1]) - 1, staging_root / "icons")
            validated_pairs += 1

        family_review = family_reviews[raw_id] if raw_id in family_reviews else family_reviews[str(raw_id)]
        contact_sheet = staging_root / str(family_review["contact_sheet"])

        if not contact_sheet.is_file() or sha256_file(contact_sheet) != str(
            family_review["contact_sheet_sha256"]
        ):
            raise ValueError(f"armor {item.item_id} staged family contact-sheet mismatch")

    for catalogue in catalogues:
        catalogue_path = staging_root / str(catalogue["asset"])

        if not catalogue_path.is_file() or sha256_file(catalogue_path) != str(catalogue["asset_sha256"]):
            raise ValueError(f"staged catalogue hash mismatch: {catalogue_path}")

    print(f"validated {len(expected_raw_ids)} staged armor families and {validated_pairs} pose pairs")
    return 0


def promote_staged(arguments: argparse.Namespace) -> int:
    validate_staged(arguments)
    staging_root = arguments.staging_root
    review_document = read_yaml(staging_root / "pose_pair_review.yml")

    if review_document.get("review_status") != "reviewed":
        raise ValueError("staged pose pairs must be visually reviewed before promotion")

    items, _mappings, authored = armor_items(allow_stale_goal_hash=True)
    expected_raw_ids = selected_raw_ids(arguments.item_id, items)
    staged_items = review_document.get("items")
    family_reviews = review_document.get("family_reviews")
    catalogues = review_document.get("catalogues")

    if not isinstance(staged_items, dict) or {int(value) for value in staged_items} != set(expected_raw_ids):
        raise ValueError("staged armor selection does not match the requested atomic promotion")
    if not isinstance(family_reviews, dict) or {int(value) for value in family_reviews} != set(expected_raw_ids):
        raise ValueError("staged armor family-review selection is incomplete")
    if not isinstance(catalogues, list) or not catalogues:
        raise ValueError("staged armor review catalogues are missing")

    manifest = read_yaml(DEFAULT_MANIFEST)
    manifest_items = manifest.get("items")

    if not isinstance(manifest_items, dict):
        raise ValueError("generated equipment manifest has invalid items")

    for raw_id in expected_raw_ids:
        item = items[raw_id]
        staged_pairs = staged_items[raw_id] if raw_id in staged_items else staged_items[str(raw_id)]

        if len(staged_pairs) != 5 or any(pair.get("review_status") != "reviewed" for pair in staged_pairs.values()):
            raise ValueError(f"armor {item.item_id} does not have five reviewed staged pairs")

        item_manifest = manifest_items[raw_id] if raw_id in manifest_items else manifest_items[str(raw_id)]
        variant_manifest = item_manifest["variants"]
        promoted_pair_records: dict[str, Any] = {}
        family_replacements: list[tuple[Path, Path]] = []
        variant_updates: list[tuple[str, Path, Path, str]] = []

        for pair_key, pair in staged_pairs.items():
            weapon_suffix = str(pair["weapon_suffix"])
            empty_suffix = str(pair["empty_suffix"])
            canonical_suffix = str(pair["canonical_suffix"])

            for suffix, hash_field in (
                (weapon_suffix, "weapon_asset_sha256"),
                (empty_suffix, "empty_asset_sha256"),
            ):
                staged_asset = staging_root / "icons" / f"{item.icon_name}{suffix}.png"
                staged_target = staging_root / "targets" / f"{item.icon_name}{suffix}_target.png"
                generated_asset = DEFAULT_GENERATED_ROOT / f"{item.icon_name}{suffix}.png"
                active_asset = DEFAULT_WORLD_ICON_ROOT / f"{item.icon_name}{suffix}.png"
                target_hash_field = "weapon_target_sha256" if suffix == weapon_suffix else "empty_target_sha256"

                if sha256_file(staged_asset) != str(pair[hash_field]):
                    raise ValueError(f"staged hash mismatch for {item.item_id} {suffix}")
                if sha256_file(staged_target) != str(pair[target_hash_field]):
                    raise ValueError(f"staged target hash mismatch for {item.item_id} {suffix}")

                target_path = authored[(raw_id, suffix)].target_mask_path
                family_replacements.extend((
                    (staged_asset, generated_asset),
                    (staged_asset, active_asset),
                    (staged_target, target_path),
                ))
                variant_manifest[suffix]["target_mask_sha256"] = sha256_file(staged_target)

            promoted_pair = dict(pair)

            for field in (
                "allowed_change_mask",
                "common_region_mask",
                "isolated_review",
                "equipped_review",
                "blink_review",
                "difference_review",
                "seam_review",
            ):
                staged_evidence = staging_root / str(pair[field])
                target_evidence = promoted_evidence_path(staging_root, staged_evidence)
                family_replacements.append((staged_evidence, target_evidence))
                promoted_pair[field] = manifest_relative(target_evidence)

            promoted_pair["assembly"] = (
                "exact audited target alpha; transparent RGB clear; exact canonical RGBA copy outside the mapped "
                "native weapon-side arm change mask"
            )
            promoted_pair["goal"] = DEFAULT_GOAL.relative_to(REPOSITORY_ROOT).as_posix()
            promoted_pair["goal_sha256"] = sha256_file(DEFAULT_GOAL)
            promoted_pair_records[pair_key] = promoted_pair

            equipped_pair_path = staging_root / str(pair["equipped_review"])
            expected_equipped_path = DEFAULT_GENERATED_ROOT / "pose_pairs" / "reviews" / (
                f"{weapon_name(item, weapon_suffix)}_{empty_suffix}_equipped.png"
            )
            if promoted_evidence_path(staging_root, equipped_pair_path) != expected_equipped_path:
                raise ValueError(f"unexpected equipped review path for {item.item_id} {pair_key}")
            equipped_pair = Image.open(equipped_pair_path).convert("RGBA")
            half_width = equipped_pair.width // 2
            label_height = 18
            weapon_preview = equipped_pair.crop((0, label_height, half_width, equipped_pair.height))
            empty_preview = equipped_pair.crop((half_width, label_height, equipped_pair.width, equipped_pair.height))

            for suffix, preview in ((weapon_suffix, weapon_preview), (empty_suffix, empty_preview)):
                authored_variant = authored[(raw_id, suffix)]
                preview_path = authored_variant.equipped_preview_path
                staged_preview_path = staging_root / "promoted_previews" / f"{item.icon_name}{suffix}.png"
                staged_preview_path.parent.mkdir(parents=True, exist_ok=True)
                preview.save(staged_preview_path, optimize=False)
                family_replacements.append((staged_preview_path, preview_path))
                asset_path = DEFAULT_GENERATED_ROOT / f"{item.icon_name}{suffix}.png"
                variant_updates.append((suffix, asset_path, preview_path, canonical_suffix))

        family_review = family_reviews[raw_id] if raw_id in family_reviews else family_reviews[str(raw_id)]
        staged_contact_sheet = staging_root / str(family_review["contact_sheet"])

        if sha256_file(staged_contact_sheet) != str(family_review["contact_sheet_sha256"]):
            raise ValueError(f"armor {item.item_id} staged contact-sheet hash mismatch")

        promoted_contact_sheet = promoted_evidence_path(staging_root, staged_contact_sheet)
        family_replacements.append((staged_contact_sheet, promoted_contact_sheet))
        copy_family_files_atomically(family_replacements)

        for suffix, asset_path, preview_path, canonical_suffix in variant_updates:
            update_variant_manifest(variant_manifest[suffix], asset_path, preview_path, canonical_suffix)

        item_manifest["pose_pairs"] = promoted_pair_records
        item_manifest["pose_pair_review_status"] = "reviewed"
        item_manifest["pose_pair_contact_sheet"] = manifest_relative(promoted_contact_sheet)
        item_manifest["pose_pair_contact_sheet_sha256"] = sha256_file(promoted_contact_sheet)

    promoted_catalogues = []

    for catalogue in catalogues:
        if not isinstance(catalogue, dict):
            raise ValueError("staged armor catalogue record is invalid")

        staged_catalogue = staging_root / str(catalogue["asset"])

        if sha256_file(staged_catalogue) != str(catalogue["asset_sha256"]):
            raise ValueError(f"staged armor catalogue hash mismatch: {staged_catalogue}")

        promoted_catalogue = promoted_evidence_path(staging_root, staged_catalogue)
        copy_file_atomically(staged_catalogue, promoted_catalogue)
        promoted_catalogues.append({
            "asset": manifest_relative(promoted_catalogue),
            "asset_sha256": sha256_file(promoted_catalogue),
        })

    manifest["pose_pair_goal"] = DEFAULT_GOAL.relative_to(REPOSITORY_ROOT).as_posix()
    manifest["pose_pair_goal_sha256"] = sha256_file(DEFAULT_GOAL)
    manifest["pose_pair_review_status"] = "reviewed"
    manifest["pose_pair_catalogues"] = promoted_catalogues

    write_yaml(DEFAULT_MANIFEST, manifest)
    print(f"promoted {len(expected_raw_ids)} reviewed MM9 armor families atomically")
    return 0


def in_game_review_path(review_name: str) -> Path:
    return DEFAULT_GENERATED_ROOT / "pose_pairs" / "reviews" / "in_game" / f"{review_name}.png"


def validate_in_game_review_records(manifest: dict[str, Any]) -> list[str]:
    records = manifest.get("pose_pair_in_game_reviews")
    failures: list[str] = []

    if not isinstance(records, dict) or set(records) != set(REQUIRED_IN_GAME_REVIEWS):
        return ["manifest does not contain the exact four required in-game pose reviews"]

    for review_name, (item_id, right_hand_state) in REQUIRED_IN_GAME_REVIEWS.items():
        record = records.get(review_name)
        expected_fields = {"item_id", "right_hand_state", "asset", "asset_sha256", "reviewer_note"}

        if not isinstance(record, dict) or set(record) != expected_fields:
            failures.append(f"{review_name}: invalid in-game review record")
            continue
        if record["item_id"] != item_id or record["right_hand_state"] != right_hand_state:
            failures.append(f"{review_name}: in-game review identity mismatch")

        review_path = DEFAULT_MANIFEST.parent / str(record["asset"])

        if not review_path.is_file() or sha256_file(review_path) != str(record["asset_sha256"]):
            failures.append(f"{review_name}: in-game review hash mismatch")
            continue

        try:
            with Image.open(review_path) as image:
                image.verify()
        except (OSError, SyntaxError) as exception:
            failures.append(f"{review_name}: invalid in-game PNG: {exception}")

        if not str(record["reviewer_note"]).strip():
            failures.append(f"{review_name}: in-game review note is empty")

    return failures


def record_in_game_reviews(arguments: argparse.Namespace) -> int:
    if not arguments.reviewer_note.strip():
        raise ValueError("--reviewer-note must describe the completed in-game review")

    manifest = read_yaml(DEFAULT_MANIFEST)

    if manifest.get("pose_pair_review_status") != "reviewed":
        raise ValueError("pose pairs must be promoted before recording in-game review")

    records: dict[str, dict[str, Any]] = {}

    for review_name, (item_id, right_hand_state) in REQUIRED_IN_GAME_REVIEWS.items():
        path = in_game_review_path(review_name)

        if not path.is_file():
            raise ValueError(f"required in-game review is missing: {path}")

        with Image.open(path) as image:
            image.verify()

        records[review_name] = {
            "item_id": item_id,
            "right_hand_state": right_hand_state,
            "asset": manifest_relative(path),
            "asset_sha256": sha256_file(path),
            "reviewer_note": arguments.reviewer_note.strip(),
        }

    manifest["pose_pair_in_game_reviews"] = records
    write_yaml(DEFAULT_MANIFEST, manifest)
    print("recorded four reviewed in-game MM9 armor pose screenshots")
    return 0


def verify_only(arguments: argparse.Namespace) -> int:
    items, mappings, authored = armor_items()
    raw_ids = selected_raw_ids(arguments.item_id, items)
    manifest = read_yaml(DEFAULT_MANIFEST)
    manifest_items = manifest.get("items")
    failures: list[str] = []
    pair_count = 0
    foot_masks = foot_exclusion_masks()
    engine_offsets = paperdoll.read_complex_picture_offsets(
        paperdoll.ENGINE_TABLE_ROOT / "complex_item_pictures.txt"
    )

    if not isinstance(manifest_items, dict):
        raise ValueError("generated equipment manifest has invalid items")

    if not arguments.item_id:
        failures.extend(validate_in_game_review_records(manifest))

    for raw_id in raw_ids:
        item = items[raw_id]
        item_manifest = manifest_items[raw_id] if raw_id in manifest_items else manifest_items[str(raw_id)]
        pose_pairs = item_manifest.get("pose_pairs")

        if not isinstance(pose_pairs, dict) or len(pose_pairs) != 5:
            failures.append(f"{item.item_id}: missing five pair-level manifest records")
            continue

        for weapon_suffix, empty_suffix in PAIR_SUFFIXES:
            pair_count += 1
            pair_key = f"{weapon_suffix}_{empty_suffix}"
            pair = pose_pairs.get(pair_key)

            if not isinstance(pair, dict) or pair.get("review_status") != "reviewed":
                failures.append(f"{item.item_id} {pair_key}: pair is not reviewed")
                continue

            inputs = load_pair_inputs(
                raw_id,
                item,
                weapon_suffix,
                empty_suffix,
                mappings,
                authored,
            )
            weapon_path = DEFAULT_GENERATED_ROOT / f"{item.icon_name}{weapon_suffix}.png"
            empty_path = DEFAULT_GENERATED_ROOT / f"{item.icon_name}{empty_suffix}.png"
            weapon = Image.open(weapon_path).convert("RGBA")
            empty = Image.open(empty_path).convert("RGBA")
            allowed = derive_validated_pose_change_mask(inputs[4], inputs[5], inputs[2], inputs[3])
            analysis = analyze_pair(
                raw_id,
                item,
                weapon_suffix,
                empty_suffix,
                weapon,
                empty,
                inputs[2],
                inputs[3],
                allowed,
                str(pair["canonical_suffix"]),
                str(pair["canonical_reason"]),
            )

            if analysis.status != "reviewed":
                failures.append(
                    f"{item.item_id} {pair_key}: {analysis.changed_outside_allowed} forbidden differences"
                )

            for field in (
                "allowed_pixels",
                "common_pixels",
                "changed_pixels",
                "changed_inside_allowed",
                "changed_outside_allowed",
                "target_alpha_changed_outside_allowed",
                "common_rgba_exact",
            ):
                if pair.get(field) != getattr(analysis, field):
                    failures.append(f"{item.item_id} {pair_key}: stale {field} record")

            common = common_region_mask(inputs[2], inputs[3], allowed)

            if pair.get("allowed_change_mask_sha256_raw") != sha256_mask(allowed):
                failures.append(f"{item.item_id} {pair_key}: raw allowed-mask hash mismatch")
            if pair.get("common_region_sha256_raw") != sha256_mask(common):
                failures.append(f"{item.item_id} {pair_key}: raw common-region hash mismatch")

            allowed_path = DEFAULT_MANIFEST.parent / str(pair["allowed_change_mask"])
            common_path = DEFAULT_MANIFEST.parent / str(pair["common_region_mask"])

            if not np.array_equal(alpha_mask(Image.open(allowed_path)), allowed):
                failures.append(f"{item.item_id} {pair_key}: persisted allowed-mask pixels mismatch")
            if not np.array_equal(alpha_mask(Image.open(common_path)), common):
                failures.append(f"{item.item_id} {pair_key}: persisted common-region pixels mismatch")

            for suffix, image in ((weapon_suffix, weapon), (empty_suffix, empty)):
                target = inputs[2] if suffix == weapon_suffix else inputs[3]
                if image.getchannel("A").tobytes() != target.getchannel("A").tobytes():
                    failures.append(f"{item.item_id} {suffix}: target alpha mismatch")
                pixels = image_array(image)
                transparent = pixels[:, :, 3] == 0
                opaque = ~transparent
                magenta = (
                    (pixels[:, :, 0] == 255)
                    & (pixels[:, :, 1] == 0)
                    & (pixels[:, :, 2] == 255)
                    & opaque
                )
                if np.any(pixels[transparent][:, :3] != 0):
                    failures.append(f"{item.item_id} {suffix}: nonzero RGB under transparency")
                if np.any(magenta):
                    failures.append(f"{item.item_id} {suffix}: opaque chroma-key magenta")

                doll_type = int(suffix[1]) - 1
                point = engine_offsets[mappings[raw_id].reference_item_id][doll_type]
                if equipment.alpha_overlap_count(image, point, foot_masks[doll_type]) != 0:
                    failures.append(f"{item.item_id} {suffix}: foot/footwear exclusion overlap")

                active_path = DEFAULT_WORLD_ICON_ROOT / f"{item.icon_name}{suffix}.png"
                generated_path = DEFAULT_GENERATED_ROOT / f"{item.icon_name}{suffix}.png"
                if not active_path.is_file() or sha256_file(active_path) != sha256_file(generated_path):
                    failures.append(f"{item.item_id} {suffix}: active/generated asset mismatch")

            try:
                render_equipped_pair(item, int(weapon_suffix[1]) - 1, DEFAULT_GENERATED_ROOT)
            except ValueError as exception:
                failures.append(str(exception))

    if failures:
        raise ValueError("pose-pair verification failed:\n" + "\n".join(failures))

    print(f"verified {len(raw_ids)} MM9 armor families and {pair_count} reviewed pose pairs")
    return 0


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    parser.add_argument("--replace-staging", action="store_true", help="replace the exact tool-owned staging root")
    parser.add_argument("--item-id", action="append", type=int, help="global MM9 armor item id; may be repeated")
    parser.add_argument("--reviewer-note", default="", help="required with --approve-staged")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage-repairs", action="store_true")
    mode.add_argument("--approve-staged", action="store_true")
    mode.add_argument("--validate-staged", action="store_true")
    mode.add_argument("--promote-staged", action="store_true")
    mode.add_argument("--record-in-game-reviews", action="store_true")
    mode.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    if arguments.stage_repairs:
        return stage_repairs(arguments)
    if arguments.approve_staged:
        return approve_staged(arguments)
    if arguments.validate_staged:
        return validate_staged(arguments)
    if arguments.promote_staged:
        return promote_staged(arguments)
    if arguments.record_in_game_reviews:
        return record_in_game_reviews(arguments)
    return verify_only(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
