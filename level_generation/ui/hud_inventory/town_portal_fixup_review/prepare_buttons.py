#!/usr/bin/env python3
"""Derive registered MM6 Town Portal hover patches from the approved map pixels."""

import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / "mm6/buttons_v1"
BASE = HERE / "mm6/creature_fixup_v3/tpenroth.png"
TABLE = ROOT / "assets_dev/engine/data_tables/town_portal_switch.txt"
ARCHIVE = ROOT / "assets_legacy/icons_20260926/engine/icons"
CENTERS = {
    "tpblckshr": (40, 21, 14, 11),
    "tpfrhvn": (40, 31, 12, 10),
    "tpmist": (48, 29, 18, 14),
    "tpsorpig": (60, 36, 17, 12),
    "tpslvrcv": (44, 23, 11, 10),
    "tpwhtc": (45, 23, 18, 10),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(path):
    return str(path.relative_to(HERE))


def read_destinations():
    active = False
    items = []
    for line in TABLE.read_text().splitlines():
        columns = line.split("\t")
        if columns[0] == "@":
            active = columns[1].lower() == "tpenroth"
        elif active and len(columns) >= 14:
            name = columns[7].lower()
            with Image.open(ARCHIVE / (name + ".bmp")) as original:
                width, height = original.size
            items.append({
                "id": name, "label": columns[13], "mapId": int(columns[1]),
                "rect": {"x": int(columns[8]), "y": int(columns[9]),
                         "width": int(columns[10]) if columns[10] else width,
                         "height": int(columns[11]) if columns[11] else height},
                "sourceSize": [width, height],
            })
    assert {item["id"] for item in items} == set(CENTERS)
    return items


def highlight(crop, center):
    cx, cy, rx, ry = np.array(center, dtype=float) * 2
    yy, xx = np.mgrid[:crop.height, :crop.width]
    radius = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
    # Two continuous fields give the settlement a brighter core and a gentle surrounding glow.
    amount = 0.42 * np.exp(-radius * 1.25) + 0.12 * np.exp(-radius * 0.35)
    distance = np.minimum.reduce([xx, yy, crop.width - 1 - xx, crop.height - 1 - yy])
    edge = np.clip((distance - 3) / 10, 0, 1)
    amount *= edge * edge * (3 - 2 * edge)
    mask = np.rint(amount * 255).astype(np.uint8)
    source = np.asarray(crop, dtype=float) / 255
    warm_light = np.array([1.0, 0.88, 0.55])
    light = (mask.astype(float) / 255)[..., None] * warm_light
    result = 1 - (1 - source) * (1 - light)
    result = np.rint(np.clip(result, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(result), Image.fromarray(mask)


def main():
    if (HERE.parent / "town_portal_acceptance_20260927/accepted.json").exists():
        raise SystemExit("This revision is accepted; create a new revision before preparing new artwork.")
    for folder in ["default", "hover", "masks", "original", "installed", "evidence"]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    base = Image.open(BASE).convert("RGB")
    assert base.size == (1280, 960)
    native_map = Image.open(ARCHIVE / "tpenroth.bmp").convert("RGB")
    installed_index = json.loads((ROOT / "level_generation/ui/hud_inventory/accepted_icons.json").read_text())
    destinations = read_destinations()
    records = []
    for item in destinations:
        name = item["id"]
        r = item["rect"]
        x, y, w, h = (r[key] for key in ["x", "y", "width", "height"])
        box = (x * 2, y * 2, (x + w) * 2, (y + h) * 2)
        crop = base.crop(box)
        hover, mask = highlight(crop, CENTERS[name])
        crop.save(OUT / "default" / (name + ".png"))
        hover.save(OUT / "hover" / (name + ".png"))
        mask.save(OUT / "masks" / (name + ".png"))
        original = Image.open(ARCHIVE / (name + ".bmp")).convert("RGB")
        original.save(OUT / "original" / (name + ".png"))
        installed = ROOT / "assets_dev/engine/icons_x2" / (name + ".png")
        shutil.copyfile(installed, OUT / "installed" / (name + ".png"))
        accepted = installed_index["records"][f"engine--icons--{name}.bmp"]
        assert digest(installed) == accepted["sha256"]
        assert list(crop.size) == accepted["x2_size"]
        pixels = np.asarray(crop)
        delta = np.any(np.asarray(hover) != pixels, axis=2)
        assert np.array_equal(pixels, np.asarray(base)[box[1]:box[3], box[0]:box[2]])
        assert not delta[:4].any() and not delta[-4:].any()
        assert not delta[:, :4].any() and not delta[:, -4:].any()
        assert not np.any(delta & (np.asarray(mask) == 0))
        assert delta.any()
        item.update({
            "default": local(OUT / "default" / (name + ".png")),
            "hover": local(OUT / "hover" / (name + ".png")),
            "original": local(OUT / "original" / (name + ".png")),
            "installed": local(OUT / "installed" / (name + ".png")),
            "cityCenter": list(CENTERS[name][:2]),
        })
        records.append({
            **item, "target": f"engine--icons--{name}.bmp", "cropBoxX2": list(box),
            "previousAcceptance": accepted,
            "originalSha256": digest(ARCHIVE / (name + ".bmp")),
            "defaultSha256": digest(OUT / "default" / (name + ".png")),
            "hoverSha256": digest(OUT / "hover" / (name + ".png")),
            "maskSha256": digest(OUT / "masks" / (name + ".png")),
            "maskCenterRadiiNative": list(CENTERS[name]), "changedPixels": int(delta.sum()),
            "validation": {"exactMapCrop": True, "nativePlacementAndSize": True,
                           "unchangedFourPixelBorder": True, "changeConfinedToMask": True,
                           "sameOpaqueCanvas": True, "noGeometricTransform": True},
        })

    data = {
        "background": local(BASE), "backgroundSha256": digest(BASE),
        "logicalSize": [640, 480], "destinations": destinations,
        "versions": {
            "candidate": {"background": local(BASE), "hoverKey": "hover", "label": "Revised map + matching hover"},
            "previous": {"background": "mm6/creature_fixup_v2/tpenroth.png", "hoverKey": "hover",
                         "label": "Before terrain repair"},
            "installed": {"background": "mm6/attempt_01/inputs/previous.png", "hoverKey": "installed",
                          "label": "Previously installed map and buttons"},
            "original": {"background": "mm6/attempt_01/inputs/original.png", "hoverKey": "original",
                         "label": "Original map and buttons"},
        },
    }
    (HERE / "data.js").write_text("window.TOWN_PORTAL_REVIEW = " + json.dumps(data, indent=2) + ";\n")
    manifest = {
        "schema": 1, "status": "review_candidate", "accepted": False, "installed": False,
        "background": {"path": str(BASE.relative_to(ROOT)), "sha256": digest(BASE)},
        "placementSource": {"path": str(TABLE.relative_to(ROOT)), "sha256": digest(TABLE)},
        "recipe": {"operation": "Warm screen blend in a feathered settlement-centered mask",
                   "coreStrength": 0.42, "haloStrength": 0.12, "screenColor": [1, 0.88, 0.55],
                   "unchangedEdgePixels": 4, "generationUsed": False,
                   "placementChanges": False, "resizingOrRepositioning": False},
        "records": records,
        "validation": {"result": "PASS", "destinations": len(records), "exactMapCrops": True,
                       "identicalStateGeometry": True, "seamlessBorders": True,
                       "allOriginalPlacementsAndCanvasesPreserved": True},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    proof = Image.new("RGB", (1160, 1130), (27, 31, 36))
    draw = ImageDraw.Draw(proof)
    for col, heading in enumerate(["Original hover", "Exact new map crop", "Derived hover"]):
        draw.text((185 + col * 320, 10), heading, fill=(239, 226, 199), font=font)
    for row, item in enumerate(destinations):
        name = item["id"]
        y = 45 + row * 178
        draw.text((12, y + 12), item["label"], fill=(239, 226, 199), font=font)
        for col, folder in enumerate(["original", "default", "hover"]):
            patch = Image.open(OUT / folder / (name + ".png"))
            if folder == "original":
                patch = patch.resize((patch.width * 2, patch.height * 2), Image.Resampling.NEAREST)
            proof.paste(patch, (185 + col * 320, y))
    proof.save(OUT / "evidence/buttons.png")
    print(json.dumps(manifest["validation"], indent=2))


if __name__ == "__main__":
    main()
