"""Measure the PC01 shield-hand variants against native geometry and their open-hand sibling."""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
INVENTORY = REVIEW.parent
OUT = HERE / "prepared/doll_01/in_situ_left_closed"
SHARED = HERE / "prepared/doll_01/shared_bracer_shield"
OPEN = HERE / "prepared/doll_01/in_situ_left_open"
sys.path.insert(0, str(INVENTORY))
import queue as queue_module  # noqa: E402
import registration  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def premultiplied_resize(image, size):
    return image.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def repair_tiny_confirmed_fringe(image):
    """Replace RGB of near-invisible purple edge pixels; retain alpha and all other pixels."""
    pixels = np.asarray(image).copy()
    corrected = []
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue, alpha = (int(value) for value in pixels[y, x])
            if not (0 < alpha <= 16 and min(red, blue) - green > 40):
                continue
            nearest = None
            for radius in range(1, 7):
                for sample_y in range(max(0, y - radius), min(image.height, y + radius + 1)):
                    for sample_x in range(max(0, x - radius), min(image.width, x + radius + 1)):
                        if pixels[sample_y, sample_x, 3] >= 128:
                            nearest = pixels[sample_y, sample_x, :3]
                            break
                    if nearest is not None:
                        break
                if nearest is not None:
                    break
            if nearest is None:
                raise ValueError(f"Could not repair confirmed fringe pixel {(x, y)}")
            pixels[y, x, :3] = nearest
            corrected.append([x, y])
    if len(corrected) > 2:
        raise ValueError(f"Unexpectedly broad fringe repair: {corrected}")
    return Image.fromarray(pixels, "RGBA"), corrected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shared-bracer", action="store_true")
    arguments = parser.parse_args()
    folder = SHARED if arguments.shared_bracer else OUT
    manifest = json.loads((folder / "manifest.json").read_text())
    raw_path = folder / "raw_shield_v1.png"
    with Image.open(raw_path) as opened:
        raw = opened.convert("RGBA")
    input_width, input_height = manifest["frame_size"]
    if abs(raw.width / input_width - raw.height / input_height) > .02:
        raise ValueError("Return changed the guide aspect")
    flat = premultiplied_resize(raw, (input_width, input_height))
    crop_x, crop_y = manifest["frame_position"]
    left, top, right, bottom = manifest["crop_x2"]
    scale = manifest["scale"]
    region = flat.crop((crop_x, crop_y, crop_x + (right - left) * scale,
                        crop_y + (bottom - top) * scale))
    stage_region = premultiplied_resize(region, (right - left, bottom - top))
    target_x, target_y = manifest["target_position_x2"]
    target_width, target_height = manifest["target_size_x2"]
    local_x, local_y = target_x - left, target_y - top
    sprite = stage_region.crop((local_x, local_y, local_x + target_width, local_y + target_height))
    raw_sprite_path = folder / "pc01lho_generated_v1.png"
    sprite.save(raw_sprite_path, optimize=True)
    corrected_fringe = []
    if arguments.shared_bracer:
        with Image.open(folder / "pc01lho_shared_bracer_seed.png") as opened:
            seed = opened.convert("RGBA")
        protected = np.asarray(sprite).copy()
        protected[:manifest["bracer_end_x2"], :, :] = np.asarray(seed)[:manifest["bracer_end_x2"], :, :]
        sprite = Image.fromarray(protected, "RGBA")
        sprite, corrected_fringe = repair_tiny_confirmed_fringe(sprite)
    sprite_path = folder / ("pc01lho_shared_bracer_v1.png" if arguments.shared_bracer else "pc01lho_in_situ_v1.png")
    sprite.save(sprite_path, optimize=True)
    queue = queue_module.Queue()
    identifier = "engine--icons--pc01lho.bmp"
    member = queue.members[identifier][1]
    target = queue.targets[member["target"]]
    measured = registration.measurements(member, target, sprite_path)
    flags = {profile: result["failures"] for profile, result in measured["profiles"].items()
             if result["failures"]}

    data = json.loads((REVIEW / "catalog.js").read_text()
                      .removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))
    assets = data["assets"]
    hand_region = None
    if arguments.shared_bracer:
        with Image.open(REVIEW / unquote(assets["pc01lho"]["native"])) as opened:
            native = opened.convert("RGBA").resize(sprite.size, Image.Resampling.NEAREST)
        cut = manifest["bracer_end_x2"]
        restored_alpha = np.asarray(sprite.getchannel("A"))[cut:]
        original_alpha = np.asarray(native.getchannel("A"))[cut:]
        hand_region = {}
        for threshold in (16, 128):
            restored_mask = restored_alpha >= threshold
            original_mask = original_alpha >= threshold
            intersection = int(np.count_nonzero(restored_mask & original_mask))
            union = int(np.count_nonzero(restored_mask | original_mask))
            hand_region[str(threshold)] = {
                "silhouette_iou": round(intersection / union, 6),
                "occupied_area_ratio": round(np.count_nonzero(restored_mask) /
                                             np.count_nonzero(original_mask), 6),
            }
    with Image.open(REVIEW / unquote(assets["pc01bod"]["candidate"])) as opened:
        body = opened.convert("RGBA")
    with Image.open(REVIEW / unquote(assets["pc01lho"]["candidate"])) as opened:
        old_shield = opened.convert("RGBA")
    with Image.open(OPEN / "pc01lhu_in_situ_v2.png") as opened:
        open_arm = opened.convert("RGBA")
    stages = []
    for arm, position in ((open_arm, (276, 300)), (old_shield, (264, 300)), (sprite, (264, 300))):
        stage = Image.new("RGBA", (350, 756), "#253137")
        stage.alpha_composite(body, (60, 66))
        stage.alpha_composite(arm, position)
        stages.append(stage)
    comparison = Image.new("RGBA", (3 * 350 + 2 * 12, 756), "#253137")
    for index, stage in enumerate(stages):
        comparison.alpha_composite(stage, (index * 362, 0))
    comparison_path = folder / "canonical_open_vs_old_and_new_shield.png"
    comparison.save(comparison_path, optimize=True)
    item_context = None
    if arguments.shared_bracer:
        shield_item = next(entry for entry in data["items"] if entry["id"] == 99)
        item_art = assets[shield_item["icon"]]
        item_path = REVIEW / unquote(item_art["candidate"] or item_art["native"])
        with Image.open(item_path) as opened:
            shield_picture = opened.convert("RGBA")
        if not item_art["candidate"]:
            shield_picture = shield_picture.resize((shield_picture.width * 2, shield_picture.height * 2),
                                                   Image.Resampling.NEAREST)
        with Image.open(REVIEW / unquote(assets["pc01rhd"]["candidate"])) as opened:
            right_open = opened.convert("RGBA")
        doll_type = data["types"]["0"]
        item_x = (doll_type["leftClosedX"] + doll_type["shieldX"] - shield_item["equipX"]) * 2
        item_y = (doll_type["leftClosedY"] + doll_type["shieldY"] - shield_item["equipY"]) * 2
        pair_with_item = Image.new("RGBA", (712, 756), "#253137")
        for index, arm in enumerate((old_shield, sprite)):
            stage = Image.new("RGBA", (350, 756), "#253137")
            stage.alpha_composite(body, (60, 66))
            stage.alpha_composite(right_open, (58, 220))
            stage.alpha_composite(arm, (264, 300))
            stage.alpha_composite(shield_picture, (item_x, item_y))
            pair_with_item.alpha_composite(stage, (index * 362, 0))
        item_context_path = folder / "old_vs_shared_bracer_with_item099.png"
        pair_with_item.save(item_context_path, optimize=True)
        item_context = {"item_id": 99, "name": shield_item["name"], "position_x2": [item_x, item_y],
                        "asset": str(item_path.resolve()), "asset_sha256": digest(item_path),
                        "path": str(item_context_path.resolve()), "sha256": digest(item_context_path)}
    alpha = np.asarray(sprite.getchannel("A"))
    report = {
        "schema": "openyamm-paperdoll-shield-hand-return-v1", "target": identifier,
        "shared_bracer": arguments.shared_bracer,
        "confirmed_fringe_rgb_replaced_at": corrected_fringe,
        "raw": str(raw_path.resolve()), "raw_sha256": digest(raw_path), "raw_size": list(raw.size),
        "source_manifest_sha256": digest(folder / "manifest.json"),
        "submitted_prompt_sha256": digest(folder / "submitted_prompt_v1.txt"),
        "raw_sprite": str(raw_sprite_path.resolve()), "raw_sprite_sha256": digest(raw_sprite_path),
        "sprite": str(sprite_path.resolve()), "sprite_sha256": digest(sprite_path),
        "sprite_size": list(sprite.size), "alpha_extrema": [int(alpha.min()), int(alpha.max())],
        "registration_flags": flags, "registration_profiles": measured["profiles"],
        "hand_region_from_row_x2": manifest["bracer_end_x2"] if arguments.shared_bracer else None,
        "hand_region_measurements": hand_region,
        "comparison": str(comparison_path.resolve()), "comparison_sha256": digest(comparison_path),
        "shield_item_context": item_context,
        "visual_approval": False,
        "note": "The shared-bracer version preserves the seed's top 48 rows exactly and takes its hand from imagegen. "
                "Registration is a guard, not approval; all seams and in-context poses still need review."
                if arguments.shared_bracer else
                "This second hand pose uses the open-hand restoration as a style reference. "
                "Registration is a guard, not approval; the shield item and all seam/edge views still need review.",
    }
    (folder / "return_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"sprite_size": list(sprite.size), "alpha_extrema": report["alpha_extrema"],
                      "registration_flags": flags}, indent=2))


if __name__ == "__main__":
    main()
