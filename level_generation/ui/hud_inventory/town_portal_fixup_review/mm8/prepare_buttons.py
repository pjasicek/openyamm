#!/usr/bin/env python3
"""Cut MM8 portal destinations from the approved map and derive registered hover light."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OUT = HERE / "buttons_v1"
BASE = HERE / "attempt_03/townport.png"
BASE_SHA = "ea776bd080d2e658278e29e5d33a227044f3663f0eb8767392449342474115b7"
TABLE = ROOT / "assets_dev/engine/data_tables/town_portal_switch.txt"
ARCHIVE = ROOT / "assets_legacy/icons_20260926/engine/icons"
INDEX = ROOT / "level_generation/ui/hud_inventory/accepted_icons.json"
ALIASES = {
    "tpharmndy": "tp_alvar",
    "tpelf": "tp_ravenshore",
    "tpwarlock": "tp_balthazarlair",
    "tpisland": "tp_regna",
    "tpheaven": "tp_shadowspire",
    "tphell": "tp_daggerwoundislands",
}
CENTERS = {
    "tp_alvar": (28, 26, 21, 21),
    "tp_ravenshore": (34, 25, 26, 18),
    "tp_balthazarlair": (31, 36, 22, 26),
    "tp_regna": (39, 28, 28, 19),
    "tp_shadowspire": (44, 31, 30, 22),
    "tp_daggerwoundislands": (37, 29, 23, 21),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(path):
    return str(path.relative_to(HERE))


def artifact(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(path)}


def destinations():
    active = False
    items = []
    for line in TABLE.read_text().splitlines():
        columns = line.split("\t")
        if columns[0] == "@":
            active = columns[1].lower() == "townport"
        elif active and len(columns) >= 14:
            table_name = columns[7]
            name = ALIASES[table_name.lower()]
            with Image.open(ARCHIVE / (name + ".bmp")) as original:
                width, height = original.size
            items.append({
                "id": name, "tableIconName": table_name, "label": columns[13], "mapId": int(columns[1]),
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
    amount = 0.42 * np.exp(-radius * 1.25) + 0.12 * np.exp(-radius * 0.35)
    distance = np.minimum.reduce([xx, yy, crop.width - 1 - xx, crop.height - 1 - yy])
    edge = np.clip((distance - 3) / 10, 0, 1)
    amount *= edge * edge * (3 - 2 * edge)
    mask = np.rint(amount * 255).astype(np.uint8)
    source = np.asarray(crop, dtype=float) / 255
    light = (mask.astype(float) / 255)[..., None] * np.array([1.0, 0.88, 0.55])
    result = np.rint(np.clip(1 - (1 - source) * (1 - light), 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(result), Image.fromarray(mask)


def main():
    if (OUT / "acceptance.json").exists() or (HERE / "acceptance.json").exists():
        raise SystemExit("This revision is accepted; create a new revision before changing its artwork.")
    assert digest(BASE) == BASE_SHA, "Approved background changed"
    index = json.loads(INDEX.read_text())
    for name in CENTERS:
        accepted = index["records"][f"engine--icons--{name}.bmp"]
        if Path(accepted["artifact"]).resolve().is_relative_to(OUT):
            raise SystemExit("The accepted index references these exports; create a new revision.")
    protected = [INDEX, ROOT / "level_generation/ui/hud_inventory/checkpoint/state.json", BASE, TABLE,
                 ROOT / "assets_dev/engine/ui/gameplay/town_portal.yml"]
    protected += [ROOT / "assets_dev/engine/icons_x2" / (name + ".png")
                  for name in ["townport", "antagrich", "tpenroth", *CENTERS]]
    protected_before = {str(path.relative_to(ROOT)): digest(path) for path in protected}
    assert digest(HERE / "attempt_01/inputs/current.png") == index["records"]["engine--icons--townport.bmp"]["sha256"]
    for folder in ["default", "hover", "masks", "original", "installed", "evidence"]:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    base = Image.open(BASE).convert("RGB")
    assert base.size == (1280, 960)
    items = destinations()
    records = []
    for item in items:
        name = item["id"]
        x, y, w, h = (item["rect"][key] for key in ["x", "y", "width", "height"])
        box = (x * 2, y * 2, (x + w) * 2, (y + h) * 2)
        assert 0 <= box[0] < box[2] <= base.width and 0 <= box[1] < box[3] <= base.height
        crop = base.crop(box)
        hover, mask = highlight(crop, CENTERS[name])
        for folder, image in [("default", crop), ("hover", hover), ("masks", mask)]:
            image.save(OUT / folder / (name + ".png"))
        Image.open(ARCHIVE / (name + ".bmp")).convert("RGB").save(OUT / "original" / (name + ".png"))
        runtime = ROOT / "assets_dev/engine/icons_x2" / (name + ".png")
        shutil.copyfile(runtime, OUT / "installed" / (name + ".png"))
        accepted = index["records"][f"engine--icons--{name}.bmp"]
        assert digest(runtime) == accepted["sha256"]
        assert list(crop.size) == accepted["x2_size"]
        pixels = np.asarray(crop)
        delta = np.any(np.asarray(hover) != pixels, axis=2)
        assert np.array_equal(pixels, np.asarray(base)[box[1]:box[3], box[0]:box[2]])
        assert not delta[:4].any() and not delta[-4:].any()
        assert not delta[:, :4].any() and not delta[:, -4:].any()
        assert not np.any(delta & (np.asarray(mask) == 0)) and delta.any()
        restored = base.copy()
        restored.paste(hover, box[:2])
        restored.paste(crop, box[:2])
        assert np.array_equal(np.asarray(restored), np.asarray(base))
        for folder in ["default", "hover", "original", "installed"]:
            item[folder] = local(OUT / folder / (name + ".png"))
        records.append({
            **item, "target": f"engine--icons--{name}.bmp", "cropBoxX2": list(box),
            "previousAcceptance": accepted, "originalSource": artifact(ARCHIVE / (name + ".bmp")),
            "exports": {folder: artifact(OUT / folder / (name + ".png"))
                        for folder in ["default", "hover", "masks", "original", "installed"]},
            "maskCenterRadiiNative": list(CENTERS[name]), "changedPixels": int(delta.sum()),
            "validation": {"exactMapCrop": True, "nativePlacementAndSize": True,
                           "unchangedFourPixelBorder": True, "changeConfinedToMask": True,
                           "opaqueRgb": True, "noGeometricTransform": True, "exactReset": True},
        })
    unchanged = {path: digest(ROOT / path) == sha for path, sha in protected_before.items()}
    assert all(unchanged.values())
    data = {
        "logicalSize": [640, 480], "destinations": items,
        "versions": {
            "candidate": {"background": local(BASE), "hoverKey": "hover",
                          "label": "Corrected map + matching buttons"},
            "previous": {"background": "attempt_01/townport.png", "hoverKey": None,
                         "label": "Before corrections"},
            "reference": {"background": "attempt_01/inputs/colored_reference.png", "hoverKey": None,
                          "label": "2063 color reference", "fit": "contain"},
            "current": {"background": "attempt_01/inputs/current.png", "hoverKey": "installed",
                        "label": "Current installation"},
            "original": {"background": "attempt_01/inputs/original.png", "hoverKey": "original",
                         "label": "Original game artwork"},
        },
    }
    (HERE / "data.js").write_text("window.MM8_TOWN_PORTAL_REVIEW = " + json.dumps(data, indent=2) + ";\n")
    manifest = {
        "schema": 1, "status": "review_candidate", "accepted": False, "installed": False,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "background": artifact(BASE),
        "backgroundUserApproval": "OK good, now create the town portal buttons",
        "placementSource": artifact(TABLE), "layoutSource": artifact(protected[4]),
        "recipeSource": artifact(Path(__file__).resolve()),
        "aliasSource": artifact(ROOT / "game/ui/GameplayUiRuntime.cpp"),
        "referenceRecipe": artifact(HERE.parent / "mm7/prepare_buttons.py"),
        "recipe": {"operation": "Warm screen blend in a feathered landmark-centered mask",
                   "coreStrength": 0.42, "coreFalloff": 1.25, "haloStrength": 0.12, "haloFalloff": 0.35,
                   "screenColor": [1, 0.88, 0.55], "unchangedEdgePixels": 4,
                   "edgeFeatherPixels": 10, "maskQuantization": "8-bit rounded",
                   "generationUsed": False, "placementChanges": False, "resizingOrRepositioning": False},
        "records": records, "protectedBefore": protected_before,
        "validation": {"result": "PASS", "destinations": len(records), "exactMapCrops": True,
                       "identicalStateGeometry": True, "seamlessBorders": True,
                       "allOriginalPlacementsAndCanvasesPreserved": True, "protectedFilesUnchanged": unchanged},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    proof = Image.new("RGB", (1140, 1160), (27, 31, 36))
    draw = ImageDraw.Draw(proof)
    for col, heading in enumerate(["Original hover", "Exact map crop", "New hover", "Light mask"]):
        draw.text((245 + col * 220, 10), heading, fill=(239, 226, 199), font=font)
    for row, item in enumerate(items):
        y = 45 + row * 182
        draw.text((12, y + 12), item["label"], fill=(239, 226, 199), font=font)
        for col, folder in enumerate(["original", "default", "hover", "masks"]):
            patch = Image.open(OUT / folder / (item["id"] + ".png")).convert("RGB")
            if folder == "original":
                patch = patch.resize((patch.width * 2, patch.height * 2), Image.Resampling.NEAREST)
            proof.paste(patch, (245 + col * 220, y))
    proof.save(OUT / "evidence/buttons.png")
    for path in OUT.rglob("*.png"):
        path.chmod(0o644)
    summary = {"result": "PASS", "destinations": len(items), "protectedFilesUnchanged": len(unchanged)}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
