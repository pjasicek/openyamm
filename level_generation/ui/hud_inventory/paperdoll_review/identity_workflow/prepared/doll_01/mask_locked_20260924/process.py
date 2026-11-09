"""Extract PC01 RGB restorations using immutable native sprite alpha and placement."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[3]
STAGE = (350, 756)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    catalog = json.loads((REVIEW / "catalog.js").read_text().split(" = ", 1)[1].removesuffix(";\n"))
    definition = json.loads((HERE.parent / "manifest.json").read_text())
    raw_path = HERE / "raw_v1.png"
    raw = Image.open(raw_path).convert("RGBA")
    # Map the complete returned canvas; never fit a foreground bounding box.
    sheet = raw.resize((STAGE[0] * 2, STAGE[1]), Image.Resampling.LANCZOS)
    cells = [np.array(sheet.crop((i * STAGE[0], 0, (i + 1) * STAGE[0], STAGE[1]))) for i in range(2)]
    raw_pose_iou = {}
    for i, pose in enumerate(("empty", "one_hand")):
        source = Image.open(HERE.parent / "full_doll_20260924" / f"source_two_pose_{pose}_x2.png")
        native_mask = np.array(source.getchannel("A")) >= 128
        generated_mask = cells[i][:, :, 3] >= 128
        raw_pose_iou[pose] = round(float((native_mask & generated_mask).sum() /
                                       (native_mask | generated_mask).sum()), 6)
    colors = []
    distances = []
    for cell in cells:
        # Extend opaque generated RGB beneath the frozen native edge. This prevents
        # transparent/matte RGB becoming visible when replacing generated alpha.
        support = cell[:, :, 3] >= 250
        distance, indices = distance_transform_edt(~support, return_indices=True)
        colors.append(cell[indices[0], indices[1], :3])
        distances.append(distance)

    placements = {
        "pc01bod": (0, 30, 33), "pc01lhu": (0, 138, 150), "pc01rhd": (0, 29, 110),
        "pc01rhu": (1, 27, 117), "pc01rhb": (1, 27, 118),
    }
    restored = {}
    originals = {}
    records = {}
    for name, (cell_id, x, y) in placements.items():
        asset = catalog["assets"][name]
        native_path = REVIEW / asset["native"]
        native = Image.open(native_path).convert("RGBA")
        size = tuple(2 * v for v in native.size)
        original = native.resize(size, Image.Resampling.NEAREST)
        originals[name] = original
        src = np.array(original)
        alpha = src[:, :, 3]
        box = (x * 2, y * 2, x * 2 + size[0], y * 2 + size[1])
        x0, y0, x1, y1 = box
        rgb = colors[cell_id][y0:y1, x0:x1].copy()
        missing_distance = distances[cell_id][y0:y1, x0:x1]
        # The original body contains blue-black legacy boot backing/shadow pixels.
        # They are retained explicitly, not hallucinated as additional foot anatomy.
        shadow = np.zeros(alpha.shape, dtype=bool)
        if name == "pc01bod":
            rows = np.arange(size[1])[:, None] + y0
            shadow = ((rows >= 560) & (alpha > 0) & (src[:, :, 2] >= src[:, :, 0])
                      & (src[:, :, 1] >= src[:, :, 0]))
            rgb[shadow] = src[:, :, :3][shadow]
        output = np.dstack((rgb, alpha))
        output[alpha == 0] = 0
        image = Image.fromarray(output)
        path = HERE / f"{name}.png"
        image.save(path, optimize=True)
        restored[name] = image
        evaluated = (alpha > 0) & ~shadow
        raw_alpha = cells[cell_id][y0:y1, x0:x1, 3] >= 128
        mask = alpha >= 128
        assert np.array_equal(np.array(image.getchannel("A")), alpha)
        records[name] = {
            "path": path.name, "sha256": digest(path), "source": asset["source"],
            "source_sha256": asset["sourceHash"], "native_preview_sha256": digest(native_path),
            "size": list(size), "xy_x2": [x0, y0], "source_cell": cell_id,
            "alpha_differing_pixels": 0, "alpha_iou": 1.0,
            "raw_coverage_of_native_mask": round(float((raw_alpha & mask).sum() / mask.sum()), 4),
            "retained_legacy_shadow_pixels": int(shadow.sum()),
            "rgb_extended_pixels": int(np.count_nonzero(evaluated & (missing_distance > 0))),
            "rgb_extension_max_distance_x2": round(float(missing_distance[evaluated].max()), 3),
            "rgb_extension_over_4px": int(np.count_nonzero(evaluated & (missing_distance > 4))),
        }

    poses = {}
    for pose in definition["pose_layers"]:
        if pose["pose"] == "shield":
            continue  # Shield hand is a separate un-restored pose.
        original_stage = Image.new("RGBA", STAGE)
        restored_stage = Image.new("RGBA", STAGE)
        for name, x, y in pose["layers"]:
            original_stage.alpha_composite(originals[name], (x * 2, y * 2))
            restored_stage.alpha_composite(restored[name], (x * 2, y * 2))
        assert np.array_equal(np.array(original_stage.getchannel("A")),
                              np.array(restored_stage.getchannel("A")))
        original_stage.save(HERE / f"original_{pose['pose']}.png", optimize=True)
        restored_stage.save(HERE / f"restored_{pose['pose']}.png", optimize=True)
        comparison = Image.new("RGBA", (700, 756))
        comparison.alpha_composite(original_stage)
        comparison.alpha_composite(restored_stage, (350, 0))
        comparison.save(HERE / f"comparison_{pose['pose']}.png", optimize=True)
        mask = np.array(original_stage.getchannel("A"))
        proof = np.zeros((STAGE[1], STAGE[0], 4), dtype=np.uint8)
        proof[mask > 0] = [75, 195, 100, 255]
        Image.fromarray(proof).save(HERE / f"mask_{pose['pose']}.png", optimize=True)
        poses[pose["pose"]] = {"alpha_differing_pixels": 0, "alpha_iou": 1.0,
                               "body": "pc01bod.png", "layers": pose["layers"]}

    manifest = {
        "schema": "openyamm-pc01-native-mask-restoration-v1", "status": "visual_review_pending",
        "raw": {"path": raw_path.name, "sha256": digest(raw_path), "size": list(raw.size)},
        "raw_pose_iou_alpha128": raw_pose_iou,
        "mapping": "Whole 2-cell canvas resized to 700x756. Fixed native alpha; opaque RGB edge extension.",
        "mask_note": "Final alpha equality is enforced, not evidence of generated anatomical registration.",
        "body_count": 1, "parts": records, "poses": poses,
        "limitations": ["Legacy blue-black boot backing retained from the source.",
                        "pc01lho shield hand has not been restored in this pass.",
                        "RGB landmarks, seams and equipment fit require visual review."],
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
