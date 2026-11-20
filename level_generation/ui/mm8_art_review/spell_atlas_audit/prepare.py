"""Recrop retained spell masters at measured sheet gutters for visual audit.

The output is full-resolution raw artwork. It does not resize, matte, or approve it.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = HERE.parents[3]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def web_path(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def catalog():
    return json.loads((REVIEW / "catalog.js").read_text().split("=", 1)[1].rstrip(" ;\n"))


def load_layout(raw, members):
    if raw.parent.name.startswith("pair_sheet_"):
        layout_path = raw.parent / "layout.json"
        layout = json.loads(layout_path.read_text())
        rects = {entry["id"]: entry["reference_rect"] for entry in layout["cells"]}
    else:
        layout_path = raw.parent / "payload.json"
        layout = json.loads(layout_path.read_text())["execution_layout"]
        rects = layout["cell_rects"]
    return layout_path, {member["id"]: rects[member["id"]] for member in members}


def occupancy(raw):
    rgba = np.asarray(raw.convert("RGBA"))
    if "A" in raw.getbands() and raw.getchannel("A").getextrema()[0] == 0:
        return rgba[:, :, 3] > 128, "native alpha"
    rgb = rgba[:, :, :3].astype(int)
    corner = rgb[0, 0]
    if corner[0] > 165 and corner[2] > 150 and corner[1] < 100:
        magenta = (rgb[:, :, 0] > 165) & (rgb[:, :, 2] > 145) & (rgb[:, :, 1] < 115)
        visible = ~magenta
        kind = "magenta foreground matte" if visible.mean() < 0.5 else "magenta matte and paper"
        return visible, kind
    luminance = (rgb[:, :, 0] * 3 + rgb[:, :, 1] * 6 + rgb[:, :, 2]) / 10
    return luminance > 65, "dark gutter and paper"


def split_axis(occupied, count, axis):
    extent = occupied.shape[1 if axis == "x" else 0]
    if count == 1:
        return [0, extent], []
    projection = occupied.mean(axis=0 if axis == "x" else 1)
    projection = ndimage.gaussian_filter1d(projection, 3)
    pitch = extent / count
    bounds = [0]
    measurements = []
    for index in range(1, count):
        expected = index * pitch
        low = max(bounds[-1] + 8, round(expected - pitch * 0.38))
        high = min(extent - 8, round(expected + pitch * 0.38))
        if low >= high:
            raise ValueError(f"Unable to search {axis} split {index}/{count}")
        positions = np.arange(low, high)
        penalty = 0.02 * np.abs(positions - expected) / pitch
        position = int(positions[np.argmin(projection[low:high] + penalty)])
        bounds.append(position)
        measurements.append({"position": position, "expected": round(expected, 2),
                             "occupied_fraction": round(float(projection[position]), 4)})
    bounds.append(extent)
    return bounds, measurements


def isolate_paper_panel(cut):
    rgb = np.asarray(cut.convert("RGB"))
    paper = ~((rgb[:, :, 0] > 165) & (rgb[:, :, 2] > 145) & (rgb[:, :, 1] < 115))
    labels, count = ndimage.label(paper)
    if count == 0:
        raise ValueError("Magenta-backed cell has no paper panel")
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    panel = labels == int(np.argmax(sizes))
    rows, columns = np.nonzero(panel)
    panel_box = [max(0, int(columns.min()) - 2), max(0, int(rows.min()) - 2),
                 min(cut.width, int(columns.max()) + 3), min(cut.height, int(rows.max()) + 3)]
    return cut.crop(panel_box), panel_box


def main():
    items = [item for item in catalog()["items"] if item["category"] == "Spell icons"]
    groups = {}
    for item in items:
        candidate = item["candidates"][0] if item["candidates"] else {}
        if candidate.get("raw"):
            raw = (REVIEW / candidate["raw"]).resolve()
            groups.setdefault(raw, []).append(item)
    slots = HERE / "slots"
    slots.mkdir(parents=True, exist_ok=True)
    entries = []
    sheets = []
    for raw_path, members in sorted(groups.items()):
        layout_path, rects = load_layout(raw_path, members)
        xs = sorted({rect[0] for rect in rects.values()})
        ys = sorted({rect[1] for rect in rects.values()})
        with Image.open(raw_path) as raw:
            occupied, matte_kind = occupancy(raw)
            x_bounds, x_measures = split_axis(occupied, len(xs), "x")
            y_bounds, y_measures = split_axis(occupied, len(ys), "y")
            for item in members:
                rect = rects[item["id"]]
                col, row = xs.index(rect[0]), ys.index(rect[1])
                box = [x_bounds[col], y_bounds[row], x_bounds[col + 1], y_bounds[row + 1]]
                cut = raw.crop(box)
                panel_box = None
                if matte_kind == "magenta matte and paper":
                    cut, panel_box = isolate_paper_panel(cut)
                destination = slots / (item["id"] + ".png")
                cut.save(destination, optimize=True)
                native_width, native_height = item["native_size"]
                entry = {
                    "id": item["id"], "name": item["name"], "pair": item["name"][:-1],
                    "state": item["name"][-1], "native_size": item["native_size"],
                    "x2_size": item["x2_size"], "original": "../" + item["original"],
                    "previous": "../" + item["candidates"][0]["path"],
                    "slot": "slots/" + destination.name, "slot_sha256": digest(destination),
                    "source_sha256": item["source_sha256"], "raw": web_path(raw_path),
                    "raw_sha256": digest(raw_path), "layout": web_path(layout_path),
                    "box": box, "row": row, "column": col,
                    "panel_box": panel_box,
                    "sampling_x": round(cut.width / native_width, 3),
                    "sampling_y": round(cut.height / native_height, 3),
                    "matte_kind": matte_kind,
                }
                entries.append(entry)
        sheets.append({"raw": web_path(raw_path), "raw_sha256": digest(raw_path),
                       "layout": web_path(layout_path), "size": list(raw.size),
                       "columns": len(xs), "rows": len(ys), "matte_kind": matte_kind,
                       "x_bounds": x_bounds, "y_bounds": y_bounds,
                       "x_splits": x_measures, "y_splits": y_measures})
    result = {"schema": 1, "description": "measured full-resolution raw spell sheet slots; no resizing or approval",
              "summary": {"raw_sheets": len(sheets), "states": len(entries),
                          "pairs": len({entry["pair"] for entry in entries}),
                          "below_2x_slot": sum(min(entry["sampling_x"], entry["sampling_y"]) < 2 for entry in entries)},
              "sheets": sheets, "items": sorted(entries, key=lambda entry: entry["name"])}
    (HERE / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "manifest.js").write_text("window.SPELL_ATLAS_AUDIT = " + json.dumps(result, separators=(",", ":")) + ";\n")
    print(json.dumps(result["summary"], indent=2))
    for sheet in sheets:
        weak = [m for m in sheet["x_splits"] + sheet["y_splits"] if m["occupied_fraction"] > 0.05]
        if weak:
            print("Weak gutter", sheet["raw"], weak)


if __name__ == "__main__":
    main()
