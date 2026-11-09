"""
Review sheets: a contact sheet of one tour, a side-by-side of two tours with the same views (MM9 original left, the
native BLV right), and the lighting compare of three (MM9 original | native unbaked | native baked).

    python3 -m dungeon.sheet <review dir>/<new> <review dir>/<original>          # (run with mm9r_common on sys.path)
    python3 -m dungeon.sheet <original> <a> <b> [--labels "MM9 original,before,after"] [--out <name>.jpg]
    python3 -m dungeon.sheet --brightness <folder>...                           # mean of each folder's views
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

TILE = (480, 270)


def compare(folders: list[Path], labels: list[str], out: Path, per_row: int | None = None) -> Path:
    """Shots of the same names from each folder side by side (one group per view), labelled."""
    shots = sorted(p.name for p in folders[-1].glob("*.png"))
    per_row = per_row or (3 if len(folders) == 1 else (2 if len(folders) == 2 else 1))
    columns = per_row * len(folders)
    rows = (len(shots) + per_row - 1) // per_row
    sheet = Image.new("RGB", (TILE[0] * columns, (TILE[1] + 18) * rows), (12, 12, 16))
    draw = ImageDraw.Draw(sheet)
    for index, name in enumerate(shots):
        row, slot = divmod(index, per_row)
        for k, (folder, label) in enumerate(zip(folders, labels)):
            x = (slot * len(folders) + k) * TILE[0]
            y = row * (TILE[1] + 18)
            if (folder / name).exists():
                sheet.paste(Image.open(folder / name).convert("RGB").resize(TILE), (x, y + 18))
            else:
                draw.text((x + 8, y + 40), "missing", fill=(255, 80, 80))
            draw.text((x + 4, y + 3), name[:-4] + (f" ({label})" if label else ""), fill=(230, 230, 230))
    sheet.save(out, quality=88)
    print(out)
    return out


def brightness(folder: Path) -> float:
    """Mean brightness (0-255, mean of RGB) of a tour's views, centre crop (the middle 60 % across, 10-75 % down:
    no HUD, no portraits)."""
    values = []
    for shot in sorted(folder.glob("*.png")):
        image = Image.open(shot).convert("RGB")
        w, h = image.size
        crop = image.crop((int(w * 0.2), int(h * 0.1), int(w * 0.8), int(h * 0.75)))
        values.append(float(np.asarray(crop, dtype=np.float32).mean()))
    return sum(values) / len(values) if values else 0.0


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--brightness":
        for folder in args[1:]:
            print(f"{brightness(Path(folder)):6.1f}  {folder}")
        return 0
    labels = out = None
    if "--labels" in args:
        index = args.index("--labels")
        labels = args[index + 1].split(",")
        del args[index:index + 2]
    if "--out" in args:
        index = args.index("--out")
        out = Path(args[index + 1])
        del args[index:index + 2]
    folders = [Path(a) for a in args]
    if labels:
        compare(folders, labels, out or folders[-1].parent / f"{folders[-1].name}_compare.jpg")
    elif len(folders) == 1:
        compare(folders, [""], folders[0].parent / f"{folders[0].name}_sheet.jpg")
    elif len(folders) == 2:            # new, original -> original | new
        compare([folders[1], folders[0]], ["MM9 original", "native BLV"],
                folders[0].parent / f"{folders[0].name}_compare.jpg")
    else:                              # original, unbaked, baked
        compare(folders[:3], ["MM9 original", "native BLV, unbaked", "native BLV, baked"],
                folders[2].parent / f"{folders[2].name.rsplit('_', 1)[0]}_compare.jpg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
