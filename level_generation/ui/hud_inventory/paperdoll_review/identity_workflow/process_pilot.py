"""Split a portrait-conditioned pilot return and measure each sprite before visual review."""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
INVENTORY = REVIEW.parent
sys.path.insert(0, str(REVIEW))
from prepare_raw_candidates import decontaminate_translucent_edges, digest, image_to_x2  # noqa: E402

sys.path.insert(0, str(INVENTORY))
import queue as queue_module  # noqa: E402
import registration  # noqa: E402


def main():
    folder = HERE / "prepared/doll_01"
    reference = json.loads((folder / "manifest.json").read_text())
    raw_path = folder / "raw_pilot_v1.png"
    with Image.open(raw_path) as opened:
        raw = opened.convert("RGBA")
    if raw.getchannel("A").getextrema() != (0, 255):
        raise ValueError("Imagegen return lacks real alpha")
    ref_width, ref_height = reference["sheet_size"]
    scale_x, scale_y = raw.width / ref_width, raw.height / ref_height
    if abs(scale_x / scale_y - 1) > .03:
        raise ValueError("Return changed sheet aspect by more than 3%")
    output = folder / "pilot_v1"
    output.mkdir(exist_ok=True)
    queue = queue_module.Queue()
    records = {}
    for name, cell in reference["cells"].items():
        target_id = "engine--icons--" + name + ".bmp"
        member = queue.members[target_id][1]
        target = queue.targets[member["target"]]
        x, y, width, height = cell["rect"]
        bounds = [round(x * scale_x), round(y * scale_y),
                  round((x + width) * scale_x), round((y + height) * scale_y)]
        crop = raw.crop(tuple(bounds))
        cleaned, fringe_replaced = decontaminate_translucent_edges(crop, crop)
        candidate, operation = image_to_x2(cleaned, tuple(target["x2_size"]), False)
        path = output / (name + ".png")
        candidate.save(path, optimize=True)
        measurements = registration.measurements(member, target, path)
        flags = {profile: report["failures"] for profile, report in measurements["profiles"].items()
                 if report["failures"]}
        alpha = np.asarray(candidate.getchannel("A"))
        records[name] = {"path": str(path.resolve()), "sha256": digest(path),
                         "native_size": cell["native_size"], "x2_size": list(candidate.size),
                         "crop": bounds, "sampling_pixels_per_native": [
                             round(crop.width / cell["native_size"][0], 4),
                             round(crop.height / cell["native_size"][1], 4)],
                         "alpha_extrema": [int(alpha.min()), int(alpha.max())],
                         "fringe_rgb_from_nearest_core": fringe_replaced,
                         "operation": operation, "registration_flags": flags}

    pose_sheet = Image.new("RGBA", (4 * 350 + 3 * 12, 756), "#253137")
    for index, pose in enumerate(reference["pose_layers"]):
        canvas = Image.new("RGBA", (350, 756))
        for name, x, y in pose["layers"]:
            if name not in records:
                continue
            with Image.open(records[name]["path"]) as opened:
                image = opened.convert("RGBA")
            canvas.alpha_composite(image, (x * 2, y * 2))
        pose_sheet.alpha_composite(canvas, (index * 362, 0))
    pose_path = output / "assembled_pilot_v1.png"
    pose_sheet.save(pose_path, optimize=True)
    report = {"schema": "openyamm-paperdoll-identity-pilot-v1", "character_id": 1,
              "raw": str(raw_path.resolve()), "raw_sha256": digest(raw_path), "raw_size": list(raw.size),
              "reference_sheet_sha256": reference["target_sheet_sha256"],
              "portrait_reference_sha256": reference["portrait_original_x4_sha256"],
              "pose_reference_sha256": reference["assembled_poses_sha256"],
              "submitted_prompt": str((folder / "submitted_prompt_v1.txt").resolve()),
              "submitted_prompt_sha256": digest(folder / "submitted_prompt_v1.txt"),
              "tool": "built-in image_gen.imagegen", "cells": records,
              "assembled": str(pose_path.resolve()), "assembled_sha256": digest(pose_path),
              "visual_approval": False,
              "disposition": "rejected_geometry_and_hand_pose",
              "note": "All six parts exceed registration tolerance. The main-hand grip and finger overlay "
                      "changed pose; do not promote or use this sheet as a batch template."}
    (folder / "pilot_v1_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"cells": len(records), "raw_sampling": [round(scale_x * 2, 3), round(scale_y * 2, 3)],
                      "registration_flagged": sum(bool(entry["registration_flags"])
                                                  for entry in records.values())}, indent=2))


if __name__ == "__main__":
    main()
