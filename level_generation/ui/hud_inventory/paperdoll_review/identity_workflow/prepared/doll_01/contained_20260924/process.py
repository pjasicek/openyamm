"""Fit existing PC01 generated detail inside a smooth native silhouette envelope."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[3]
STAGE = (350, 756)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure(original, restored):
    native = np.array(original.getchannel("A"))
    result = np.array(restored.getchannel("A"))
    native_mask = native >= 128
    result_mask = result >= 128
    outside = int(np.count_nonzero((result > 0) & (native == 0)))
    assert outside == 0, f"Restoration protrudes beyond native silhouette: {outside} pixels"
    return {
        "outside_native_pixels": outside,
        "opaque_area_ratio": round(float(result_mask.sum() / native_mask.sum()), 5),
        "antialiased_pixels": int(np.count_nonzero((result > 0) & (result < 255))),
        "removed_native_pixels_alpha128": int(np.count_nonzero(native_mask & ~result_mask)),
    }


def main():
    catalog = json.loads((REVIEW / "catalog.js").read_text().split(" = ", 1)[1].removesuffix(";\n"))
    definition = json.loads((HERE.parent / "manifest.json").read_text())
    raw_path = HERE.parent / "mask_locked_20260924/raw_v1.png"
    raw = Image.open(raw_path).convert("RGBA")
    # Whole-canvas mapping only. Working at 4x is for edge sampling, not a claim
    # of extra generated detail (the retained raw master is approximately 3.45x).
    work_size = (STAGE[0] * 2, STAGE[1] * 2)
    sheet = raw.resize((work_size[0] * 2, work_size[1]), Image.Resampling.LANCZOS)
    cells = []
    for i, pose in enumerate(("empty", "one_hand")):
        box = (i * work_size[0], 0, (i + 1) * work_size[0], work_size[1])
        generated = np.array(sheet.crop(box))
        source = Image.open(HERE.parent / "full_doll_20260924" / f"original_assembled_{pose}_x2.png")
        native_envelope = np.array(source.getchannel("A").resize(work_size, Image.Resampling.NEAREST)) / 255.0
        # Smooth and move the exterior edge inward. Work on the assembled pose
        # so internal body/limb seams are not independently eroded.
        smooth = gaussian_filter(native_envelope, sigma=1.25)
        envelope = np.minimum(native_envelope, np.clip((smooth - 0.5) / 0.35, 0, 1))
        # The generated master has alpha around 253 throughout solid interiors.
        # Normalize those to opaque while retaining the actual edge transition.
        generated_alpha = np.clip((generated[:, :, 3].astype(float) - 8) / 232, 0, 1)
        alpha = np.rint(255 * envelope * generated_alpha).astype(np.uint8)
        # Use opaque generated RGB beneath the antialiased fringe; discard the
        # nearly transparent red RGB present around the raw master, not skin hue.
        _, indices = distance_transform_edt(generated[:, :, 3] < 240, return_indices=True)
        rgb = generated[indices[0], indices[1], :3]
        work = np.dstack((rgb, alpha))
        work[alpha == 0] = 0
        cell = Image.fromarray(work).resize(STAGE, Image.Resampling.LANCZOS)
        pixels = np.array(cell)
        # Keep all visible coverage inside the original envelope after filtering.
        pixels[np.array(source.getchannel("A")) == 0] = 0
        cells.append(pixels)

    placements = {
        "pc01bod": (0, 30, 33), "pc01lhu": (0, 138, 150), "pc01rhd": (0, 29, 110),
        "pc01rhu": (1, 27, 117), "pc01rhb": (1, 27, 118),
    }
    originals, restored, parts = {}, {}, {}
    for name, (cell_id, x, y) in placements.items():
        asset = catalog["assets"][name]
        native = Image.open(REVIEW / asset["native"]).convert("RGBA")
        size = tuple(2 * v for v in native.size)
        original = native.resize(size, Image.Resampling.NEAREST)
        originals[name] = original
        x0, y0 = x * 2, y * 2
        output = cells[cell_id][y0:y0 + size[1], x0:x0 + size[0]].copy()
        # Original part masks divide ownership at the joints; only the external
        # assembled silhouette has been smoothed. No cut-line erosion or offset.
        output[np.array(original.getchannel("A")) == 0] = 0
        image = Image.fromarray(output)
        path = HERE / f"{name}.png"
        image.save(path, optimize=True)
        restored[name] = image
        parts[name] = {"path": path.name, "sha256": digest(path), "size": list(size),
                       "xy_x2": [x0, y0], "source_cell": cell_id, "source": asset["source"],
                       "source_sha256": asset["sourceHash"], **measure(original, image)}

    poses = {}
    for pose in definition["pose_layers"]:
        if pose["pose"] == "shield":
            continue
        original_stage = Image.new("RGBA", STAGE)
        restored_stage = Image.new("RGBA", STAGE)
        for name, x, y in pose["layers"]:
            original_stage.alpha_composite(originals[name], (x * 2, y * 2))
            restored_stage.alpha_composite(restored[name], (x * 2, y * 2))
        restored_stage.save(HERE / f"restored_{pose['pose']}.png", optimize=True)
        original_stage.save(HERE / f"original_{pose['pose']}.png", optimize=True)
        legacy = Image.open(HERE.parent / "mask_locked_20260924" / f"restored_{pose['pose']}.png")
        comparison = Image.new("RGBA", (700, 756))
        comparison.alpha_composite(legacy)
        comparison.alpha_composite(restored_stage, (350, 0))
        comparison.save(HERE / f"comparison_{pose['pose']}.png", optimize=True)
        native_mask = np.array(original_stage.getchannel("A")) > 0
        result_mask = np.array(restored_stage.getchannel("A")) > 0
        proof = np.zeros((STAGE[1], STAGE[0], 4), dtype=np.uint8)
        proof[native_mask] = [90, 115, 145, 180]
        proof[result_mask] = [75, 195, 100, 255]
        Image.fromarray(proof).save(HERE / f"mask_{pose['pose']}.png", optimize=True)
        poses[pose["pose"]] = {"body": "pc01bod.png", "layers": pose["layers"],
                               **measure(original_stage, restored_stage)}

    manifest = {
        "schema": "openyamm-pc01-contained-restoration-v1", "status": "visual_review_pending",
        "raw": {"path": "../mask_locked_20260924/raw_v1.png", "sha256": digest(raw_path),
                "size": list(raw.size), "native_sampling": [raw.width / 350, raw.height / 378]},
        "new_generation": False, "body_count": 1,
        "mapping": "Whole raw canvas mapped to native coordinates; no per-part warp, shrink or translation.",
        "alpha": "Generated alpha limited by an inward-antialiased native envelope, then split at original joints.",
        "legacy_rgb_copied": False,
        "parts": parts, "poses": poses,
        "limitations": ["pc01lho shield hand remains original.",
                        "Source master detail is unchanged; this improves contour extraction, not texture resolution.",
                        "Individual equipment candidates still need visual review."],
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"parts": parts, "poses": poses}, indent=2))


if __name__ == "__main__":
    main()
