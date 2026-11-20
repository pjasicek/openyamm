#!/usr/bin/env python3
"""
The 2026-10-31 measurement of the user's real MM9 screenshots against our current bakes (no lighting changed):
per real shot, our capture at the same view (each map's make_real_tour.py, desktop run at unlimited view distance),
both measured by real_shots.py (same view box, thirds, extra boxes), joined with MM9's own prediction of the view
(real_context.py: DAT texture x DAT lightmap x1, the lights near the eye, WorldInfo). Writes
devdocs/mm9_rework/overnight/real_mm9/measurements/measurements.json and the sheets <map>_real_vs_ours.jpg (real | ours
| alternatives) next to the shots. Read only towards the maps.

    python3 level_generation/projects/mm9r_common/real_measure.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from real_shots import REAL_DIR, ROOT, stats  # noqa: E402

PROJECTS = ROOT / "level_generation/projects"
OUT = REAL_DIR / "measurements"
TILE = (520, 300)

# real shot -> (map, our capture folder, shot name, [alternative shot names], extra real-frame boxes, context tour shot)
SHOTS = [
    ("yanmirsfort_real_1.png", "yanmirsfort", "real01_baked", "y1_great_hall_south", ["y1_alt_west", "y1_alt_east"],
     {}),
    ("yanmirsfort_real_2.png", "yanmirsfort", "real01_baked", "y2_great_hall_southwest",
     ["y2_alt_northeast", "y2_alt_east"], {}),
    ("dungeonofsecrets_real_1_corridor.png", "dungeonofsecrets", "real02_baked", "d1_west_corridor", ["d1_alt_back"],
     {"far_end": (0.33, 0.54, 0.33, 0.63), "near_walls": (0.20, 0.30, 0.05, 0.88)}),
    ("dungeonofsecrets_real_2_purple_room.png", "dungeonofsecrets", "real02_baked", "d2_pool_room_w", ["d2_alt_south"],
     {"banners": (0.20, 0.78, 0.05, 0.30), "passage": (0.45, 0.54, 0.35, 0.55), "water": (0.20, 0.78, 0.60, 0.88)}),
    ("dungeonofsecrets_real_3_doorway.png", "dungeonofsecrets", "real03d3a_baked", "d3a_hub_door_s10", [],
     {"doorway": (0.34, 0.68, 0.23, 0.85), "near_wall_left": (0.20, 0.33, 0.05, 0.88),
      "near_wall_right": (0.69, 0.78, 0.05, 0.88)}),
    ("dungeonofsecrets_real_3_doorway.png", "dungeonofsecrets", "real02_baked", "d3b_s10_room", [],
     {"doorway": (0.34, 0.68, 0.23, 0.85)}),
    ("dungeonofsecrets_real_4_corridor_purple.png", "dungeonofsecrets", "real02_baked", "d4_s04_corridor_w",
     ["d4_alt_back"],
     {"purple_room": (0.37, 0.55, 0.20, 0.48), "corridor_walls": (0.20, 0.33, 0.05, 0.88),
      "floor": (0.35, 0.60, 0.60, 0.88)}),
    ("dragonstadium_real_1_floor.png", "dragonstadium", "real01_baked", "s1_floor_southwest",
     ["s1_alt_closer", "s1_alt_north"], {}),
]
CONTEXT = {m: json.loads((OUT / f"{m}_context.json").read_text())
           for m in ("yanmirsfort", "dungeonofsecrets", "dragonstadium")}


def shot_path(stem: str, folder: str, name: str) -> Path:
    return next((PROJECTS / f"mm9r_{stem}/review" / folder).glob(f"*-{name}.png"))


def context(stem: str, name: str) -> dict | None:
    return next((s for s in CONTEXT[stem]["shots"] if s["shot"] == name), None)


def main() -> int:
    rows, sheets = [], {}
    for real, stem, folder, name, alts, extra in SHOTS:
        real_path = REAL_DIR / real
        entry = {"real": real, "map": stem, "real_stats": stats(real_path, True, extra), "ours": []}
        for shot in [name] + alts:
            path = shot_path(stem, folder, shot)
            ctx = context(stem, shot)
            entry["ours"].append({"shot": shot, "capture": str(path.relative_to(ROOT)),
                                  "stats": stats(path, False, extra),
                                  "mm9_prediction": None if ctx is None else
                                  {k: ctx[k] for k in ("eye_lt", "rays", "no_hit", "no_lightmap", "unlit_models",
                                                       "all", "bands", "kinds", "textures")},
                                  "lights": None if ctx is None else ctx["lights"]})
        rows.append(entry)
        sheets.setdefault(stem, []).append((real_path, [Path(ROOT / o["capture"]) for o in entry["ours"]],
                                            entry))
    result = {"settings": {m: CONTEXT[m]["settings"] for m in CONTEXT}, "shots": rows}
    (OUT / "measurements.json").write_text(json.dumps(result, indent=1) + "\n")
    for stem, items in sheets.items():
        columns = 1 + max(len(i[1]) for i in items)
        image = Image.new("RGB", (TILE[0] * columns, (TILE[1] + 34) * len(items)), (12, 12, 16))
        draw = ImageDraw.Draw(image)
        for row, (real_path, ours, entry) in enumerate(items):
            y = row * (TILE[1] + 34)
            rs = entry["real_stats"]
            cells = [(real_path, f"REAL {real_path.stem.split('_real_')[-1]}: luma {rs['luma']} med {rs['median']} "
                                 f"RGB {tuple(rs['rgb'])}")]
            for o in entry["ours"]:
                st, pred = o["stats"], o["mm9_prediction"]
                text = f"ours {o['shot']}: {st['luma']} (x{st['luma'] / rs['luma']:.2f}) RGB {tuple(st['rgb'])}"
                if pred and pred["all"].get("n"):
                    text += f"  MM9 tex*lm {pred['all']['pred_luma']}"
                cells.append((Path(o["capture"]) if Path(o["capture"]).is_absolute() else ROOT / o["capture"], text))
            for col, (path, text) in enumerate(cells):
                image.paste(Image.open(path).convert("RGB").resize(TILE), (col * TILE[0], y + 34))
                draw.text((col * TILE[0] + 4, y + 3), text[:86], fill=(235, 235, 235))
                draw.text((col * TILE[0] + 4, y + 17), path.name[:80], fill=(160, 160, 160))
        out = REAL_DIR / f"{stem}_real_vs_ours.jpg"
        image.save(out, quality=88)
        print(out)
    for entry in rows:
        rs = entry["real_stats"]
        print(f"\n{entry['real']}: real {rs}")
        for o in entry["ours"]:
            pred = o["mm9_prediction"]["all"] if o["mm9_prediction"] else {}
            print(f"  {o['shot']}: ours {o['stats']}")
            print(f"     MM9 tex*lm: {pred}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
