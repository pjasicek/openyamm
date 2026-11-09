#!/usr/bin/env python3
"""Correct the fading white ankh frame after a color-faithful imagegen retry."""

import hashlib
import json

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

from process_imagegen_regen import HERE, RUN, metrics, x2_resize


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = json.loads((RUN / "third-ankh-palette.json").read_text())
    reference = HERE / plan["reference"]
    raw_path = RUN / "returns/third-ankh-palette.png"
    if sha256(reference) != plan["reference_sha256"]:
        raise ValueError("Changed ankh reference")
    with Image.open(raw_path) as file:
        raw = file.convert("RGBA")
    cell = plan["cells"][-1]
    target_id = cell["id"]
    x, y, width, height = cell["rect"]
    sx, sy = raw.width / plan["reference_size"][0], raw.height / plan["reference_size"][1]
    search = (max(0, round(x * sx) - 12), max(0, round(y * sy) - 12),
              min(raw.width, round((x + width) * sx) + 12),
              min(raw.height, round((y + height) * sy) + 12))
    slot = raw.crop(search)
    alpha = np.asarray(slot.getchannel("A")) >= 64
    yy, xx = np.where(alpha)
    region = (search[0] + int(xx.min()), search[1] + int(yy.min()),
              search[0] + int(xx.max()) + 1, search[1] + int(yy.max()) + 1)
    pixels = np.array(raw.crop(region), dtype=np.uint8)
    rgb = pixels[:, :, :3].astype(np.int16)
    pink = (rgb[:, :, 0] - rgb[:, :, 1] > 55) & (rgb[:, :, 2] - rgb[:, :, 1] > 35) \
        & (pixels[:, :, 3] > 0)
    valid = (pixels[:, :, 3] >= 64) & ~pink
    nearest = distance_transform_edt(~valid, return_distances=False, return_indices=True)
    pixels[pink, :3] = pixels[nearest[0][pink], nearest[1][pink], :3]
    original_path = HERE / "originals" / f"{target_id}.png"
    if sha256(original_path) != cell["original_sha256"]:
        raise ValueError("Changed original ankh")
    with Image.open(original_path) as file:
        original = file.convert("RGBA")
    native = np.asarray(original.getchannel("A")) >= 128
    yy, xx = np.where(native)
    box = (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1)
    if region[2] - region[0] < (box[2] - box[0]) * 2 \
            or region[3] - region[1] < (box[3] - box[1]) * 2:
        raise ValueError("Ankh return below native 2x detail")
    fitted = x2_resize(Image.fromarray(pixels, "RGBA"), ((box[2] - box[0]) * 2, (box[3] - box[1]) * 2))
    candidate = Image.new("RGBA", (original.width * 2, original.height * 2))
    candidate.alpha_composite(fitted, (box[0] * 2, box[1] * 2))
    destination = RUN / "palette_candidates" / target_id / "candidate-2x.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    candidate.save(destination, optimize=True)
    report = {"schema": 1, "tool": "built-in image_gen with measured pink-matte decontamination",
              "items": {target_id: {
                  "status": "candidate_technical", "source_sha256": cell["source_sha256"],
                  "artifact": str(destination.relative_to(HERE)), "artifact_sha256": sha256(destination),
                  "method": "color-faithful four-frame imagegen retry; pink matte colors replaced from nearby ivory art",
                  "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path),
                  "returned_region": list(region), "native_opaque_box": list(box),
                  "decontaminated_raw_pixels": int(pink.sum()),
                  "metrics_after_fit": metrics(x2_resize(original, candidate.size), candidate),
              }}}
    (RUN / "palette_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Prepared {target_id}; replaced {pink.sum()} pink matte pixels")


if __name__ == "__main__":
    main()
