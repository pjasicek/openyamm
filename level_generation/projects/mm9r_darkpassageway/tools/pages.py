#!/usr/bin/env python3
"""Compare pages: tools/pages.py out_prefix dirA [dirB ...] -- rows per view (columns = dirs), 6 views a page."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, dirs = sys.argv[1], [Path(d) for d in sys.argv[2:]]
names = sorted(p.name for p in dirs[0].glob("*.png"))
W, H, PER = 520, 293, 6
for page in range(0, len(names), PER):
    chunk = names[page:page + PER]
    sheet = Image.new("RGB", (W * len(dirs), H * len(chunk)), (0, 0, 0))
    d = ImageDraw.Draw(sheet)
    for r, n in enumerate(chunk):
        for c, folder in enumerate(dirs):
            p = folder / n
            if p.exists():
                sheet.paste(Image.open(p).convert("RGB").resize((W, H)), (c * W, r * H))
        d.text((4, r * H + 4), n, fill=(255, 255, 0))
    sheet.save(f"{out}_p{page // PER + 1:02d}.jpg", quality=85)
    print(f"{out}_p{page // PER + 1:02d}.jpg")
