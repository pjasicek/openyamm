#!/usr/bin/env python3
"""
Lighting sheet and per-view numbers of the 2026-10-31 re-light: review/<name>_original | _unbaked | [old bake] | _baked,
centre-crop luma per view (Beethoven's views.py crop: 20-80 % across, 20-75 % down), the darkest baked views, and the
sheets review/<name>_compare.jpg (all views) and review/<name>_pNN.jpg (6 views a page, for reading).

    python3 level_generation/projects/mm9r_common/relight_views.py level_generation/projects/mm9r_<map> NAME \
        [--old FOLDER] [--no-sheet]
"""
import argparse
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dungeon import sheet  # noqa: E402

LUMA = np.array([0.2126, 0.7152, 0.0722])


def crop(path: Path):
    a = np.asarray(Image.open(path).convert("RGB"), float)
    h, w = a.shape[:2]
    m = a[h // 5:h * 3 // 4, w // 5:w * 4 // 5].reshape(-1, 3).mean(0)
    return float(m @ LUMA), m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", type=Path)
    ap.add_argument("name")
    ap.add_argument("--old", help="folder of the old bake's shots (same names), under review/")
    ap.add_argument("--baked", help="folder of the installed bake's shots under review/ (default <name>_baked)")
    ap.add_argument("--no-sheet", action="store_true")
    args = ap.parse_args()
    review = args.project.resolve() / "review"
    folders = [review / f"{args.name}_original", review / f"{args.name}_unbaked"]
    labels = ["MM9 capture (old import)", "unbaked"]
    if args.old:
        folders.append(review / args.old)
        labels.append("old bake (capture-matched)")
    folders.append(review / (args.baked or f"{args.name}_baked"))
    labels.append("lightmap-matched bake")
    shots = sorted(p.name for p in folders[-1].glob("*.png"))
    print(f"{'view':28s} " + " ".join(f"{f.name[len(args.name) + 1:] if f.name.startswith(args.name) else 'old':>9s}"
                                      for f in folders) + "  baked RGB")
    rows = []
    for name in shots:
        values = [crop(f / name) if (f / name).exists() else (float("nan"), np.zeros(3)) for f in folders]
        rows.append([v[0] for v in values])
        print(f"{Path(name).stem:28s} " + " ".join(f"{v[0]:9.1f}" for v in values)
              + f"  {np.round(values[-1][1]).astype(int).tolist()}")
    rows = np.array(rows)
    print(f"{'mean':28s} " + " ".join(f"{v:9.1f}" for v in np.nanmean(rows, 0)))
    order = np.argsort(rows[:, -1])
    print("darkest baked views: " + ", ".join(f"{Path(shots[i]).stem} {rows[i, -1]:.1f}" for i in order[:5]))
    print(f"baked / capture: {np.nanmean(rows[:, -1]) / np.nanmean(rows[:, 0]):.2f}")
    if args.no_sheet:
        return 0
    sheet.compare(folders, labels, review / f"{args.name}_compare.jpg")
    for page in range(0, len(shots), 6):
        with tempfile.TemporaryDirectory() as temp:
            subsets = []
            for folder in folders:
                target = Path(temp) / folder.name
                target.mkdir()
                for name in shots[page:page + 6]:
                    if (folder / name).exists():
                        (target / name).symlink_to(folder / name)
                subsets.append(target)
            sheet.compare(subsets, labels, review / f"{args.name}_p{page // 6 + 1:02d}.jpg")
    print("sheets", review / f"{args.name}_compare.jpg", review / f"{args.name}_p01.jpg", "...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
