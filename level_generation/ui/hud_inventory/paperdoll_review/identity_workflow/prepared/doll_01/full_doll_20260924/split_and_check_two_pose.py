"""Split the generated two-cell sheet and check its unchanged PC01 coordinates."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[3]
CELL_SIZE = (350, 756)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure(source: Image.Image, result: Image.Image, region: tuple[int, int, int, int]) -> dict:
    x0, y0, x1, y1 = region
    record = {}
    for threshold in (16, 128):
        native = np.asarray(source.getchannel("A"))[y0:y1, x0:x1] >= threshold
        generated = np.asarray(result.getchannel("A"))[y0:y1, x0:x1] >= threshold
        intersection = int(np.count_nonzero(native & generated))
        union = int(np.count_nonzero(native | generated))
        native_area = int(np.count_nonzero(native))
        generated_area = int(np.count_nonzero(generated))

        def centroid(mask: np.ndarray) -> list[float] | None:
            ys, xs = np.nonzero(mask)
            return [round(float(xs.mean() + x0), 2), round(float(ys.mean() + y0), 2)] if len(xs) else None

        a = centroid(native)
        b = centroid(generated)
        record[str(threshold)] = {
            "iou": round(intersection / union, 4) if union else None,
            "area_ratio": round(generated_area / native_area, 4) if native_area else None,
            "source_centroid": a, "result_centroid": b,
            "centroid_delta": [round(y - x, 2) for x, y in zip(a, b)] if a and b else None,
        }
    return record


def mask_overlay(source: Image.Image, result: Image.Image, output: Path) -> None:
    native = np.asarray(source.getchannel("A")) >= 128
    generated = np.asarray(result.getchannel("A")) >= 128
    comparison = np.zeros((CELL_SIZE[1], CELL_SIZE[0], 4), dtype=np.uint8)
    comparison[native & generated] = (95, 205, 140, 255)
    comparison[native & ~generated] = (250, 80, 80, 255)
    comparison[~native & generated] = (85, 160, 255, 255)
    Image.fromarray(comparison, "RGBA").save(output, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", choices=("v1", "v2", "v3"), required=True)
    args = parser.parse_args()
    version = args.version
    raw_path = HERE / f"raw_two_pose_sheet_{version}.png"
    with Image.open(raw_path) as opened:
        raw = opened.convert("RGBA")
    # The generator returned an odd-width sheet. Add one transparent pixel at
    # the far right so the original pixels remain untouched and halves are equal.
    normalized = Image.new("RGBA", (raw.width + raw.width % 2, raw.height))
    normalized.alpha_composite(raw)
    normalized_path = HERE / f"raw_two_pose_sheet_{version}_even.png"
    normalized.save(normalized_path, optimize=True)
    half_width = normalized.width // 2
    raw_cells = {}
    for index, pose in enumerate(("empty", "one_hand")):
        cell = normalized.crop((index * half_width, 0, (index + 1) * half_width, normalized.height))
        path = HERE / f"raw_two_pose_{version}_{pose}.png"
        cell.save(path, optimize=True)
        raw_cells[pose] = cell

    source_cells = {}
    for pose in raw_cells:
        with Image.open(HERE / f"source_two_pose_{pose}_x2.png") as opened:
            source_cells[pose] = opened.convert("RGBA")

    source_bbox = source_cells["empty"].getchannel("A").point(
        lambda alpha: 255 if alpha >= 128 else 0).getbbox()
    result_bbox = raw_cells["empty"].getchannel("A").point(
        lambda alpha: 255 if alpha >= 128 else 0).getbbox()
    assert source_bbox and result_bbox
    sx = (source_bbox[2] - source_bbox[0]) / (result_bbox[2] - result_bbox[0])
    sy = (source_bbox[3] - source_bbox[1]) / (result_bbox[3] - result_bbox[1])
    dx = source_bbox[0] - sx * result_bbox[0]
    dy = source_bbox[1] - sy * result_bbox[1]

    catalog = json.loads((REVIEW / "catalog.js").read_text().removeprefix(
        "window.PAPERDOLL_REVIEW_DATA = ").removesuffix(";\n"))
    character = next(entry for entry in catalog["characters"] if entry["id"] == 1)
    doll_type = catalog["types"][str(character["type"])]
    item = next(entry for entry in catalog["items"] if entry["id"] == 1)
    finger_width = catalog["assets"][character["rightFingers"]]["size"][0]
    grip_x = doll_type["rightFingersX"] + (finger_width + 1) // 2
    sword_position = ((grip_x - item["equipX"]) * 2,
                      (doll_type["rightClosedY"] + doll_type["mainHandOffsetY"] - item["equipY"]) * 2)
    with Image.open(REVIEW / catalog["assets"][item["icon"]]["native"]) as opened:
        sword = opened.convert("RGBA")
    sword = sword.resize((sword.width * 2, sword.height * 2), Image.Resampling.NEAREST)

    records = {}
    for pose, cell in raw_cells.items():
        original = source_cells[pose]
        direct = cell.resize(CELL_SIZE, Image.Resampling.LANCZOS)
        fitted = cell.transform(CELL_SIZE, Image.Transform.AFFINE,
                                (1 / sx, 0, -dx / sx, 0, 1 / sy, -dy / sy), Image.Resampling.BICUBIC)
        direct_path = HERE / f"two_pose_{version}_{pose}_direct_x2.png"
        fitted_path = HERE / f"two_pose_{version}_{pose}_shared_fit_x2.png"
        direct.save(direct_path, optimize=True)
        fitted.save(fitted_path, optimize=True)
        mask_overlay(original, direct, HERE / f"two_pose_{version}_{pose}_direct_mask_x2.png")
        mask_overlay(original, fitted, HERE / f"two_pose_{version}_{pose}_shared_mask_x2.png")
        if pose == "one_hand":
            equipped = fitted.copy()
            equipped.alpha_composite(sword, sword_position)
            equipped.save(HERE / f"two_pose_{version}_one_hand_sword_shared_fit_x2.png", optimize=True)

        region = (40, 210, 157, 409) if pose == "empty" else (40, 218, 157, 305)
        records[pose] = {
            "raw_cell_sha256": sha256(HERE / f"raw_two_pose_{version}_{pose}.png"),
            "raw_bbox_alpha128": cell.getchannel("A").point(lambda alpha: 255 if alpha >= 128 else 0).getbbox(),
            "source_bbox_alpha128": original.getchannel("A").point(
                lambda alpha: 255 if alpha >= 128 else 0).getbbox(),
            "direct": {"whole": measure(original, direct, (0, 0, *CELL_SIZE)),
                       "changed_arm_region": measure(original, direct, region)},
            "shared_fit": {"whole": measure(original, fitted, (0, 0, *CELL_SIZE)),
                           "changed_arm_region": measure(original, fitted, region)},
        }

    common_left = np.asarray(raw_cells["empty"].convert("RGBA"))
    common_right = np.asarray(raw_cells["one_hand"].convert("RGBA"))
    # Screen-left arms occupy the left side of the pose; the body and the
    # opposite arm should be byte-identical in the common right-side region.
    common_region = (slice(None), slice(half_width // 2, None))
    a = common_left[common_region]
    b = common_right[common_region]
    differing = int(np.count_nonzero(np.any(a != b, axis=2)))
    report = {
        "schema": "openyamm-pc01-two-pose-split-check-v1",
        "raw_sheet": {"path": raw_path.name, "sha256": sha256(raw_path), "size": list(raw.size)},
        "even_sheet": {"path": normalized_path.name, "sha256": sha256(normalized_path),
                       "size": list(normalized.size), "transparent_right_pad": raw.width % 2},
        "split_x": half_width,
        "direct_mapping": "Resize each complete half to original 350x756 x2 canvas; no crop or translation.",
        "shared_fit_warning": "A single nonuniform bbox fit derived only from empty pose, applied to both. "
                              "Diagnostic upper bound, not an accepted sprite transform.",
        "shared_fit_transform": {"scale": [sx, sy], "translation": [dx, dy]},
        "same_body_region": {"x_from": half_width // 2, "pixels": a.shape[0] * a.shape[1],
                             "differing_rgba_pixels": differing},
        "unchanged_sword_position_x2": list(sword_position),
        "poses": records,
    }
    (HERE / f"two_pose_{version}_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"size": raw.size, "split_x": half_width,
                      "same_body_differing_pixels": differing,
                      "direct_iou_128": {pose: data["direct"]["whole"]["128"]["iou"]
                                         for pose, data in records.items()},
                      "shared_fit_iou_128": {pose: data["shared_fit"]["whole"]["128"]["iou"]
                                             for pose, data in records.items()}}, indent=2))


if __name__ == "__main__":
    main()
