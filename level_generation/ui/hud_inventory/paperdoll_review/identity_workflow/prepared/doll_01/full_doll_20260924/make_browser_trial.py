"""Prepare a fixed-transform PC01 full-doll trial for the equipment browser."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
SHEET = HERE / "two_pose_v2_five_digit_grip_composite.png"
FIT_REPORT = HERE / "two_pose_v2_report.json"
CELL_SIZE = (350, 756)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with Image.open(SHEET) as opened:
        sheet = opened.convert("RGBA")
    if sheet.size != (1207, 1303):
        raise ValueError("Two-pose sheet changed; inspect the split before exporting")
    report = json.loads(FIT_REPORT.read_text())
    sx, sy = report["shared_fit_transform"]["scale"]
    dx, dy = report["shared_fit_transform"]["translation"]
    even = Image.new("RGBA", (sheet.width + 1, sheet.height))
    even.alpha_composite(sheet)
    half = even.width // 2
    outputs = {}
    for index, (pose, source_name) in enumerate((("empty", "source_two_pose_empty_x2.png"),
                                                  ("held", "source_two_pose_one_hand_x2.png"))):
        cell = even.crop((index * half, 0, (index + 1) * half, sheet.height))
        stage = cell.transform(CELL_SIZE, Image.Transform.AFFINE,
                               (1 / sx, 0, -dx / sx, 0, 1 / sy, -dy / sy), Image.Resampling.BICUBIC)
        path = HERE / f"browser_trial_{pose}_x2.png"
        stage.save(path, optimize=True)
        with Image.open(HERE / source_name) as opened:
            source = opened.convert("RGBA")
        mask = np.asarray(stage.getchannel("A")) >= 128
        source_mask = np.asarray(source.getchannel("A")) >= 128
        iou = np.count_nonzero(mask & source_mask) / np.count_nonzero(mask | source_mask)
        outputs[pose] = {"path": path.name, "sha256": digest(path), "size": list(stage.size),
                         "alpha_128_iou_vs_original": round(float(iou), 4)}

    manifest = {
        "schema": "openyamm-pc01-browser-trial-v1",
        "status": "experimental_preview_only",
        "note": "Both poses use the same nonuniform diagnostic registration, with no per-pose or item x/y adjustment. "
                "The full figure fails the 0.85 silhouette IoU guard and must not be installed as game art.",
        "source_sheet": {"path": SHEET.name, "sha256": digest(SHEET)},
        "transform": report["shared_fit_transform"],
        "poses": outputs,
    }
    (HERE / "browser_trial_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    main()
