"""Preview a grip-hand edit on the original alpha footprint; never approve it automatically."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
FOLDER = HERE / "prepared/doll_01"


def alpha_bbox(image):
    return image.getchannel("A").point(lambda value: 255 if value >= 128 else 0).getbbox()


def main():
    manifest = json.loads((FOLDER / "manifest.json").read_text())
    x, y, width, height = manifest["cells"]["pc01rhu"]["rect"]
    source = Image.open(FOLDER / "body_and_limbs_original_x2.png").convert("RGBA")
    original = source.crop((x, y, x + width, y + height))
    generated = Image.open(FOLDER / "raw_grip_v2.png").convert("RGBA")
    generated_bbox = alpha_bbox(generated)
    original_bbox = alpha_bbox(original)
    if not generated_bbox or not original_bbox:
        raise ValueError("Missing grip silhouette")
    # The new art changed the object's width/height ratio. This affine preview measures
    # whether its texture survives the original shape; it is not a valid geometry repair.
    cropped = generated.crop(generated_bbox)
    normalized = cropped.resize((original_bbox[2] - original_bbox[0],
                                 original_bbox[3] - original_bbox[1]), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", original.size)
    canvas.alpha_composite(normalized, original_bbox[:2])
    pixels = np.asarray(canvas).copy()
    pixels[:, :, 3] = np.asarray(original.getchannel("A"))
    locked = Image.fromarray(pixels, "RGBA")
    out = FOLDER / "grip_v2_geometry_locked_preview.png"
    locked.save(out, optimize=True)

    pose_sheet = Image.new("RGBA", (4 * 350 + 3 * 12, 756), "#253137")
    for index, pose in enumerate(manifest["pose_layers"]):
        canvas = Image.new("RGBA", (350, 756))
        for name, position_x, position_y in pose["layers"]:
            art = locked if name == "pc01rhu" else Image.open(FOLDER / "pilot_v1" / (name + ".png")).convert("RGBA")
            canvas.alpha_composite(art, (position_x * 2, position_y * 2))
        pose_sheet.alpha_composite(canvas, (index * 362, 0))
    assembled = FOLDER / "assembled_grip_v2_geometry_locked_preview.png"
    pose_sheet.save(assembled, optimize=True)
    report = {"schema": "openyamm-paperdoll-grip-v2-preview", "visual_approval": False,
              "disposition": "rejected_geometry_diagnostic_only",
              "original_alpha_bbox": list(original_bbox), "generated_alpha_bbox": list(generated_bbox),
              "original_bbox_aspect": round((original_bbox[2] - original_bbox[0]) /
                                            (original_bbox[3] - original_bbox[1]), 4),
              "generated_bbox_aspect": round((generated_bbox[2] - generated_bbox[0]) /
                                             (generated_bbox[3] - generated_bbox[1]), 4),
              "alpha_exact": np.array_equal(np.asarray(locked.getchannel("A")),
                                            np.asarray(original.getchannel("A"))),
              "note": "The imagegen return is deformed to the original bbox and alpha for diagnosis only. "
                      "It is not an accepted sprite or a proven art restoration."}
    (FOLDER / "grip_v2_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
