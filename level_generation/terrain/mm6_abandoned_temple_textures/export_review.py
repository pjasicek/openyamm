"""Export this study's selected images and assemble review proofs; no production writes."""

import hashlib
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


base = Path(__file__).resolve().parent
manifest = json.loads((base / "full_manifest.json").read_text())
jobs = {job["name"]: job for job in json.loads((base / "full_jobs.json").read_text())}
metrics = {}


def strip_bounds(source, horizontal):
    """Crop real alpha padding; generated material interiors can have alpha 251–254."""
    alpha = np.asarray(source)[:, :, 3]
    assert alpha.min() == 0 and alpha.max() >= 250, "Real PNG alpha required"
    material = alpha >= 240
    bounds = Image.fromarray(material).getbbox()
    assert bounds, "Empty texture"
    left, top, right, bottom = bounds
    # A bevel or antialiased end must not force transparent padding into a wall texture.
    for inset in range(max(1, max(source.size) // 100) + 1):
        rect = (left + inset, top, right - inset, bottom) if horizontal else (
            left, top + inset, right, bottom - inset)
        view = material[rect[1]:rect[3], rect[0]:rect[2]]
        bands = np.flatnonzero(view.all(axis=1 if horizontal else 0))
        if len(bands) and len(bands) == bands[-1] - bands[0] + 1:
            crop = (rect[0], rect[1] + int(bands[0]), rect[2], rect[1] + int(bands[-1]) + 1) if horizontal else (
                rect[0] + int(bands[0]), rect[1], rect[0] + int(bands[-1]) + 1, rect[3])
            assert material[crop[1]:crop[3], crop[0]:crop[2]].all(), "Padding remains"
            return list(crop)
    raise AssertionError("No rectangular material strip without transparent holes")


def panel_bounds(source):
    """Keep the complete rectangular colour plane, including dark keyholes with source alpha."""
    mask = np.asarray(source)[:, :, 3] >= 240
    bounds = Image.fromarray(mask).getbbox()
    assert bounds, "Empty panel"
    left, top, right, bottom = bounds
    view = mask[top:bottom, left:right]
    rows = np.flatnonzero(view.mean(axis=1) >= 0.95)
    columns = np.flatnonzero(view.mean(axis=0) >= 0.95)
    assert len(rows) and len(columns), "Missing rectangular panel footprint"
    return [left + int(columns[0]), top + int(rows[0]),
            left + int(columns[-1]) + 1, top + int(rows[-1]) + 1]


# Both strip orientations, nearly opaque generated interiors and transparent padding.
check = Image.new("RGBA", (40, 20))
check.paste((80, 60, 40, 253), (0, 5, 40, 15))
assert strip_bounds(check, True) == [0, 5, 40, 15]
assert strip_bounds(check.transpose(Image.Transpose.ROTATE_90), False) == [5, 0, 15, 40]
check.putpixel((0, 7), (80, 60, 40, 0))
assert strip_bounds(check, True) == [1, 5, 39, 15]
panel = Image.new("RGBA", (60, 60))
panel.paste((80, 60, 40, 253), (5, 5, 55, 55))
panel.putpixel((30, 30), (0, 0, 0, 0))
assert panel_bounds(panel) == [5, 5, 55, 55]
try:
    strip_bounds(Image.new("RGBA", (40, 20), (80, 60, 40, 255)), True)
except AssertionError:
    pass
else:
    raise AssertionError("Opaque fake padding accepted")

for texture in manifest["textures"]:
    name = texture["name"]
    raw = base / texture.get("selected", "generated/" + name + "_full_v1.png")
    if name in jobs and raw.exists():
        source = Image.open(raw).convert("RGBA")
        crop = None
        if jobs[name]["padding"] or "master_region" in texture:
            alpha = np.asarray(source)[:, :, 3]
            assert alpha.min() == 0 and alpha.max() >= 250, (name, "Real PNG alpha required")
            texture["source_alpha"] = dict(extrema=[int(alpha.min()), int(alpha.max())],
                                           transparent_pixels=int((alpha == 0).sum()),
                                           near_opaque_pixels=int((alpha >= 240).sum()))
            horizontal = texture.get("master_strip_horizontal",
                                     texture["native_size"][0] > texture["native_size"][1])
            crop = panel_bounds(source) if "master_region" in texture else strip_bounds(source, horizontal)
            if "master_region" in texture:
                left, top, right, bottom = texture["master_region"]
                x, y, width, height = crop[0], crop[1], crop[2] - crop[0], crop[3] - crop[1]
                crop = [x + round(left * width), y + round(top * height),
                        x + round(right * width), y + round(bottom * height)]
            source = source.crop(crop)
        if texture.get("master_rotation", 0) == 90:
            source = source.transpose(Image.Transpose.ROTATE_90)
        source = source.convert("RGB").convert("RGBA")
        assert all(a >= b for a, b in zip(source.size, texture["runtime_size"])), (name, "Upscaling forbidden")
        source.resize(tuple(texture["runtime_size"]), Image.Resampling.LANCZOS).save(
            base / "runtime" / (name + ".png"))
        texture.update(status="generated", selected=str(raw.relative_to(base)), crop=crop)
        texture.setdefault("prompt", "prompts/" + name + "_full_v1.txt")
    candidate = base / "runtime" / (name + ".png")
    if not candidate.exists():
        continue
    assert Image.open(candidate).size == tuple(texture["runtime_size"]), name
    assert Image.open(candidate).convert("RGBA").getchannel("A").getextrema() == (255, 255), name
    texture["runtime_sha256"] = hashlib.sha256(candidate.read_bytes()).hexdigest()
    metrics[name] = {}
    for mode, path in [("native", base / "references" / (name + "_native.png")),
                       ("before", base / "references" / (name + "_before.png")), ("after", candidate)]:
        image = Image.open(path).convert("RGB").resize(tuple(texture["runtime_size"]),
                                                       Image.Resampling.NEAREST)
        values = np.asarray(image, dtype=np.float32)
        wrap = [float(np.abs(values[:, 0] - values[:, -1]).mean()),
                float(np.abs(values[0] - values[-1]).mean())]
        internal = [float(np.abs(np.diff(values, axis=1)).mean()),
                    float(np.abs(np.diff(values, axis=0)).mean())]
        metrics[name][mode] = dict(wrap_rgb=wrap, internal_rgb=internal,
                                  ratio=[a / max(b, 0.001) for a, b in zip(wrap, internal)])
        repeat = Image.new("RGB", (image.width * 3, image.height * 3))
        for y in range(3):
            for x in range(3):
                repeat.paste(image, (image.width * x, image.height * y))
        repeat.thumbnail((1100, 1100), Image.Resampling.LANCZOS)
        repeat.save(base / "review" / (name + "_" + mode + "_repeat.png"))

for page in range(3):
    contact = Image.new("RGB", (1820, 960), (30, 30, 30))
    draw = ImageDraw.Draw(contact)
    for i, texture in enumerate(manifest["textures"][page * 21:(page + 1) * 21]):
        path = base / "runtime" / (texture["name"] + ".png")
        if not path.exists():
            continue
        image = Image.open(path)
        image.thumbnail((240, 280))
        x, y = i % 7 * 260, i // 7 * 320
        contact.paste(image, (x + (260 - image.width) // 2, y + 28))
        draw.text((x + 6, y + 6), texture["name"], fill="white")
    contact.save(base / "review" / ("full_after_" + str(page + 1) + ".png"))

(base / "full_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
(base / "review/full_seam_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
viewer = base / "review/index.html"
entries = [dict(name=t["name"], selected=t["selected"], prompt=t["prompt"],
                continuity=jobs[t["name"]]["continuity"] if t["name"] in jobs else "both axes")
           for t in manifest["textures"]]
html, replaced = re.subn(r"^const textures=.*;$", "const textures=" + json.dumps(entries) + ";",
                        viewer.read_text(), flags=re.MULTILINE)
assert replaced == 1, "Viewer selection registry missing"
viewer.write_text(html)
print("Exported and reviewed", len(metrics), "of", manifest["count"], "textures")
