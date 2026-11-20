"""Prepare a shield-hand seed by reusing PC01's aligned open-hand bracer pixels."""

import hashlib
import json
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image, ImageFilter


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
OPEN = HERE / "prepared/doll_01/in_situ_left_open"
OUT = HERE / "prepared/doll_01/shared_bracer_shield"
CROP = (260, 260, 344, 430)
FRAME_POSITION = (88, 44)
FRAME_SIZE = (512, 768)
SCALE = 4
BRACER_END = 48  # x2 pixels in the limb canvas; cuff/hand below stays editable.


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame(stage):
    crop = stage.crop(CROP).resize(((CROP[2] - CROP[0]) * SCALE,
                                    (CROP[3] - CROP[1]) * SCALE), Image.Resampling.NEAREST)
    output = Image.new("RGBA", FRAME_SIZE)
    output.alpha_composite(crop, FRAME_POSITION)
    return output


def main():
    data = json.loads((REVIEW / "catalog.js").read_text()
                      .removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))
    assets = data["assets"]
    character = data["characters"][0]
    doll_type = data["types"][str(character["type"])]
    body_path = (REVIEW / unquote(assets[character["body"]]["candidate"])).resolve()
    shield_path = (REVIEW / unquote(assets[character["leftClosed"]]["native"])).resolve()
    open_path = OPEN / "pc01lhu_in_situ_v2.png"
    with Image.open(body_path) as opened:
        body = opened.convert("RGBA")
    with Image.open(shield_path) as opened:
        shield = opened.convert("RGBA")
    shield = shield.resize((shield.width * 2, shield.height * 2), Image.Resampling.NEAREST)
    with Image.open(open_path) as opened:
        canonical = opened.convert("RGBA")
    closed_x, closed_y = doll_type["leftClosedX"] * 2, doll_type["leftClosedY"] * 2
    open_x, open_y = doll_type["leftFingersX"] * 2, doll_type["leftFingersY"] * 2
    if open_y != closed_y:
        raise ValueError("The two bracers do not share a vertical offset")
    dx = open_x - closed_x
    source = np.asarray(shield).copy()
    open_pixels = np.asarray(canonical)
    copied = 0
    inferred = 0
    for y in range(BRACER_END):
        for x in range(shield.width):
            if source[y, x, 3] < 128:
                continue
            canonical_x = x - dx
            if 0 <= canonical_x < canonical.width and open_pixels[y, canonical_x, 3] >= 128:
                source[y, x, :3] = open_pixels[y, canonical_x, :3]
                copied += 1
                continue
            closest = None
            for radius in range(1, 5):
                for offset_y in range(-radius, radius + 1):
                    for offset_x in range(-radius, radius + 1):
                        sample_x, sample_y = canonical_x + offset_x, y + offset_y
                        if (0 <= sample_x < canonical.width and 0 <= sample_y < BRACER_END
                                and open_pixels[sample_y, sample_x, 3] >= 128):
                            closest = open_pixels[sample_y, sample_x, :3]
                            break
                    if closest is not None:
                        break
                if closest is not None:
                    break
            if closest is not None:
                source[y, x, :3] = closest
                inferred += 1
    seed = Image.fromarray(source, "RGBA")
    stage = Image.new("RGBA", (350, 756))
    stage.alpha_composite(body, (character["bodyX"] * 2, character["bodyY"] * 2))
    stage.alpha_composite(seed, (closed_x, closed_y))
    allowed = Image.new("L", seed.size)
    alpha = seed.getchannel("A")
    editable = Image.new("L", seed.size)
    editable.paste(alpha.crop((0, BRACER_END - 4, seed.width, seed.height)),
                   (0, BRACER_END - 4))
    editable = editable.filter(ImageFilter.MaxFilter(7))
    allowed.paste(editable, (0, 0))
    mask_stage = Image.new("L", stage.size)
    mask_stage.paste(allowed, (closed_x, closed_y))
    mask_crop = mask_stage.crop(CROP).resize(((CROP[2] - CROP[0]) * SCALE,
                                              (CROP[3] - CROP[1]) * SCALE), Image.Resampling.NEAREST)
    mask_frame = Image.new("L", FRAME_SIZE)
    mask_frame.paste(mask_crop, FRAME_POSITION)
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "seed_sprite": OUT / "pc01lho_shared_bracer_seed.png",
        "seed_context": OUT / "shield_shared_bracer_context_x8.png",
        "hand_edit_mask": OUT / "shield_hand_edit_mask_x8.png",
        "canonical_context": OUT / "canonical_open_arm_x8.png",
    }
    seed.save(files["seed_sprite"], optimize=True)
    frame(stage).save(files["seed_context"], optimize=True)
    Image.merge("RGB", (mask_frame, mask_frame, mask_frame)).save(files["hand_edit_mask"], optimize=True)
    canonical_stage = Image.new("RGBA", stage.size)
    canonical_stage.alpha_composite(body, (character["bodyX"] * 2, character["bodyY"] * 2))
    canonical_stage.alpha_composite(canonical, (open_x, open_y))
    frame(canonical_stage).save(files["canonical_context"], optimize=True)
    record = {
        "schema": "openyamm-pc01-shared-bracer-shield-seed-v1", "target": "pc01lho",
        "target_position_x2": [closed_x, closed_y], "target_size_x2": list(seed.size),
        "crop_x2": list(CROP), "frame_position": list(FRAME_POSITION), "frame_size": list(FRAME_SIZE),
        "scale": SCALE, "bracer_end_x2": BRACER_END, "direct_copy_pixels": copied,
        "neighbor_filled_pixels": inferred, "body_source_sha256": digest(body_path),
        "shield_original_sha256": digest(shield_path), "canonical_open_sha256": digest(open_path),
        "files": {name: {"path": str(path.resolve()), "sha256": digest(path)} for name, path in files.items()},
        "status": "seed_only_unapproved",
    }
    (OUT / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"direct_copy_pixels": copied, "neighbor_filled_pixels": inferred,
                      "bracer_end_x2": BRACER_END}, indent=2))


if __name__ == "__main__":
    main()
