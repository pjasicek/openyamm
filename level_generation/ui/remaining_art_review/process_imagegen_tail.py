#!/usr/bin/env python3
"""Finish tiny icons that imagegen left empty and the backhand UI veil."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from process_imagegen_regen import HERE, RUN


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(target_id: str, image: Image.Image, source_hash: str, method: str,
         raw_path: Path | None = None) -> dict:
    destination = RUN / "tail_candidates" / target_id / "candidate-2x.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, optimize=True)
    record = {"status": "candidate_technical", "source_sha256": source_hash,
              "artifact": str(destination.relative_to(HERE)), "artifact_sha256": sha256(destination),
              "method": method}
    if raw_path:
        record.update({"raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path)})
    return record


def arrow(down: bool) -> Image.Image:
    scale = 8
    high = Image.new("RGBA", (14 * scale, 14 * scale))
    draw = ImageDraw.Draw(high)
    outside = [(7, 0), (14, 7), (9, 7), (9, 14), (5, 14), (5, 7), (0, 7)]
    inside = [(7, 2), (11, 6), (8, 6), (8, 14), (6, 14), (6, 6), (3, 6)]
    draw.polygon([(round(x * scale), round(y * scale)) for x, y in outside], fill=(113, 113, 113, 255))
    draw.polygon([(round(x * scale), round(y * scale)) for x, y in inside], fill=(252, 252, 252, 255))
    result = high.convert("RGBa").resize((14, 14), Image.Resampling.LANCZOS).convert("RGBA")
    return result.transpose(Image.Transpose.ROTATE_180) if down else result


def main() -> None:
    first = json.loads((RUN / "report.json").read_text())["items"]
    retry = json.loads((RUN / "retry_report.json").read_text())["items"]
    report = {"schema": 1, "tool": "imagegen retry with deterministic tiny-geometry cleanup", "items": {}}
    for name, down in (("mapdir2.bmp", False), ("mapdir6.bmp", True)):
        target_id = f"engine--icons--{name}"
        if retry[target_id]["status"] != "hold_empty_foreground":
            raise ValueError(f"Tiny arrow imagegen return changed: {target_id}")
        report["items"][target_id] = save(
            target_id, arrow(down), first[target_id]["source_sha256"],
            "smooth vector redraw of exact 7x7 gray-white native arrow after two empty imagegen returns")
    target_id = "engine--icons--none.bmp"
    with Image.open(HERE / "originals" / f"{target_id}.png") as original:
        if original.convert("RGBA").getchannel("A").getbbox():
            raise ValueError("Native empty sprite changed")
    report["items"][target_id] = save(
        target_id, Image.new("RGBA", (2, 2)), first[target_id]["source_sha256"],
        "preserved intentional fully transparent sprite after two empty imagegen returns")

    target_id = "engine--icons--backhand.bmp"
    plan = json.loads((RUN / "third-backhand.json").read_text())
    reference = HERE / plan["reference"]
    raw_path = RUN / "returns/third-backhand.png"
    if sha256(reference) != plan["reference_sha256"]:
        raise ValueError("Changed backhand reference")
    with Image.open(HERE / "originals" / f"{target_id}.png") as original, Image.open(raw_path) as raw:
        original = original.convert("RGBA")
        if sha256(HERE / "originals" / f"{target_id}.png") != plan["cell"]["original_sha256"]:
            raise ValueError("Changed backhand original")
        if raw.width < original.width * 2 or raw.height < original.height * 2:
            raise ValueError("Backhand return below native 2x detail")
        candidate = raw.convert("RGB").resize((original.width * 2, original.height * 2),
                                              Image.Resampling.LANCZOS).convert("RGBA")
        source_alpha = np.asarray(original.getchannel("A"))
        native_panels = np.zeros(source_alpha.shape, dtype=bool)
        for box in ((16, 62, 67, 150), (108, 62, 158, 150), (16, 174, 159, 261)):
            native_panels[box[1]:box[3], box[0]:box[2]] = True
        veil_alpha = round(float((source_alpha[~native_panels] > 128).mean()) * 255)
        if not 120 <= veil_alpha <= 150:
            raise ValueError(f"Changed native stipple coverage: {veil_alpha}")
        mask = Image.new("L", candidate.size, veil_alpha)
        panel_layer = Image.new("L", candidate.size)
        draw = ImageDraw.Draw(panel_layer)
        # Bounds measured from the generated return after exact 2x resizing.
        for box in ((40, 129, 140, 301), (213, 129, 313, 301), (40, 341, 314, 539)):
            draw.rectangle(box, fill=255)
        panel_layer = panel_layer.filter(ImageFilter.GaussianBlur(radius=0.7))
        mask = Image.fromarray(np.maximum(np.asarray(mask), np.asarray(panel_layer)).astype(np.uint8), "L")
        candidate.putalpha(mask)
    report["items"][target_id] = save(
        target_id, candidate, first[target_id]["source_sha256"],
        f"full-screen imagegen edit; measured generated panels opaque, native stippled veil averaged to alpha {veil_alpha}",
        raw_path)
    (RUN / "tail_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Prepared {len(report['items'])} final candidates")


if __name__ == "__main__":
    main()
