#!/usr/bin/env python3
"""Extract the reviewed 21-button imagegen sheet to exact native-x2 review canvases."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
MASTER = HERE / "imagegen_master_v2.png"
FAMILIES = [f"but{number}" for number in range(20, 27)]
STATES = "uhd"
X_BOUNDS = [(25, 412), (437, 823), (849, 1239)]
Y_BOUNDS = [(47, 187), (205, 345), (364, 506), (526, 670), (691, 835), (856, 998), (1018, 1163)]
OUTPUT_SIZE = (150, 52)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def luminance(image):
    rgb = np.asarray(image.convert("RGB").resize((75, 26), Image.Resampling.LANCZOS), dtype=np.float32)
    return rgb[:, :, 0] * 0.2126 + rgb[:, :, 1] * 0.7152 + rgb[:, :, 2] * 0.0722


def state_metrics(images):
    values = []
    region = (slice(4, 23), slice(7, 68))
    for family in FAMILIES:
        u = luminance(images[family + "u"])[region]
        h = luminance(images[family + "h"])[region]
        d = luminance(images[family + "d"])[region]
        values.append({
            "family": family,
            "highlight_mean_luminance_delta": round(float(np.mean(h - u)), 2),
            "highlight_positive_area_pct": round(float(np.mean((h - u) > 8) * 100), 2),
            "pressed_mean_luminance_delta": round(float(np.mean(d - u)), 2),
        })
    return values


def main():
    source_manifest = json.loads((HERE / "source_manifest.json").read_text())
    if sha256(HERE / "native_reference.png") != source_manifest["native_sheet_sha256"]:
        raise ValueError("Native reference changed; prepare the sheet again")
    if sha256(HERE / "current_reference.png") != source_manifest["current_sheet_sha256"]:
        raise ValueError("Current reference changed; prepare the sheet again")
    output_dir = HERE / "outputs_v2"
    output_dir.mkdir(exist_ok=True)
    sheet = Image.open(MASTER).convert("RGB")
    if sheet.size != (1262, 1246):
        raise ValueError(f"Unexpected imagegen master size: {sheet.size}")
    native_images = {}
    old_images = {}
    new_images = {}
    records = []
    for row, family in enumerate(FAMILIES):
        for column, state in enumerate(STATES):
            name = family + state
            x0, x1 = X_BOUNDS[column]
            y0, y1 = Y_BOUNDS[row]
            crop = sheet.crop((x0, y0, x1, y1))
            fitted = crop.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS).convert("RGBA")
            output = output_dir / f"engine--icons--{name}.png"
            fitted.save(output)
            record = source_manifest["records"][name]
            native_path = REVIEW.parents[3] / record["native"]
            old_path = REVIEW / record["current"]
            if sha256(native_path) != record["native_sha256"] or sha256(old_path) != record["current_sha256"]:
                raise ValueError(f"Inputs changed after reference preparation: {name}")
            native_images[name] = Image.open(native_path).convert("RGBA")
            old_images[name] = Image.open(old_path).convert("RGBA")
            new_images[name] = fitted
            pixels = np.asarray(fitted)
            magenta = (pixels[:, :, 0] >= 220) & (pixels[:, :, 1] <= 40) & (pixels[:, :, 2] >= 220)
            records.append({
                "name": name,
                "target": record["target"],
                "source_sha256": record["original_sha256"],
                "current_sha256": record["current_sha256"],
                "native_sha256": record["native_sha256"],
                "native_preview_sha256": record["native_preview_sha256"],
                "crop": [x0, y0, x1, y1],
                "output": str(output.relative_to(REVIEW)),
                "output_sha256": sha256(output),
                "size": list(fitted.size),
                "alpha_minimum": int(pixels[:, :, 3].min()),
                "near_key_magenta_pixels": int(magenta.sum()),
            })
    metrics = {
        "native": state_metrics(native_images),
        "previous_x2": state_metrics(old_images),
        "imagegen_v2": state_metrics(new_images),
    }
    manifest = {
        "schema": "openyamm-button-triplet-review-v1",
        "status": "unapproved_review_candidate",
        "tool": "built-in imagegen",
        "master": MASTER.name,
        "master_sha256": sha256(MASTER),
        "source_manifest_sha256": sha256(HERE / "source_manifest.json"),
        "prompt": "imagegen-call-v2.txt",
        "prompt_sha256": sha256(HERE / "imagegen-call-v2.txt"),
        "count": len(records),
        "metrics": metrics,
        "records": records,
    }
    (HERE / "review_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    font = ImageFont.load_default()
    contact = Image.new("RGB", (3 * 310 + 20, 7 * 112 + 20), (36, 35, 33))
    draw = ImageDraw.Draw(contact)
    for row, family in enumerate(FAMILIES):
        for column, state in enumerate(STATES):
            name = family + state
            image = new_images[name].convert("RGB").resize((300, 104), Image.Resampling.LANCZOS)
            x, y = 10 + column * 310, 10 + row * 112
            contact.paste(image, (x, y))
            draw.text((x + 3, y + 105), name, fill="white", font=font)
    contact.save(HERE / "fitted_contact_v2.png")
    print(f"Fitted {len(records)} opaque x2 button states from {MASTER.name}")
    for group, values in metrics.items():
        print(group, [(v["family"], v["highlight_mean_luminance_delta"],
                       v["pressed_mean_luminance_delta"]) for v in values])


if __name__ == "__main__":
    main()
