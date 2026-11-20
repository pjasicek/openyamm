#!/usr/bin/env python3
"""Make aligned native and current x2 references for the active but20–but26 triplets."""

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[5]
REVIEW = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
FAMILIES = [f"but{number}" for number in range(20, 27)]
STATES = "uhd"
CELL_WIDTH = 300
CELL_HEIGHT = 104
CELL_GAP_X = 22
CELL_GAP_Y = 30
MARGIN_X = 20
MARGIN_TOP = 44
SHEET_WIDTH = MARGIN_X * 2 + CELL_WIDTH * 3 + CELL_GAP_X * 2
SHEET_HEIGHT = MARGIN_TOP + CELL_HEIGHT * 7 + CELL_GAP_Y * 6 + 20


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_sheet(kind, records):
    image = Image.new("RGB", (SHEET_WIDTH, SHEET_HEIGHT), (45, 44, 42))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for column, state in enumerate(STATES):
        x = MARGIN_X + column * (CELL_WIDTH + CELL_GAP_X)
        draw.text((x, 13), f"{state.upper()}  {'native original' if kind == 'native' else 'current x2 review'}", fill="white", font=font)
    for row, family in enumerate(FAMILIES):
        for column, state in enumerate(STATES):
            name = family + state
            record = records[name]
            source = ROOT / record["native"] if kind == "native" else REVIEW / record["current"]
            with Image.open(source) as loaded:
                artwork = loaded.convert("RGBA")
                if kind == "native":
                    artwork = artwork.resize((CELL_WIDTH, CELL_HEIGHT), Image.Resampling.NEAREST)
                else:
                    artwork = artwork.resize((CELL_WIDTH, CELL_HEIGHT), Image.Resampling.LANCZOS)
            x = MARGIN_X + column * (CELL_WIDTH + CELL_GAP_X)
            y = MARGIN_TOP + row * (CELL_HEIGHT + CELL_GAP_Y)
            image.paste(artwork, (x, y), artwork)
            draw.rectangle((x - 1, y - 1, x + CELL_WIDTH, y + CELL_HEIGHT), outline=(112, 109, 101), width=1)
            draw.text((x + 3, y + CELL_HEIGHT + 4), name, fill="white", font=font)
    output = HERE / f"{kind}_reference.png"
    image.save(output)
    return output


def main():
    data = json.loads((REVIEW / "data.js").read_text().removeprefix("window.HUD_REVIEW_DATA = ").removesuffix(";\n"))
    records = {}
    for family in FAMILIES:
        for state in STATES:
            name = family + state
            asset = data["assets"][name]
            native_path = ROOT / asset["source"]
            native_preview_path = REVIEW / asset["native"]
            prior_review = asset["restored"].get("button_triplet_repair", {}).get("previous")
            current_review = prior_review or asset["restored"]["image"]
            current_path = REVIEW / current_review
            original_path = REVIEW / asset["restored"]["original"]
            if tuple(asset["native_size"]) != (75, 26) or not asset["restored"]["exact_x2"]:
                raise ValueError(f"Not a fitted 75x26 triplet member: {name}")
            records[name] = {
                "target": asset["target"],
                "native": asset["source"],
                "native_sha256": sha256(native_path),
                "native_preview_sha256": sha256(native_preview_path),
                "current": current_review,
                "current_sha256": sha256(current_path),
                "original": asset["restored"]["original"],
                "original_sha256": sha256(original_path),
                "uses": asset["uses"],
            }
    native_sheet = make_sheet("native", records)
    current_sheet = make_sheet("current", records)
    manifest = {
        "schema": "openyamm-button-triplets-v1",
        "families": FAMILIES,
        "states": STATES,
        "reference_cell_pixels": [CELL_WIDTH, CELL_HEIGHT],
        "reference_native_scale": 4,
        "reference_current_scale": 2,
        "native_sheet_sha256": sha256(native_sheet),
        "current_sheet_sha256": sha256(current_sheet),
        "records": records,
    }
    (HERE / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared {len(records)} active button states in two aligned reference sheets.")


if __name__ == "__main__":
    main()
