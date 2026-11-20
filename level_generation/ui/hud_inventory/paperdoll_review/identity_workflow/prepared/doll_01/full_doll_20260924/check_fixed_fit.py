"""Review generated PC01 poses against unchanged game-table equipment offsets.

This deliberately uses one transform, derived from the v5 empty-pose silhouette,
for every generated pose. It is a diagnostic fit, not an approved sprite export.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[3]
STAGE_SIZE = (350, 756)
POSES = {
    "empty": ("raw_detail_repaint_v5.png", "original_assembled_empty_x2.png", []),
    "one_hand": ("raw_one_hand_open_v2.png", "original_assembled_one_hand_x2.png", [(1, "main")]),
    "two_hand": ("raw_one_hand_open_v2.png", "original_assembled_two_hand_x2.png", [(1, "main")]),
    "shield": ("raw_shield_v1.png", "original_assembled_shield_x2.png",
               [(1, "main"), (99, "shield")]),
}
REGIONS = {
    "whole": (0, 0, 350, 756),
    "right_open": (48, 212, 153, 405),
    "right_grip": (40, 218, 155, 301),
    "left_open": (260, 286, 340, 424),
    "left_shield": (252, 286, 342, 439),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric(reference: np.ndarray, candidate: np.ndarray, region: tuple[int, int, int, int]) -> dict:
    x0, y0, x1, y1 = region
    source = reference[y0:y1, x0:x1]
    result = candidate[y0:y1, x0:x1]
    intersection = int(np.count_nonzero(source & result))
    union = int(np.count_nonzero(source | result))
    source_area = int(np.count_nonzero(source))
    result_area = int(np.count_nonzero(result))

    def centroid(mask: np.ndarray) -> list[float] | None:
        ys, xs = np.nonzero(mask)
        return [round(float(xs.mean() + x0), 2), round(float(ys.mean() + y0), 2)] if len(xs) else None

    source_center = centroid(source)
    result_center = centroid(result)
    return {
        "source_area": source_area,
        "candidate_area": result_area,
        "area_ratio": round(result_area / source_area, 4) if source_area else None,
        "intersection": intersection,
        "union": union,
        "iou": round(intersection / union, 4) if union else None,
        "source_centroid": source_center,
        "candidate_centroid": result_center,
        "centroid_delta": [round(b - a, 2) for a, b in zip(source_center, result_center)]
        if source_center and result_center else None,
    }


def main() -> None:
    with Image.open(HERE / "raw_detail_repaint_v5.png") as opened:
        source_bbox = opened.getchannel("A").getbbox()
    with Image.open(HERE / "original_assembled_empty_x2.png") as opened:
        target_bbox = opened.getchannel("A").getbbox()
    assert source_bbox and target_bbox
    sx = (target_bbox[2] - target_bbox[0]) / (source_bbox[2] - source_bbox[0])
    sy = (target_bbox[3] - target_bbox[1]) / (source_bbox[3] - source_bbox[1])
    dx = target_bbox[0] - sx * source_bbox[0]
    dy = target_bbox[1] - sy * source_bbox[1]

    source = (REVIEW / "catalog.js").read_text()
    catalog = json.loads(source.removeprefix("window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))
    character = next(entry for entry in catalog["characters"] if entry["id"] == 1)
    doll_type = catalog["types"][str(character["type"])]
    items = {entry["id"]: entry for entry in catalog["items"]}

    def equipment_position(item_id: int, slot: str) -> tuple[int, int]:
        item = items[item_id]
        if slot == "main":
            finger_width = catalog["assets"][character["rightFingers"]]["size"][0]
            grip_x = doll_type["rightFingersX"] + (finger_width + 1) // 2
            x = grip_x - item["equipX"]
            y = doll_type["rightClosedY"] + doll_type["mainHandOffsetY"] - item["equipY"]
        else:
            x = doll_type["leftClosedX"] + doll_type["shieldX"] - item["equipX"]
            y = doll_type["leftClosedY"] + doll_type["shieldY"] - item["equipY"]
        return (x * 2, y * 2)

    records = {}
    for pose_name, (raw_name, original_name, equipment) in POSES.items():
        with Image.open(HERE / raw_name) as opened:
            raw = opened.convert("RGBA")
        with Image.open(HERE / original_name) as opened:
            original = opened.convert("RGBA")
        aligned = raw.transform(
            STAGE_SIZE, Image.Transform.AFFINE,
            (1 / sx, 0, -dx / sx, 0, 1 / sy, -dy / sy),
            Image.Resampling.BICUBIC,
        )
        aligned_path = HERE / f"fixed_{pose_name}_x2.png"
        aligned.save(aligned_path, optimize=True)

        metrics = {}
        for threshold in (16, 128):
            reference_mask = np.asarray(original.getchannel("A")) >= threshold
            candidate_mask = np.asarray(aligned.getchannel("A")) >= threshold
            regions = ["whole", "right_open", "left_open"] if pose_name == "empty" else [
                "whole", "right_grip", "left_shield" if pose_name == "shield" else "left_open"]
            metrics[str(threshold)] = {
                region: metric(reference_mask, candidate_mask, REGIONS[region]) for region in regions
            }
            if threshold == 128:
                comparison = np.zeros((STAGE_SIZE[1], STAGE_SIZE[0], 4), dtype=np.uint8)
                comparison[reference_mask & candidate_mask] = (95, 205, 140, 255)
                comparison[reference_mask & ~candidate_mask] = (250, 80, 80, 255)
                comparison[~reference_mask & candidate_mask] = (85, 160, 255, 255)
                Image.fromarray(comparison, "RGBA").save(HERE / f"mask_{pose_name}_x2.png", optimize=True)

        equipped = aligned.copy()
        placed = []
        for item_id, slot in equipment:
            icon = items[item_id]["icon"]
            asset = catalog["assets"][icon]
            with Image.open(REVIEW / asset["native"]) as opened:
                item_image = opened.convert("RGBA")
            item_image = item_image.resize((item_image.width * 2, item_image.height * 2), Image.Resampling.NEAREST)
            xy = equipment_position(item_id, slot)
            equipped.alpha_composite(item_image, xy)
            placed.append({"item_id": item_id, "icon": icon, "position_x2": list(xy)})
        equipped_path = HERE / f"fixed_{pose_name}_equipped_x2.png"
        equipped.save(equipped_path, optimize=True)
        records[pose_name] = {
            "raw": {"path": raw_name, "sha256": sha256(HERE / raw_name)},
            "original": {"path": original_name, "sha256": sha256(HERE / original_name)},
            "aligned": {"path": aligned_path.name, "sha256": sha256(aligned_path)},
            "equipped": {"path": equipped_path.name, "sha256": sha256(equipped_path)},
            "items": placed,
            "metrics": metrics,
        }

    report = {
        "schema": "openyamm-pc01-fixed-fit-diagnostic-v1",
        "note": "No generated variant has an individual transform or changed item x/y. Full-doll alignment is "
                "diagnostic only, nonuniform, and not a reviewed per-sprite export. The original finger overlay "
                "is intentionally omitted from generated equipment previews.",
        "stage_x2": list(STAGE_SIZE),
        "transform": {"source_bbox": list(source_bbox), "target_bbox": list(target_bbox),
                      "scale": [sx, sy], "translation": [dx, dy]},
        "mask_colors": {"overlap": "green", "source_only": "red", "candidate_only": "blue"},
        "regions": REGIONS,
        "poses": records,
    }
    (HERE / "fixed_fit_report.json").write_text(json.dumps(report, indent=2) + "\n")
    for name, record in records.items():
        print(name, {threshold: {region: values["iou"] for region, values in region_metrics.items()}
                     for threshold, region_metrics in record["metrics"].items()})


if __name__ == "__main__":
    main()
