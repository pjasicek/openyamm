#!/usr/bin/env python3
"""Produce hash-bound true-alpha review candidates from uniform magenta HUD mattes."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
OUT = HERE / "alpha_repair"
sys.path.insert(0, str(HERE.parent))
from matte import extract  # noqa: E402


DEFAULT_PARAMETERS = {"background_distance": .04, "foreground_distance": .18,
                      "core_radius": 2, "fringe_radius": 6}
SPECIAL_PARAMETERS = {"asir07": {**DEFAULT_PARAMETERS, "fringe_radius": 7}}
MATTE_COLOR = np.array([250, 3, 250], dtype=np.int16)


def read_data() -> dict:
    source = (HERE / "data.js").read_text()
    return json.loads(source.removeprefix("window.HUD_REVIEW_DATA = ").removesuffix(";\n"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgba(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return source.convert("RGBA")


def score(image: Image.Image, expected_clear: np.ndarray) -> dict:
    pixels = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    opaque = pixels[:, :, 3] >= 128
    rgb = pixels[:, :, :3].astype(np.int16)
    chroma = np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1]
    magenta = opaque & (chroma >= 90) & (rgb[:, :, 0] >= 150) & (rgb[:, :, 2] >= 150)
    return {
        "transparent_pct": round(100 * float((~opaque).mean()), 3),
        "opacity_on_native_clear_pct": round(
            100 * float((opaque & expected_clear).sum()) / max(1, expected_clear.sum()), 3),
        "opaque_magenta_pct": round(100 * float(magenta.mean()), 3),
    }


def contact_image(image: Image.Image, background: str, width: int = 102, height: int = 100) -> Image.Image:
    canvas = Image.new("RGBA", image.size, background)
    canvas.alpha_composite(image.convert("RGBA"))
    thumb = canvas.convert("RGB")
    thumb.thumbnail((width, height), Image.Resampling.LANCZOS)
    result = Image.new("RGB", (width, height), background)
    result.paste(thumb, ((width - thumb.width) // 2, (height - thumb.height) // 2))
    return result


def contact_pages(records: list[dict]) -> None:
    entries = [record for record in records if record.get("output")]
    for start in range(0, len(entries), 24):
        page = entries[start:start + 24]
        width, row_height, columns = 1100, 145, 2
        sheet = Image.new("RGB", (width, 52 + row_height * 12), "#1b252b")
        draw = ImageDraw.Draw(sheet)
        draw.text((14, 14), "Native | current keyed | true-alpha repair | repair on light", fill="#f5dfa6")
        for index, record in enumerate(page):
            tile_x = (index % columns) * 550
            tile_y = 52 + (index // columns) * row_height
            draw.text((tile_x + 12, tile_y + 3), record["name"] + "  " + record["status"], fill="white")
            images = (
                rgba(HERE / record["native_path"]).resize(record["size"], Image.Resampling.NEAREST),
                rgba(HERE / record["current_path"]),
                rgba(HERE / record["output"]),
                rgba(HERE / record["output"]),
            )
            for column, art in enumerate(images):
                background = "#ddd2bb" if column == 3 else "#172127"
                sheet.paste(contact_image(art, background), (tile_x + 12 + column * 132, tile_y + 26))
        sheet.save(OUT / f"contact-{start // 24 + 1:02}.png")


def main() -> None:
    data = read_data()["assets"]
    output_dir = OUT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for name, asset in sorted(data.items()):
        restored = asset.get("restored", {})
        if not restored.get("image") or restored.get("status") == "staged":
            continue
        native_path = HERE / asset["native"]
        source_path = HERE / restored["original"]
        native = rgba(native_path)
        source = rgba(source_path)
        expected_clear = np.asarray(native)[:, :, 3] < 128
        expected_clear = np.repeat(np.repeat(expected_clear, 2, axis=0), 2, axis=1)
        if not expected_clear.any():
            continue
        rgb = np.asarray(source)[:, :, :3].astype(np.int16)
        matte = np.abs(rgb - MATTE_COLOR).max(axis=2) <= 10
        matte_on_clear = float((matte & expected_clear).sum()) / expected_clear.sum()
        if matte_on_clear < .5:
            continue

        current_path = HERE / (restored.get("keyed_image") or restored["image"])
        current = rgba(current_path)
        parameters = SPECIAL_PARAMETERS.get(name, DEFAULT_PARAMETERS)
        record = {"name": asset["name"], "target": asset["target"], "status": "not processed",
                  "source": restored["original"], "source_sha256": sha256(source_path),
                  "native_path": asset["native"], "native_sha256": sha256(native_path),
                  "current_path": (restored.get("keyed_image") or restored["image"]), "size": list(source.size),
                  "source_matte_on_native_clear_pct": round(100 * matte_on_clear, 3),
                  "current": score(current, expected_clear), "parameters": parameters}
        try:
            cleaned, details = extract(source, **parameters)
            record["parameters"] = details
            repaired = score(cleaned, expected_clear)
            record["repaired"] = repaired
            if cleaned.size != source.size or repaired["transparent_pct"] < 1:
                record["status"] = "hold_alpha_geometry"
            elif repaired["opaque_magenta_pct"] > .5:
                record["status"] = "hold_residual_magenta"
            elif repaired["opacity_on_native_clear_pct"] >= record["current"]["opacity_on_native_clear_pct"]:
                record["status"] = "hold_no_clear_improvement"
            else:
                record["status"] = "alpha_repaired_review_required"
            destination = output_dir / (asset["target"].rsplit(".", 1)[0] + ".png")
            cleaned.save(destination, optimize=True)
            record["output"] = destination.relative_to(HERE).as_posix()
            record["output_sha256"] = sha256(destination)
        except (AssertionError, ValueError) as error:
            record["status"] = "hold_extraction_failed"
            record["error"] = str(error)
        records.append(record)

    manifest = {"schema": "openyamm-hud-alpha-repair-v1",
                "method": "spatial magenta matte extraction; full exact-x2 canvas retained; review only",
                "selection": "opaque near-#FA03FA matte covers at least half of native-clear pixels",
                "counts": {status: sum(record["status"] == status for record in records)
                           for status in sorted(set(record["status"] for record in records))},
                "records": records}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    contact_pages(records)
    print(json.dumps({"selected": len(records), "counts": manifest["counts"]}, indent=2))


if __name__ == "__main__":
    main()
