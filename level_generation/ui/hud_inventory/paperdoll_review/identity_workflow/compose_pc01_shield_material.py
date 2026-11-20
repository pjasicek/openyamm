"""Transfer the registered PC01 open-arm bracer to its aligned shield-hand state."""

import hashlib
import json
import math
import sys
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
OUT = HERE / "prepared/doll_01/red_bracer_shield"
OPEN = HERE / "prepared/doll_01/red_bracer_open/pc01lhu_red_bracer_trial_v3.png"
SHIELD = HERE / "prepared/doll_01/shared_bracer_shield/pc01lho_shared_bracer_v1.png"
INVENTORY = HERE.parent.parent
sys.path.insert(0, str(INVENTORY))
import queue as queue_module  # noqa: E402
import registration  # noqa: E402

PROTECTED_END = 60
BLEND_END = 72


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loaded(path):
    with Image.open(path) as opened:
        return opened.convert("RGBA")


def sample(pixels, x, y, dx):
    center = x - dx
    if 0 <= center < pixels.shape[1] and pixels[y, center, 3] >= 128:
        return pixels[y, center, :3], True
    for radius in range(1, 5):
        for delta_y in range(-radius, radius + 1):
            yy = y + delta_y
            if not 0 <= yy < BLEND_END:
                continue
            for delta_x in range(-radius, radius + 1):
                xx = center + delta_x
                if 0 <= xx < pixels.shape[1] and pixels[yy, xx, 3] >= 128:
                    return pixels[yy, xx, :3], False
    return None, False


def stage(body, arm, x, y):
    output = Image.new("RGBA", (350, 756), "#253137")
    output.alpha_composite(body, (60, 66))
    output.alpha_composite(arm, (x, y))
    return output


def round_away(value):
    return math.floor(value + 0.5) if value >= 0 else math.ceil(value - 0.5)


def art(data, name):
    asset = data["assets"][name]
    return loaded(REVIEW / unquote(asset["candidate"] or asset["native"]))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads((REVIEW / "catalog.js").read_text()
                      .removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))
    row = data["characters"][0]
    doll_type = data["types"][str(row["type"])]
    open_x, open_y = doll_type["leftFingersX"] * 2, doll_type["leftFingersY"] * 2
    shield_x, shield_y = doll_type["leftClosedX"] * 2, doll_type["leftClosedY"] * 2
    if open_y != shield_y:
        raise ValueError("The PC01 open and shield arms do not share a vertical offset")
    dx = open_x - shield_x
    canonical = np.asarray(loaded(OPEN))
    original = np.asarray(loaded(SHIELD))
    output = original.copy()
    exact = inferred = missed = 0
    for y in range(BLEND_END):
        contribution = 1.0 if y < PROTECTED_END else (BLEND_END - y) / (BLEND_END - PROTECTED_END)
        for x in range(output.shape[1]):
            if output[y, x, 3] == 0:
                continue
            color, direct = sample(canonical, x, y, dx)
            if color is None:
                missed += 1
                continue
            if direct:
                exact += 1
            else:
                inferred += 1
            output[y, x, :3] = np.rint(color * contribution + original[y, x, :3] *
                                       (1.0 - contribution)).astype(np.uint8)
    if missed or not np.array_equal(output[:, :, 3], original[:, :, 3]):
        raise ValueError(f"Bracer transfer misses {missed} pixels or changed shield alpha")
    if not np.array_equal(output[BLEND_END:], original[BLEND_END:]):
        raise AssertionError("Shield hand pixels changed beyond the proximal blending zone")
    candidate_path = OUT / "pc01lho_red_bracer_trial.png"
    Image.fromarray(output, "RGBA").save(candidate_path, optimize=True)

    queue = queue_module.Queue()
    identifier = "engine--icons--pc01lho.bmp"
    member = queue.members[identifier][1]
    target = queue.targets[member["target"]]
    measured = registration.measurements(member, target, candidate_path)
    flags = {name: profile["failures"] for name, profile in measured["profiles"].items()
             if profile["failures"]}
    body_path = REVIEW / unquote(data["assets"][row["body"]]["candidate"])
    body = loaded(body_path)
    comparison = Image.new("RGBA", (3 * 350 + 2 * 12, 756), "#253137")
    for index, arm in enumerate((loaded(OPEN), loaded(SHIELD), loaded(candidate_path))):
        position = (open_x, open_y) if index == 0 else (shield_x, shield_y)
        comparison.alpha_composite(stage(body, arm, *position), (index * 362, 0))
    comparison_path = OUT / "red_open_brown_shield_red_shield.png"
    comparison.save(comparison_path, optimize=True)
    main_item = next(item for item in data["items"] if item["id"] == 1)
    shield_item = next(item for item in data["items"] if item["id"] == 99)
    right_hold = art(data, row["rightHold"])
    fingers = art(data, row["rightFingers"])
    sword = art(data, main_item["icon"])
    shield_item_art = art(data, shield_item["icon"])
    grip_x = doll_type["rightFingersX"] + round_away(data["assets"][row["rightFingers"]]["size"][0] * 0.5)
    sword_position = ((grip_x - main_item["equipX"]) * 2,
                      (doll_type["rightClosedY"] + doll_type["mainHandOffsetY"] - main_item["equipY"]) * 2)
    shield_position = ((doll_type["leftClosedX"] + doll_type["shieldX"] - shield_item["equipX"]) * 2,
                       (doll_type["leftClosedY"] + doll_type["shieldY"] - shield_item["equipY"]) * 2)
    equipped = Image.new("RGBA", (2 * 350 + 12, 756), "#253137")
    for index, arm in enumerate((loaded(SHIELD), loaded(candidate_path))):
        pose = Image.new("RGBA", (350, 756), "#253137")
        pose.alpha_composite(body, (60, 66))
        pose.alpha_composite(right_hold, (doll_type["rightClosedX"] * 2, doll_type["rightClosedY"] * 2))
        pose.alpha_composite(arm, (shield_x, shield_y))
        pose.alpha_composite(sword, sword_position)
        pose.alpha_composite(shield_item_art, shield_position)
        pose.alpha_composite(fingers, (doll_type["rightFingersX"] * 2, doll_type["rightFingersY"] * 2))
        equipped.alpha_composite(pose, (index * 362, 0))
    equipped_path = OUT / "brown_vs_red_with_sword_and_shield.png"
    equipped.save(equipped_path, optimize=True)
    report = {
        "schema": "openyamm-pc01-red-bracer-shield-trial-v1",
        "status": "unapproved_visual_trial",
        "target": identifier,
        "open_source": str(OPEN.relative_to(HERE)), "open_sha256": digest(OPEN),
        "shield_source": str(SHIELD.relative_to(HERE)), "shield_sha256": digest(SHIELD),
        "table_offsets_x2": {"open": [open_x, open_y], "shield": [shield_x, shield_y]},
        "shared_proximal_rows_x2": PROTECTED_END,
        "skin_blend_end_row_x2": BLEND_END,
        "copied_corresponding_pixels": exact,
        "nearby_color_samples": inferred,
        "missing_color_samples": missed,
        "alpha_identical_to_registered_shield_source": True,
        "distal_hand_identical_from_row_x2": BLEND_END,
        "candidate": str(candidate_path.relative_to(HERE)), "candidate_sha256": digest(candidate_path),
        "comparison": str(comparison_path.relative_to(HERE)), "comparison_sha256": digest(comparison_path),
        "equipped_comparison": str(equipped_path.relative_to(HERE)),
        "equipped_comparison_sha256": digest(equipped_path),
        "equipment_context": {"main_item_id": 1, "shield_item_id": 99,
                              "sword_offset_x2": sword_position, "shield_offset_x2": shield_position},
        "registration_flags": flags, "registration_profiles": measured["profiles"],
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"registration_flags": flags, "direct": exact, "nearby": inferred,
                      "missing": missed}, indent=2))


if __name__ == "__main__":
    main()
