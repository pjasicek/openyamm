#!/usr/bin/env python3
"""
Contact sheet of a review tour, or a side-by-side of two tours with the same views (original left, new right).

    python3 level_generation/projects/mm9r_anskramkeep/review_sheet.py review/v01                     # sheet
    python3 level_generation/projects/mm9r_anskramkeep/review_sheet.py review/v01 review/v01_original # compare
    python3 level_generation/projects/mm9r_anskramkeep/review_sheet.py OUT.jpg A B C --labels "a,b,c"  # columns
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parent
TILE = (480, 270)


def columns_sheet(output: Path, folders: list[Path], labels: list[str]) -> Path:
    """One view per row, one column per tour (e.g. MM9 original | native 1x | native x4)."""
    shots = sorted(p.name for p in folders[0].glob("*.png"))
    sheet = Image.new("RGB", (TILE[0] * len(folders), (TILE[1] + 18) * len(shots)), (12, 12, 16))
    draw = ImageDraw.Draw(sheet)
    for row, name in enumerate(shots):
        for k, folder in enumerate(folders):
            x, y = k * TILE[0], row * (TILE[1] + 18)
            if (folder / name).exists():
                sheet.paste(Image.open(folder / name).convert("RGB").resize(TILE), (x, y + 18))
            draw.text((x + 4, y + 3), f"{name[:-4]} ({labels[k]})", fill=(230, 230, 230))
    sheet.save(output, quality=90)
    return output


def main() -> int:
    if "--labels" in sys.argv:
        index = sys.argv.index("--labels")
        labels = sys.argv[index + 1].split(",")
        paths = sys.argv[1:index]
        print(columns_sheet(PROJECT / paths[0], [PROJECT / p for p in paths[1:]], labels))
        return 0
    folders = [PROJECT / a for a in sys.argv[1:3]]
    shots = sorted(p.name for p in folders[0].glob("*.png"))
    columns = 3 if len(folders) == 1 else 4
    rows = (len(shots) + (columns // len(folders)) - 1) // (columns // len(folders))
    sheet = Image.new("RGB", (TILE[0] * columns, (TILE[1] + 18) * rows), (12, 12, 16))
    draw = ImageDraw.Draw(sheet)
    per_row = columns // len(folders)
    for index, name in enumerate(shots):
        row, slot = divmod(index, per_row)
        for k, folder in enumerate(reversed(folders) if len(folders) == 2 else folders):
            path = folder / name
            if len(folders) == 2:
                path = (folders[1] if k == 0 else folders[0]) / name
            x = (slot * len(folders) + k) * TILE[0]
            y = row * (TILE[1] + 18)
            if path.exists():
                sheet.paste(Image.open(path).convert("RGB").resize(TILE), (x, y + 18))
            label = name[:-4] + ("" if len(folders) == 1 else (" (MM9 original)" if k == 0 else " (native BLV)"))
            draw.text((x + 4, y + 3), label, fill=(230, 230, 230))
    out = folders[0].parent / (folders[0].name + ("_sheet.jpg" if len(folders) == 1 else "_compare.jpg"))
    sheet.save(out, quality=88)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
