#!/usr/bin/env python3
"""Repair small review spills and literal UI geometry without changing other art."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, distance_transform_edt

from process_imagegen_regen import x2_resize


HERE = Path(__file__).resolve().parent
RUN = HERE / "review_repairs"
SPILLS = ("7item119", "7item263")
PLACEMENT = ("item066", "item070", "item078", "item247")
BASE_INPUTS = {
    "7item119": "extracted_retained/candidates/engine--icons--7item119.bmp.png",
    "7item263": "extracted_retained/candidates/engine--icons--7item263.bmp.png",
    "item066": "imagegen_regen/component_candidates/engine--icons--item066.bmp/candidate-2x.png",
    "item070": "imagegen_regen/candidates/engine--icons--item070.bmp/candidate-2x.png",
    "item078": "imagegen_regen/component_candidates/engine--icons--item078.bmp/candidate-2x.png",
    "item247": "imagegen_regen/candidates/engine--icons--item247.bmp/candidate-2x.png",
    "loadprog": "extracted_retained/candidates/engine--icons--loadprog.bmp.png",
    "map-pin2": "extracted_retained/candidates/engine--icons--map-pin2.bmp.png",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_and_input(item: dict) -> tuple[Image.Image, Image.Image, dict]:
    source = Image.open(HERE / item["original"]).convert("RGBA")
    path = HERE / BASE_INPUTS[item["name"]]
    previous = {}
    for report_name in ("spill_report.json", "ui_regen_report.json"):
        report_path = RUN / report_name
        if report_path.is_file():
            previous.update(json.loads(report_path.read_text())["items"])
    row = previous.get(item["id"])
    expected = row["input_sha256"] if row else item["candidates"][0]["sha256"]
    origin = "Imagegen restoration" if item["name"] in PLACEMENT else "Measured retained-sheet extraction"
    choice = {"path": BASE_INPUTS[item["name"]], "sha256": expected, "origin": origin}
    if sha256(path) != expected:
        raise ValueError(f"Changed candidate: {item['id']}")
    candidate = Image.open(path).convert("RGBA")
    if candidate.size != tuple(item["x2_size"]):
        raise ValueError(f"Wrong canvas: {item['id']}")
    return source, candidate, choice


def write_candidate(item: dict, image: Image.Image, choice: dict, method: str, subdir: str) -> dict:
    path = RUN / subdir / item["id"] / "candidate-2x.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)
    return {
        "status": "candidate_technical", "source_sha256": item["source_sha256"],
        "input_sha256": choice["sha256"], "artifact": str(path.relative_to(HERE)),
        "input_artifact": choice["path"], "input_origin": choice["origin"],
        "artifact_sha256": sha256(path), "origin": choice["origin"], "method": method,
    }


def repair_spill(source: Image.Image, candidate: Image.Image) -> tuple[Image.Image, int]:
    before = np.asarray(candidate).copy()
    rgb = before[:, :, :3].astype(np.int16)
    chroma = np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1]
    hot = (chroma > 18) & (before[:, :, 3] > 10)
    spill = hot | (binary_dilation(hot, iterations=1) & (chroma > 8) & (before[:, :, 3] > 10))
    _, nearest = distance_transform_edt(chroma > 8, return_indices=True)
    clean = before.copy()
    clean[spill, :3] = before[nearest[0][spill], nearest[1][spill], :3]
    # Let the native transparency resolve pink pixels located in original gaps.
    native_alpha = np.asarray(source.resize(candidate.size, Image.Resampling.LANCZOS).getchannel("A"))
    clean[spill & (native_alpha < 64), 3] = 0
    after = np.minimum(clean[:, :, 0].astype(np.int16), clean[:, :, 2].astype(np.int16)) \
        - clean[:, :, 1].astype(np.int16)
    if np.any((after > 18) & (clean[:, :, 3] > 10)):
        raise ValueError("Visible magenta survived local repair")
    return Image.fromarray(clean, "RGBA"), int(spill.sum())


def native_occupied_box(image: Image.Image) -> tuple[int, int, int, int]:
    yy, xx = np.where(np.asarray(image.getchannel("A")) >= 128)
    if not len(xx):
        raise ValueError("No foreground")
    return int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1


def correct_placement(source: Image.Image, candidate: Image.Image) -> Image.Image:
    source_box = tuple(value * 2 for value in native_occupied_box(source))
    candidate_box = native_occupied_box(candidate)
    target_size = (source_box[2] - source_box[0], source_box[3] - source_box[1])
    fitted = x2_resize(candidate.crop(candidate_box), target_size)
    result = Image.new("RGBA", candidate.size)
    result.alpha_composite(fitted, source_box[:2])
    return result


def redraw_loading(source: Image.Image) -> Image.Image:
    if source.size != (299, 14):
        raise ValueError("Unexpected loadprog native size")
    pixels = np.asarray(source)
    result = Image.new("RGBA", (598, 28))
    draw = ImageDraw.Draw(result)
    for index in range(20):
        x = index * 30
        native = pixels[:13, index * 15:index * 15 + 13, :3]
        # Each original tile is independent. Smooth its per-row blue progression
        # while retaining a separate rectangular bezel and transparent gutter.
        center = np.median(native[:, 3:10], axis=1)
        for y in range(26):
            position = y / 2
            low = min(12, int(position))
            high = min(12, low + 1)
            shade = (1 - (position - low)) * center[low] + (position - low) * center[high]
            color = tuple(int(value) for value in shade)
            draw.line((x, y, x + 25, y), fill=(*color, 255))
        left = tuple(int(value) for value in native[6, 0])
        right = tuple(int(value) for value in native[6, 12])
        draw.line((x, 0, x, 25), fill=(*left, 255))
        draw.line((x + 25, 0, x + 25, 25), fill=(*right, 255))
        draw.line((x + 1, 1, x + 24, 1), fill=(100, 146, min(255, 184 + index * 2), 255))
    return result


def redraw_pin(source: Image.Image) -> Image.Image:
    if source.size != (10, 10):
        raise ValueError("Unexpected map-pin2 native size")
    scale = 4
    large = Image.new("RGBA", (20 * scale, 20 * scale))
    draw = ImageDraw.Draw(large)
    draw.ellipse((0, 0, 17 * scale, 17 * scale), fill=(112, 78, 220, 255))
    draw.arc((1 * scale, 1 * scale, 16 * scale, 16 * scale), 105, 255,
             fill=(174, 139, 246, 255), width=2 * scale)
    draw.arc((1 * scale, 1 * scale, 16 * scale, 16 * scale), 275, 60,
             fill=(66, 41, 176, 255), width=2 * scale)
    draw.ellipse((5 * scale, 5 * scale, 12 * scale, 12 * scale), fill=(0, 0, 0, 0))
    draw.ellipse((7 * scale, 7 * scale, 10 * scale, 10 * scale), fill=(91, 60, 207, 255))
    return x2_resize(large, (20, 20))


def main() -> None:
    catalog = json.loads((HERE / "catalog.js").read_text().split("=", 1)[1].strip().removesuffix(";"))
    by_name = {item["name"]: item for item in catalog["items"]}
    report = {"schema": 1, "items": {}}
    for name in SPILLS:
        item = by_name[name]
        source, candidate, choice = source_and_input(item)
        clean, count = repair_spill(source, candidate)
        row = write_candidate(item, clean, choice,
                              f"local replacement of {count} magenta and halo pixels; native gaps retained",
                              "spill_candidates")
        row["spill_pixels_replaced"] = count
        report["items"][item["id"]] = row
    for name in PLACEMENT:
        item = by_name[name]
        source, candidate, choice = source_and_input(item)
        clean = correct_placement(source, candidate)
        report["items"][item["id"]] = write_candidate(
            item, clean, choice, "imagegen foreground refit to the original occupied bounds",
            "placement_candidates")
    (RUN / "spill_report.json").write_text(json.dumps(report, indent=2) + "\n")
    ui = {"schema": 1, "items": {}}
    for name, redraw in (("loadprog", redraw_loading), ("map-pin2", redraw_pin)):
        item = by_name[name]
        source, _, choice = source_and_input(item)
        clean = redraw(source)
        row = write_candidate(item, clean, choice, "native UI geometry redraw at exact 2x canvas",
                              "ui_candidates")
        row["origin"] = "Native geometry redraw"
        ui["items"][item["id"]] = row
    (RUN / "ui_regen_report.json").write_text(json.dumps(ui, indent=2) + "\n")
    print(f"Prepared {len(report['items'])} spill/placement and {len(ui['items'])} UI candidates")


if __name__ == "__main__":
    main()
