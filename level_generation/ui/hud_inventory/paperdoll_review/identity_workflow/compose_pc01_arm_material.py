"""Try the red-bracer paint on PC01's previously registered open-arm geometry."""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "prepared/doll_01/in_situ_left_open"
OUT = HERE / "prepared/doll_01/red_bracer_open"
INVENTORY = HERE.parent.parent
sys.path.insert(0, str(INVENTORY))
import queue as queue_module  # noqa: E402
import registration  # noqa: E402

BLEND_START = 65
BLEND_END = 72
REQUIRED_PAINT_END = 52


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loaded(path):
    with Image.open(path) as opened:
        return opened.convert("RGBA")


def assemble(body, right, left, position):
    stage = Image.new("RGBA", (350, 756), "#253137")
    stage.alpha_composite(body, (60, 66))
    stage.alpha_composite(right, (58, 220))
    stage.alpha_composite(left, position)
    return stage


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    old_path = Path(manifest["candidate_sources"]["pc01lhu"]["path"])
    body_path = Path(manifest["candidate_sources"]["pc01bod"]["path"])
    right_path = Path(manifest["candidate_sources"]["pc01rhd"]["path"])
    geometry_path = SOURCE / "pc01lhu_in_situ_v2.png"
    paint_path = SOURCE / "pc01lhu_in_situ_v3.png"
    geometry = np.asarray(loaded(geometry_path)).copy()
    paint = np.asarray(loaded(paint_path))
    if geometry.shape != paint.shape or geometry.shape[0] <= BLEND_END:
        raise ValueError("PC01 arm sources do not share the original 2x canvas")
    core = geometry[:REQUIRED_PAINT_END, :, 3] >= 128
    if np.any(core & (paint[:REQUIRED_PAINT_END, :, 3] < 128)):
        raise ValueError("The generated red bracer does not cover the registered arm's solid bracer")
    output = geometry.copy()
    for y in range(BLEND_END):
        contribution = 1.0 if y < BLEND_START else (BLEND_END - y) / (BLEND_END - BLEND_START)
        valid = (geometry[y, :, 3] > 0) & (paint[y, :, 3] >= 128)
        combined = (paint[y, :, :3].astype(np.float32) * contribution +
                    geometry[y, :, :3].astype(np.float32) * (1.0 - contribution))
        output[y, valid, :3] = np.rint(combined[valid]).astype(np.uint8)
    if not np.array_equal(output[:, :, 3], geometry[:, :, 3]):
        raise AssertionError("Arm alpha changed during material transfer")
    if not np.array_equal(output[BLEND_END:], geometry[BLEND_END:]):
        raise AssertionError("Hand pixels changed during material transfer")
    candidate_path = OUT / "pc01lhu_red_bracer_trial_v3.png"
    Image.fromarray(output, "RGBA").save(candidate_path, optimize=True)

    queue = queue_module.Queue()
    identifier = "engine--icons--pc01lhu.bmp"
    member = queue.members[identifier][1]
    target = queue.targets[member["target"]]
    measured = registration.measurements(member, target, candidate_path)
    flags = {name: profile["failures"] for name, profile in measured["profiles"].items()
             if profile["failures"]}
    body = loaded(body_path)
    right = loaded(right_path)
    position = tuple(manifest["target_placement_x2"])
    variants = [loaded(old_path), loaded(geometry_path), loaded(paint_path), loaded(candidate_path)]
    sheet = Image.new("RGBA", (4 * 350 + 3 * 12, 756), "#253137")
    for index, arm in enumerate(variants):
        sheet.alpha_composite(assemble(body, right, arm, position), (index * 362, 0))
    sheet_path = OUT / "old_registered_red_and_combined_v3.png"
    sheet.save(sheet_path, optimize=True)
    report = {
        "schema": "openyamm-pc01-red-bracer-material-trial-v1",
        "status": "unapproved_visual_trial",
        "target": identifier,
        "geometry_source": str(geometry_path.relative_to(HERE)),
        "geometry_sha256": digest(geometry_path),
        "paint_source": str(paint_path.relative_to(HERE)),
        "paint_sha256": digest(paint_path),
        "blend_rows_x2": [BLEND_START, BLEND_END],
        "solid_bracer_coverage": "all registered solid bracer pixels covered by generated paint",
        "alpha_identical_to_registered_source": True,
        "hand_pixels_identical_from_row_x2": BLEND_END,
        "candidate": str(candidate_path.relative_to(HERE)),
        "candidate_sha256": digest(candidate_path),
        "comparison": str(sheet_path.relative_to(HERE)),
        "comparison_sha256": digest(sheet_path),
        "registration_flags": flags,
        "registration_profiles": measured["profiles"],
    }
    (OUT / "report_v3.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"registration_flags": flags, "candidate": str(candidate_path)}, indent=2))


if __name__ == "__main__":
    main()
