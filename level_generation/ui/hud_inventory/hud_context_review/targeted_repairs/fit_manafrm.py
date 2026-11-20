#!/usr/bin/env python3
"""Fit the true-alpha mana frame master to the native 20 × 102 HUD canvas for review."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
MASTER = HERE / "manafrm-imagegen-master.png"
OUTPUT = HERE / "manafrm-review-x2.png"
SOURCE_CANDIDATE_SHA256 = "d7e33aefaf1fa5c64edb35eb19f8e2e394a49f2fc2c5799b8be4ff1ee80a91ce"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source_data = (REVIEW / "data.js").read_text()
    asset_data = json.loads(source_data.removeprefix("window.HUD_REVIEW_DATA = ").removesuffix(";\n"))
    source_candidate = REVIEW / asset_data["assets"]["manafrm"]["restored"]["original"]
    native_source = REVIEW / "native/engine--icons--manafrm.png"
    if sha256(source_candidate) != SOURCE_CANDIDATE_SHA256:
        raise SystemExit("The source candidate changed; review the new art before reusing this imagegen repair")
    with Image.open(MASTER) as source:
        master = source.convert("RGBA")
    pixels = np.asarray(master, dtype=np.uint8)
    opaque = pixels[:, :, 3] >= 16
    ys, xs = np.nonzero(opaque)
    assert len(xs) > 0
    bounds = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    crop = master.crop(bounds)
    fitted = crop.convert("RGBa").resize((18, 102), Image.Resampling.LANCZOS).convert("RGBA")
    canvas = Image.new("RGBA", (20, 102))
    canvas.alpha_composite(fitted, (0, 0))
    # The generated right rail covers x15–17 at mid-height; native rails cover x16–17.
    # Clear only the extra x15 strip between the end joins so the blue fill channel stays open.
    fitted_pixels = np.asarray(canvas).copy()
    fitted_pixels[2:100, 15] = (0, 0, 0, 0)
    canvas = Image.fromarray(fitted_pixels, "RGBA")
    canvas.save(OUTPUT)

    with Image.open(REVIEW / "native/engine--icons--manafrm.png") as source:
        native = source.convert("RGBA").resize((20, 102), Image.Resampling.NEAREST)
    native_alpha = np.asarray(native)[:, :, 3] >= 128
    output_alpha = np.asarray(canvas)[:, :, 3] >= 128
    intersection = int((native_alpha & output_alpha).sum())
    union = int((native_alpha | output_alpha).sum())
    y = 51
    rows = {
        "native_mid_opaque_x": np.flatnonzero(native_alpha[y]).tolist(),
        "repaired_mid_opaque_x": np.flatnonzero(output_alpha[y]).tolist(),
    }
    comparison = Image.new("RGB", (600, 370), "#1b252b")
    draw = ImageDraw.Draw(comparison)
    draw.text((12, 10), "manaFRM native, wrong filled candidate, true-alpha imagegen repair", fill="#f5dfa6")
    images = (native, Image.open(REVIEW / "restored_display/engine--icons--manafrm.png").convert("RGBA"),
              canvas)
    for i, image in enumerate(images):
        x = 60 + i * 190
        background = Image.new("RGBA", image.size, "#26343a")
        background.alpha_composite(image)
        comparison.paste(background.convert("RGB").resize((60, 306), Image.Resampling.NEAREST), (x, 35))
        draw.text((x, 346), ("Native", "Wrong x2", "True-alpha repair")[i], fill="white")
    comparison.save(HERE / "manafrm-comparison.png")

    report = {"target": "engine--icons--manafrm.bmp", "status": "imagegen_true_alpha_review_required",
              "method": "built-in imagegen master; alpha-bounds crop; premultiplied resize to 18 × 102; "
                        "native offset 0,0; correct extra right-rail pixel x15 between y2 and y99",
              "master": MASTER.name, "master_sha256": sha256(MASTER), "master_size": master.size,
              "source_candidate_sha256": sha256(source_candidate), "native_sha256": sha256(native_source),
              "master_alpha_bounds": bounds, "output": OUTPUT.name, "output_sha256": sha256(OUTPUT),
              "output_size": canvas.size, "native_alpha_pixels_x2": int(native_alpha.sum()),
              "output_alpha_pixels": int(output_alpha.sum()),
              "silhouette_iou": round(intersection / union, 4) if union else 0,
              "native_transparent_pct": round(100 * (1 - native_alpha.mean()), 3),
              "output_transparent_pct": round(100 * (1 - output_alpha.mean()), 3), **rows}
    (HERE / "manafrm-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
