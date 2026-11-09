"""Prepare a PC01 shield-hand trial conditioned on the successful open-arm style pilot."""

import hashlib
import json
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageFilter


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
OPEN = HERE / "prepared/doll_01/in_situ_left_open"
OUT = HERE / "prepared/doll_01/in_situ_left_closed"
CROP = (260, 260, 344, 430)
POSITION = (88, 44)
CANVAS = (512, 768)
SCALE = 4


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def framed(stage):
    crop = stage.crop(CROP).resize(((CROP[2] - CROP[0]) * SCALE,
                                    (CROP[3] - CROP[1]) * SCALE), Image.Resampling.NEAREST)
    image = Image.new("RGBA", CANVAS)
    image.alpha_composite(crop, POSITION)
    return image


def main():
    data = json.loads((REVIEW / "catalog.js").read_text()
                      .removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))
    assets = data["assets"]
    character = data["characters"][0]
    doll_type = data["types"][str(character["type"])]
    body_path = (REVIEW / unquote(assets[character["body"]]["candidate"])).resolve()
    native_path = (REVIEW / unquote(assets[character["leftClosed"]]["native"])).resolve()
    canonical_path = OPEN / "pc01lhu_in_situ_v2.png"
    with Image.open(body_path) as opened:
        body = opened.convert("RGBA")
    with Image.open(native_path) as opened:
        shield = opened.convert("RGBA")
    shield = shield.resize((shield.width * 2, shield.height * 2), Image.Resampling.NEAREST)
    with Image.open(canonical_path) as opened:
        canonical = opened.convert("RGBA")
    shield_pos = (doll_type["leftClosedX"] * 2, doll_type["leftClosedY"] * 2)
    open_pos = (doll_type["leftFingersX"] * 2, doll_type["leftFingersY"] * 2)
    stage = Image.new("RGBA", (350, 756))
    stage.alpha_composite(body, (character["bodyX"] * 2, character["bodyY"] * 2))
    stage.alpha_composite(shield, shield_pos)
    canonical_stage = Image.new("RGBA", stage.size)
    canonical_stage.alpha_composite(body, (character["bodyX"] * 2, character["bodyY"] * 2))
    canonical_stage.alpha_composite(canonical, open_pos)
    mask = Image.new("L", stage.size)
    mask.paste(shield.getchannel("A"), shield_pos)
    mask = mask.filter(ImageFilter.MaxFilter(9))
    mask_crop = mask.crop(CROP).resize(((CROP[2] - CROP[0]) * SCALE,
                                        (CROP[3] - CROP[1]) * SCALE), Image.Resampling.NEAREST)
    mask_frame = Image.new("L", CANVAS)
    mask_frame.paste(mask_crop, POSITION)
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "shield_pose_input": OUT / "shield_pose_input_x8.png",
        "shield_edit_mask": OUT / "shield_edit_mask_x8.png",
        "canonical_open_arm": OUT / "canonical_open_arm_x8.png",
    }
    framed(stage).save(files["shield_pose_input"], optimize=True)
    Image.merge("RGB", (mask_frame, mask_frame, mask_frame)).save(files["shield_edit_mask"], optimize=True)
    framed(canonical_stage).save(files["canonical_open_arm"], optimize=True)
    record = {
        "schema": "openyamm-pc01-shield-hand-style-transfer-v1", "target": "pc01lho",
        "crop_x2": list(CROP), "frame_position": list(POSITION), "frame_size": list(CANVAS), "scale": SCALE,
        "target_position_x2": list(shield_pos), "target_size_x2": list(shield.size),
        "body_source_sha256": digest(body_path), "original_shield_sha256": digest(native_path),
        "canonical_open_arm_sha256": digest(canonical_path),
        "files": {name: {"path": str(path.resolve()), "sha256": digest(path)} for name, path in files.items()},
        "status": "references_only",
    }
    (OUT / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"target": record["target"], "size": record["target_size_x2"],
                      "placement": record["target_position_x2"]}, indent=2))


if __name__ == "__main__":
    main()
