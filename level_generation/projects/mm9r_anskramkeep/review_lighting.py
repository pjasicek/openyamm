#!/usr/bin/env python3
"""
The baked-lighting review of Anskram Keep (devdocs/INDOOR_BAKED_LIGHTING.md): the v02 tour's views, three ways.

    python3 level_generation/projects/mm9r_anskramkeep/review_lighting.py tours <name>
        writes review_tour_<name>_{original,native,baked}.yml (output in review/<name>_<kind>/)
    python3 level_generation/projects/mm9r_anskramkeep/review_lighting.py sheet <name>
        review/<name>_compare.jpg: MM9 original (its own lightmaps) | native BLV unbaked | native BLV baked

Run the tours with tools/run_game.sh: the original against output/mm9_rework/assets_original (anskramkeep.odm), the
native one with `--set video.lightmaps=false`, the baked one with the bake installed (dungeon/lighting.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parent
KINDS = [("original", "MM9 original"), ("native", "native BLV, unbaked"), ("baked", "native BLV, baked")]
TILE = (480, 270)


def tours(name: str) -> None:
    base = yaml.safe_load((PROJECT / "review_tour_v02.yml").read_text())
    original = yaml.safe_load((PROJECT / "review_tour_v02_original.yml").read_text())
    for kind, _ in KINDS:
        tour = dict(original if kind == "original" else base)
        tour["output_dir"] = str(PROJECT / "review" / f"{name}_{kind}")
        path = PROJECT / f"review_tour_{name}_{kind}.yml"
        path.write_text(yaml.safe_dump(tour, sort_keys=False))
        print(path)


def sheet(name: str) -> None:
    folders = [PROJECT / "review" / f"{name}_{kind}" for kind, _ in KINDS]
    shots = sorted(p.name for p in folders[2].glob("*.png"))
    columns = len(KINDS)
    sheet_image = Image.new("RGB", (TILE[0] * columns, (TILE[1] + 18) * len(shots)), (12, 12, 16))
    draw = ImageDraw.Draw(sheet_image)
    for row, shot in enumerate(shots):
        for column, (folder, (_, label)) in enumerate(zip(folders, KINDS)):
            x, y = column * TILE[0], row * (TILE[1] + 18)
            if (folder / shot).exists():
                sheet_image.paste(Image.open(folder / shot).convert("RGB").resize(TILE), (x, y + 18))
            draw.text((x + 4, y + 3), f"{shot[:-4]} ({label})", fill=(230, 230, 230))
    out = PROJECT / "review" / f"{name}_compare.jpg"
    sheet_image.save(out, quality=88)
    print(out)


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("tours", "sheet"):
        print(__doc__)
        return 2
    (tours if sys.argv[1] == "tours" else sheet)(sys.argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
