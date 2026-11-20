#!/usr/bin/env python3
"""Make unapproved alpha-cleanup comparisons for selected HUD cutouts."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from matte import extract  # noqa: E402


PILOT_NAMES = ("butn1u", "butn1d", "butn2u", "butn2d", "butn4u", "butn4d", "asiR07", "mapframe",
               "attack_default", "joystick_base_active", "Ui-FrSp")
PARAMETERS = {
    "butn1u": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2, "fringe_radius": 6},
    "butn1d": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2, "fringe_radius": 6},
    "butn2u": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2, "fringe_radius": 6},
    "butn2d": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2, "fringe_radius": 6},
    "butn4u": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2, "fringe_radius": 6},
    "butn4d": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2, "fringe_radius": 6},
    "asiR07": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2, "fringe_radius": 7},
    "mapframe": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2, "fringe_radius": 6},
    "attack_default": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2,
                       "fringe_radius": 6},
    "joystick_base_active": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2,
                             "fringe_radius": 6},
    "Ui-FrSp": {"background_distance": .04, "foreground_distance": .18, "core_radius": 2, "fringe_radius": 6},
}
VISUAL_NOTES = {
    "butn1u": "Exterior magenta is removed; compare scroll size and placement before fitting.",
    "butn1d": "Exterior magenta is removed; compare pressed-state shape and placement before fitting.",
    "butn2u": "Exterior magenta is removed; compare tent size and position with the native button.",
    "butn2d": "Exterior magenta is removed; compare pressed-state tent geometry with the up state.",
    "butn4u": "Exterior magenta is removed, but the green rectangular backing remains behind the key.",
    "butn4d": "Exterior magenta is removed, but the green rectangular backing remains behind the key.",
    "asiR07": "Cloud edge no longer has visible pink; check soft edge and native position.",
    "mapframe": "Aperture no longer has visible pink specks; check border registration.",
    "attack_default": "Exterior magenta is removed; review the button corner contour at actual size.",
    "joystick_base_active": "Exterior magenta is removed; review the circular edge and active/default state pair.",
    "Ui-FrSp": "Thin frame is matted for diagnosis; check all four rails for clipping.",
}


def read_data() -> dict:
    source = (HERE / "data.js").read_text()
    return json.loads(source.removeprefix("window.HUD_REVIEW_DATA = ").removesuffix(";\n"))


def measures(image: Image.Image, native: Image.Image) -> dict:
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    alpha = rgba[:, :, 3] >= 128
    expected_clear = np.asarray(native.convert("RGBA"))[:, :, 3] < 128
    expected_clear = np.repeat(np.repeat(expected_clear, 2, axis=0), 2, axis=1)
    chroma = np.minimum(rgba[:, :, 0].astype(np.int16), rgba[:, :, 2].astype(np.int16))
    chroma -= rgba[:, :, 1].astype(np.int16)
    pink = alpha & (chroma >= 90) & (rgba[:, :, 0] >= 150) & (rgba[:, :, 2] >= 150)
    return {
        "transparent_pct": round(100 * float((~alpha).mean()), 2),
        "opaque_on_native_clear_pct": round(100 * float((alpha & expected_clear).sum()) / max(1, expected_clear.sum()), 2),
        "opaque_magenta_pct": round(100 * float(pink.mean()), 2),
    }


def comparison(name: str, native: Image.Image, candidate: Image.Image, cleaned: Image.Image, output: Path) -> None:
    cell_w = 340
    cell_h = 275
    sheet = Image.new("RGB", (cell_w * 3, cell_h * 2), "#182128")
    draw = ImageDraw.Draw(sheet)
    variants = (native.resize(candidate.size, Image.Resampling.NEAREST), candidate, cleaned)
    titles = ("Native nearest x2", "Current candidate", "Matte pilot · unapproved")
    backgrounds = ("#1b2227", "#d6ccb7")
    for row, background in enumerate(backgrounds):
        for column, (image, title) in enumerate(zip(variants, titles)):
            canvas = Image.new("RGBA", image.size, background)
            canvas.alpha_composite(image.convert("RGBA"))
            thumb = canvas.convert("RGB")
            thumb.thumbnail((cell_w - 20, cell_h - 45), Image.Resampling.NEAREST)
            x = column * cell_w + (cell_w - thumb.width) // 2
            y = row * cell_h + 32 + (cell_h - 45 - thumb.height) // 2
            sheet.paste(thumb, (x, y))
            draw.text((column * cell_w + 10, row * cell_h + 9), f"{name}: {title}", fill="white")
    sheet.save(output)


def main() -> None:
    data = read_data()["assets"]
    output = HERE / "diagnostic_alpha"
    output.mkdir(exist_ok=True)
    rows = []
    for name in PILOT_NAMES:
        asset = data[name.lower()]
        with Image.open(HERE / asset["native"]) as source:
            native = source.convert("RGBA")
        with Image.open(HERE / asset["restored"]["original"]) as source:
            candidate = source.convert("RGBA")
        with Image.open(HERE / (asset["restored"].get("keyed_image") or asset["restored"]["image"])) as source:
            display = source.convert("RGBA")
        cleaned, params = extract(candidate, **PARAMETERS[name])
        cleaned.save(output / f"{name.lower()}-matte-pilot.png")
        comparison(name, native, display, cleaned, output / f"{name.lower()}-comparison.png")
        rows.append({"name": name, "target": asset["target"],
                     "current_display": measures(display, native), "pilot": measures(cleaned, native),
                     "parameters": params, "source": asset["restored"]["original"],
                     "source_sha256": hashlib.sha256((HERE / asset["restored"]["original"]).read_bytes()).hexdigest(),
                     "visual_note": VISUAL_NOTES[name],
                     "status": "diagnostic only; visual and registration review required"})
    (output / "measurements.json").write_text(json.dumps(rows, indent=2) + "\n")
    with (output / "measurements.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "target", "current_display", "pilot", "status"])
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row[key] for key in writer.fieldnames})
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
