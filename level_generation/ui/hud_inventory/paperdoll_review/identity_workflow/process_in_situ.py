"""Measure a PC01 in-place arm return without altering the accepted art or review catalog."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
OUT = HERE / "prepared/doll_01/in_situ_left_open"
INVENTORY = HERE.parent.parent
sys.path.insert(0, str(INVENTORY))
import queue as queue_module  # noqa: E402
import registration  # noqa: E402


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def premultiplied_resize(image, size):
    return image.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", type=int, choices=(1, 2, 3), default=1)
    arguments = parser.parse_args()
    version = arguments.version
    source = json.loads((OUT / "manifest.json").read_text())
    raw_path = OUT / f"raw_arm_only_v{version}.png"
    with Image.open(raw_path) as opened:
        raw = opened.convert("RGBA")
    input_width, input_height = source["arm_canvas"]
    scale_x, scale_y = raw.width / input_width, raw.height / input_height
    if abs(scale_x - scale_y) > 0.02:
        raise ValueError("Imagegen changed the arm canvas aspect")
    flat = premultiplied_resize(raw, (input_width, input_height))
    flat_path = OUT / f"returned_arm_canvas_v{version}_at_input_size.png"
    flat.save(flat_path, optimize=True)
    crop_x, crop_y = source["arm_position"]
    left, top, right, bottom = source["arm_crop_x2"]
    width, height = (right - left) * source["input_upscale"], (bottom - top) * source["input_upscale"]
    region = flat.crop((crop_x, crop_y, crop_x + width, crop_y + height))
    stage_region = premultiplied_resize(region, (right - left, bottom - top))
    target_x, target_y = source["target_placement_x2"]
    target_width, target_height = source["target_size_x2"]
    x0, y0 = target_x - left, target_y - top
    sprite = stage_region.crop((x0, y0, x0 + target_width, y0 + target_height))
    sprite_path = OUT / f"pc01lhu_in_situ_v{version}.png"
    sprite.save(sprite_path, optimize=True)

    queue = queue_module.Queue()
    identifier = "engine--icons--pc01lhu.bmp"
    member = queue.members[identifier][1]
    target = queue.targets[member["target"]]
    measured = registration.measurements(member, target, sprite_path)
    flags = {profile: result["failures"] for profile, result in measured["profiles"].items()
             if result["failures"]}
    with Image.open(source["candidate_sources"]["pc01bod"]["path"]) as opened:
        body = opened.convert("RGBA")
    with Image.open(source["candidate_sources"]["pc01rhd"]["path"]) as opened:
        right_arm = opened.convert("RGBA")
    with Image.open(source["candidate_sources"]["pc01lhu"]["path"]) as opened:
        old_arm = opened.convert("RGBA")
    stages = []
    for arm in (old_arm, sprite):
        stage = Image.new("RGBA", (350, 756), "#253137")
        stage.alpha_composite(body, (60, 66))
        stage.alpha_composite(right_arm, (58, 220))
        stage.alpha_composite(arm, (target_x, target_y))
        stages.append(stage)
    pair = Image.new("RGBA", (712, 756), "#253137")
    pair.alpha_composite(stages[0], (0, 0))
    pair.alpha_composite(stages[1], (362, 0))
    pair_path = OUT / f"old_vs_in_situ_v{version}.png"
    pair.save(pair_path, optimize=True)
    alpha = np.asarray(sprite.getchannel("A"))
    report = {
        "schema": "openyamm-paperdoll-in-situ-limb-return-v1", "target": identifier,
        "version": version, "input_art": "original_limb" if version == 2 else "existing_candidate_limb",
        "raw": str(raw_path.resolve()), "raw_sha256": digest(raw_path), "raw_size": list(raw.size),
        "source_manifest_sha256": digest(OUT / "manifest.json"),
        "submitted_prompt_sha256": digest(OUT / f"submitted_prompt_arm_only_v{version}.txt"),
        "sampling_per_x2_pixel": [round(scale_x * source["input_upscale"], 3),
                                  round(scale_y * source["input_upscale"], 3)],
        "sprite": str(sprite_path.resolve()), "sprite_sha256": digest(sprite_path),
        "sprite_size": list(sprite.size), "alpha_extrema": [int(alpha.min()), int(alpha.max())],
        "registration_flags": flags, "registration_profiles": measured["profiles"],
        "assembly_pair": str(pair_path.resolve()), "assembly_pair_sha256": digest(pair_path),
        "visual_approval": False,
        "note": "Diagnostic in-place arm edit. The original body candidate and opposite arm are unchanged in the pair; "
                "the new limb has not been approved or installed.",
    }
    (OUT / f"return_report_v{version}.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"raw_size": list(raw.size), "sprite_size": list(sprite.size),
                      "alpha_extrema": report["alpha_extrema"], "registration_flags": flags}, indent=2))


if __name__ == "__main__":
    main()
