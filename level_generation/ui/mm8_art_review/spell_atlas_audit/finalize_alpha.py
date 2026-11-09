"""Fit complete retained RGBA spell-master cells to exact 2x review canvases.

The source is each measured raw-sheet slot, never an earlier extracted candidate.
All fits are uniform downscales, shared by the color/sepia pair, with no art crop.
"""

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def magenta_cleanup(image):
    source = ROOT / "level_generation/creatures/mm6_goblin/direct_ai_attack/clean_edges.py"
    spec = importlib.util.spec_from_file_location("spell_magenta_cleanup", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.extract(image.convert("RGB"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remove_isolated_pixels(image):
    pixels = np.asarray(image.convert("RGBA")).copy()
    labels, count = ndimage.label(pixels[:, :, 3] > 12)
    if count:
        sizes = np.bincount(labels.ravel())
        keep = (labels == 0) | (sizes[labels] >= 6)
        pixels[:, :, 3][~keep] = 0
    return Image.fromarray(pixels, "RGBA")


def remove_known_neighbor_fragment(image, name):
    if name[:-1] != "sbdk11":
        return image
    # Both raw sbdk11 cells carry an isolated fragment at y=365–377, more than
    # 55 raw pixels below their lowest original glyph. It belongs to the next row.
    pixels = np.asarray(image.convert("RGBA")).copy()
    pixels[330:, :, 3] = 0
    return Image.fromarray(pixels, "RGBA")


def bounds(image):
    alpha = np.asarray(image.getchannel("A"))
    rows, columns = np.nonzero(alpha > 32)
    if len(rows) == 0:
        raise ValueError("Retained spell master cell is empty")
    return [max(0, int(columns.min()) - 4), max(0, int(rows.min()) - 4),
            min(image.width, int(columns.max()) + 5), min(image.height, int(rows.max()) + 5)]


def main():
    audit = json.loads((HERE / "manifest.json").read_text())
    by_pair = {}
    for entry in audit["items"]:
        if entry["matte_kind"] in {"native alpha", "magenta foreground matte"}:
            by_pair.setdefault(entry["pair"], {})[entry["state"]] = entry
    output = HERE / "alpha_candidates"
    output.mkdir(exist_ok=True)
    results = []
    for pair, states in sorted(by_pair.items()):
        if set(states) != {"a", "b"}:
            raise ValueError(f"Incomplete pair: {pair}")
        panels = {}
        cleanup_stats = {}
        for state, entry in states.items():
            image = Image.open(HERE / entry["slot"])
            if entry["matte_kind"] == "magenta foreground matte":
                image, cleanup_stats[state] = magenta_cleanup(image)
            image = remove_isolated_pixels(image)
            image = remove_known_neighbor_fragment(image, entry["name"])
            box = bounds(image)
            panels[state] = (image.crop(box), box)
        shared_width = max(panel.width for panel, _ in panels.values())
        shared_height = max(panel.height for panel, _ in panels.values())
        target_width = min(states[state]["x2_size"][0] for state in "ab")
        target_height = min(states[state]["x2_size"][1] for state in "ab")
        scale = min(1, (target_width - 4) / shared_width, (target_height - 4) / shared_height)
        for state in "ab":
            entry = states[state]
            panel, box = panels[state]
            size = [round(panel.width * scale), round(panel.height * scale)]
            if min(size) <= 0:
                raise ValueError(f"Invalid scaled size: {pair}{state}")
            fitted = panel.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")
            canvas = Image.new("RGBA", entry["x2_size"])
            offset = [(canvas.width - fitted.width) // 2, (canvas.height - fitted.height) // 2]
            canvas.alpha_composite(fitted, tuple(offset))
            target = output / (entry["id"] + ".png")
            canvas.save(target, optimize=True)
            results.append({"id": entry["id"], "name": entry["name"], "pair": pair, "state": state,
                            "path": "alpha_candidates/" + target.name, "sha256": digest(target),
                            "slot": entry["slot"], "slot_sha256": entry["slot_sha256"],
                            "source_matte": entry["matte_kind"],
                            "magenta_cleanup": cleanup_stats.get(state),
                            "crop": box, "raw_size": list(panel.size), "shared_scale": round(scale, 6),
                            "fitted_size": size, "offset": offset, "x2_size": entry["x2_size"]})
    report = {"schema": 1, "description": "full-master uniform 2x fit; visual review required",
              "states": len(results), "pairs": len(by_pair), "items": results}
    (HERE / "alpha_candidates.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"states": len(results), "pairs": len(by_pair),
                      "smallest_scale": min(row["shared_scale"] for row in results),
                      "no_upscales": all(row["shared_scale"] <= 1 for row in results)}, indent=2))


if __name__ == "__main__":
    main()
