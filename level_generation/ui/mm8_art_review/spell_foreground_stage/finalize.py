"""Register transparent 2x spell foreground previews for visual review only."""

import hashlib
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = HERE.parents[3]
HUD = ROOT / "level_generation/ui/hud_inventory"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def web_path(path):
    return Path(os.path.relpath(path, HERE)).as_posix()


def resize_alpha(image, size):
    return image.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def gap_position(projection, lo, hi):
    """Locate the transparent gutter between generated rows or columns."""
    smoothed = ndimage.uniform_filter1d(projection.astype(float), size=25)
    center = len(projection) / 2
    choices = np.arange(lo, hi)
    best = min(choices, key=lambda value: (smoothed[value], abs(value - center)))
    return int(best)


def visible_bounds(image):
    alpha = np.asarray(image.getchannel("A"))
    ys, xs = np.nonzero(alpha > 128)
    if not len(xs):
        raise ValueError("Generated spell cell is empty")
    padding = max(4, round(min(image.size) * 0.012))
    return (max(0, int(xs.min()) - padding), max(0, int(ys.min()) - padding),
            min(image.width, int(xs.max()) + 1 + padding),
            min(image.height, int(ys.max()) + 1 + padding))


def extract_batch(number):
    directory = HERE / "batches" / f"{number:02d}"
    layout_path = directory / "layout.json"
    layout = json.loads(layout_path.read_text())
    reference = directory / "reference.png"
    raw_path = directory / "raw.png"
    prompt_path = directory / "prompt.txt"
    if digest(reference) != layout["reference_sha256"]:
        raise ValueError(f"Reference changed: {reference}")
    raw = Image.open(raw_path).convert("RGBA")
    if raw.getextrema()[3] != (0, 255):
        raise ValueError(f"Raw sheet lacks genuine alpha: {raw_path}")
    sx = raw.width / layout["reference_size"][0]
    sy = raw.height / layout["reference_size"][1]
    if abs(sx / sy - 1) > 0.015:
        raise ValueError(f"Sheet changed aspect ratio: {raw_path}")
    alpha = np.asarray(raw.getchannel("A")) > 16
    split_x = gap_position(alpha.sum(axis=0), round(raw.width * 0.4), round(raw.width * 0.6))
    split_y = (gap_position(alpha.sum(axis=1), round(raw.height * 0.35), round(raw.height * 0.65))
               if len(layout["pairs"]) == 2 else raw.height)
    panels = []
    for index, cell in enumerate(layout["cells"]):
        x0, x1 = (0, split_x) if index % 2 == 0 else (split_x, raw.width)
        y0, y1 = (0, split_y) if index // 2 == 0 else (split_y, raw.height)
        panel = raw.crop((x0, y0, x1, y1))
        panels.append((panel, visible_bounds(panel), cell))
    result = {}
    for index, (panel, bounds, cell) in enumerate(panels):
        other_bounds = panels[index + 1 if index % 2 == 0 else index - 1][1]
        union_width = max(bounds[2] - bounds[0], other_bounds[2] - other_bounds[0])
        union_height = max(bounds[3] - bounds[1], other_bounds[3] - other_bounds[1])
        target_width, target_height = cell["x2_size"]
        scale = min((target_width - 4) / union_width, (target_height - 4) / union_height)
        cut = panel.crop(bounds)
        size = (max(1, round(cut.width * scale)), max(1, round(cut.height * scale)))
        fitted = resize_alpha(cut, size)
        preview = Image.new("RGBA", (target_width, target_height))
        offset = ((target_width - fitted.width) // 2, (target_height - fitted.height) // 2)
        preview.alpha_composite(fitted, offset)
        output = HERE / "candidates" / f"{cell['id']}.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        preview.save(output, optimize=True)
        result[cell["id"]] = {
            "path": output, "kind": "new transparent sheet edit", "batch": number,
            "raw": raw_path, "raw_sha256": digest(raw_path), "crop": list(bounds),
            "prompt": prompt_path, "prompt_sha256": digest(prompt_path),
            "split": [split_x, split_y], "fitted_size": list(size), "fitted_offset": list(offset),
            "reference_sha256": layout["reference_sha256"],
            "parent_sha256": cell["current_sha256"],
        }
    return result


def air_ink(item, state):
    record = state["cells"].get(item["id"], {})
    if record.get("status") != "accepted":
        return None
    registration = record.get("review", {}).get("registration_record")
    if not registration:
        return None
    path = Path(registration).parent.parent / f"{item['name']}-ink.png"
    if not path.is_file():
        return None
    if Image.open(path).size != tuple(item["x2_size"]):
        return None
    return {"path": path, "kind": "existing accepted Air ink", "parent_sha256": record["sha256"]}


def alpha_stats(path):
    pixels = np.asarray(Image.open(path).convert("RGBA"))
    alpha = pixels[:, :, 3]
    opaque = alpha > 240
    red, green, blue = (pixels[:, :, channel].astype(int) for channel in range(3))
    paper = opaque & (red > 160) & (green > 130) & (blue > 80) & (red > green + 7) & (green > blue + 5)
    magenta = (alpha > 32) & (red > 170) & (blue > 110) & (green < 110) & (red > green * 1.6) & (blue > green * 1.4)
    return {"transparent_fraction": round(float(np.mean(alpha < 16)), 4),
            "opaque_fraction": round(float(np.mean(opaque)), 4),
            "paper_color_fraction": round(float(np.mean(paper)), 4),
            "magenta_pixel_count": int(np.count_nonzero(magenta))}


def main():
    catalog = json.loads((REVIEW / "catalog.js").read_text().split("=", 1)[1].rstrip(" ;\n"))
    items = sorted((row for row in catalog["items"] if row["category"] == "Spell icons"), key=lambda x: x["name"])
    state = json.loads((HUD / "checkpoint/state.json").read_text())
    batches = json.loads((HERE / "batches.json").read_text())["batches"]
    generated = {}
    for batch in batches:
        generated.update(extract_batch(batch["batch"]))
    entries = []
    for item in items:
        current = (REVIEW / item["candidates"][0]["path"]).resolve()
        selected = generated.get(item["id"])
        if selected is None and item["name"].startswith("sba"):
            selected = air_ink(item, state)
        if selected is None:
            selected = {"path": current, "kind": "retained transparent candidate",
                        "parent_sha256": digest(current)}
        path = selected["path"]
        if not path.is_file() or Image.open(path).size != tuple(item["x2_size"]):
            raise ValueError(f"Missing or wrong-sized stage candidate: {item['id']}")
        entries.append({
            "id": item["id"], "name": item["name"], "pair": item["name"][:-1],
            "state": item["name"][-1], "x2_size": item["x2_size"], "native_size": item["native_size"],
            "source_sha256": item["source_sha256"], "original": web_path(REVIEW / item["original"]),
            "current": web_path(current), "current_sha256": digest(current),
            "candidate": web_path(path), "candidate_sha256": digest(path),
            "kind": selected["kind"], "batch": selected.get("batch"),
            "raw": web_path(selected["raw"]) if selected.get("raw") else None,
            "raw_sha256": selected.get("raw_sha256"), "crop": selected.get("crop"),
            "prompt": web_path(selected["prompt"]) if selected.get("prompt") else None,
            "prompt_sha256": selected.get("prompt_sha256"),
            "parent_sha256": selected["parent_sha256"], "alpha": alpha_stats(path),
        })
    if len(entries) != 222 or len({entry["id"] for entry in entries}) != 222:
        raise ValueError("Spell stage must contain every paired state once")
    result = {"schema": 1, "stage": "transparent spell foregrounds", "items": entries,
              "summary": {"states": len(entries), "pairs": len(entries) // 2,
                          "new_sheet_edits": sum(entry["kind"] == "new transparent sheet edit" for entry in entries),
                          "accepted_air_ink": sum(entry["kind"] == "existing accepted Air ink" for entry in entries),
                          "retained": sum(entry["kind"] == "retained transparent candidate" for entry in entries)}}
    (HERE / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "manifest.js").write_text("window.SPELL_STAGE = " + json.dumps(result, separators=(",", ":")) + ";\n")
    print(json.dumps(result["summary"], indent=2))
    for entry in entries:
        if entry["kind"] == "retained transparent candidate" and entry["alpha"]["opaque_fraction"] > 0.8:
            print("Opaque retained:", entry["name"], entry["alpha"])


if __name__ == "__main__":
    main()
