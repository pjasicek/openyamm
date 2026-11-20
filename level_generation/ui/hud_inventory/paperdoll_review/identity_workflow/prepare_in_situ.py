"""Prepare a PC01 in-place forearm trial using the existing doll candidate as fixed context."""

import hashlib
import json
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageFilter


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
OUT = HERE / "prepared/doll_01/in_situ_left_open"
TARGET = "pc01lhu"
CROP = (188, 228, 348, 468)  # x2 stage pixels: shoulder, sleeve, wrist, and hand.
UPSCALE = 4
ARM_CROP = (260, 260, 344, 430)
ARM_CANVAS = (512, 768)
ARM_POSITION = (88, 44)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_catalog():
    source = (REVIEW / "catalog.js").read_text()
    return json.loads(source.removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))


def candidate(assets, name):
    entry = assets[name]
    path = (REVIEW / unquote(entry["candidate"])).resolve()
    with Image.open(path) as opened:
        image = opened.convert("RGBA")
    expected = tuple(dimension * 2 for dimension in entry["size"])
    if image.size != expected:
        raise ValueError(f"{name} candidate has {image.size}, expected {expected}")
    return image, path


def main():
    data = load_catalog()
    character = data["characters"][0]
    doll_type = data["types"][str(character["type"])]
    assets = data["assets"]
    parts = {}
    sources = {}
    for name in (character["body"], character["rightOpen"], TARGET):
        parts[name], sources[name] = candidate(assets, name)
    stage = Image.new("RGBA", (350, 756))
    stage.alpha_composite(parts[character["body"]], (character["bodyX"] * 2, character["bodyY"] * 2))
    stage.alpha_composite(parts[character["rightOpen"]],
                          (doll_type["rightOpenX"] * 2, doll_type["rightOpenY"] * 2))
    target_x, target_y = doll_type["leftFingersX"] * 2, doll_type["leftFingersY"] * 2
    stage.alpha_composite(parts[TARGET], (target_x, target_y))

    allowed = Image.new("L", stage.size)
    allowed.paste(parts[TARGET].getchannel("A"), (target_x, target_y))
    allowed = allowed.filter(ImageFilter.MaxFilter(9))
    crop = stage.crop(CROP)
    crop_big = crop.resize((crop.width * UPSCALE, crop.height * UPSCALE), Image.Resampling.NEAREST)
    mask = allowed.crop(CROP)
    mask_big = mask.resize(crop_big.size, Image.Resampling.NEAREST)
    mask_rgb = Image.merge("RGB", (mask_big, mask_big, mask_big))
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "full_candidate_pose": OUT / "full_candidate_pose_x2.png",
        "context_crop": OUT / "context_crop_x8.png",
        "edit_mask": OUT / "edit_mask_x8.png",
        "arm_only_context": OUT / "arm_only_context_x8.png",
        "arm_only_mask": OUT / "arm_only_mask_x8.png",
        "arm_only_original_limb": OUT / "arm_only_original_limb_x8.png",
        "arm_native_context": OUT / "arm_native_context_x8.png",
        "arm_native_mask": OUT / "arm_native_mask_x8.png",
    }
    stage.save(files["full_candidate_pose"], optimize=True)
    crop_big.save(files["context_crop"], optimize=True)
    mask_rgb.save(files["edit_mask"], optimize=True)
    arm_pixels = stage.crop(ARM_CROP).resize(((ARM_CROP[2] - ARM_CROP[0]) * UPSCALE,
                                             (ARM_CROP[3] - ARM_CROP[1]) * UPSCALE), Image.Resampling.NEAREST)
    arm_context = Image.new("RGBA", ARM_CANVAS)
    arm_context.alpha_composite(arm_pixels, ARM_POSITION)
    arm_context.save(files["arm_only_context"], optimize=True)
    arm_mask_pixels = allowed.crop(ARM_CROP).resize(arm_pixels.size, Image.Resampling.NEAREST)
    arm_mask = Image.new("L", ARM_CANVAS)
    arm_mask.paste(arm_mask_pixels, ARM_POSITION)
    Image.merge("RGB", (arm_mask, arm_mask, arm_mask)).save(files["arm_only_mask"], optimize=True)
    native_path = (REVIEW / unquote(assets[TARGET]["native"])).resolve()
    with Image.open(native_path) as opened:
        native = opened.convert("RGBA").resize(parts[TARGET].size, Image.Resampling.NEAREST)
    native_stage = Image.new("RGBA", stage.size)
    native_stage.alpha_composite(native, (target_x, target_y))
    native_pixels = native_stage.crop(ARM_CROP).resize(arm_pixels.size, Image.Resampling.NEAREST)
    original_limb = Image.new("RGBA", ARM_CANVAS)
    original_limb.alpha_composite(native_pixels, ARM_POSITION)
    original_limb.save(files["arm_only_original_limb"], optimize=True)
    native_pose = Image.new("RGBA", stage.size)
    native_pose.alpha_composite(parts[character["body"]], (character["bodyX"] * 2, character["bodyY"] * 2))
    native_pose.alpha_composite(parts[character["rightOpen"]],
                                (doll_type["rightOpenX"] * 2, doll_type["rightOpenY"] * 2))
    native_pose.alpha_composite(native, (target_x, target_y))
    native_arm = native_pose.crop(ARM_CROP).resize(arm_pixels.size, Image.Resampling.NEAREST)
    native_context = Image.new("RGBA", ARM_CANVAS)
    native_context.alpha_composite(native_arm, ARM_POSITION)
    native_context.save(files["arm_native_context"], optimize=True)
    native_allowed = Image.new("L", stage.size)
    native_allowed.paste(native.getchannel("A"), (target_x, target_y))
    native_allowed = native_allowed.filter(ImageFilter.MaxFilter(9))
    native_mask_pixels = native_allowed.crop(ARM_CROP).resize(arm_pixels.size, Image.Resampling.NEAREST)
    native_mask = Image.new("L", ARM_CANVAS)
    native_mask.paste(native_mask_pixels, ARM_POSITION)
    Image.merge("RGB", (native_mask, native_mask, native_mask)).save(files["arm_native_mask"], optimize=True)
    manifest = {
        "schema": "openyamm-paperdoll-in-situ-limb-pilot-v1",
        "doll": character["id"], "target": TARGET,
        "stage_size_x2": list(stage.size), "crop_x2": list(CROP), "input_upscale": UPSCALE,
        "arm_crop_x2": list(ARM_CROP), "arm_canvas": list(ARM_CANVAS), "arm_position": list(ARM_POSITION),
        "target_placement_x2": [target_x, target_y], "target_size_x2": list(parts[TARGET].size),
        "candidate_sources": {name: {"path": str(path), "sha256": digest(path)} for name, path in sources.items()},
        "files": {name: {"path": str(path.resolve()), "sha256": digest(path)} for name, path in files.items()},
        "status": "references_only",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"crop_x2": list(CROP), "crop_input": list(crop_big.size),
                      "target_placement_x2": [target_x, target_y]}, indent=2))


if __name__ == "__main__":
    main()
