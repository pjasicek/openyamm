#!/usr/bin/env python3
"""Two heads on one upload (guard_heads_upload.glb): composite the Codex head views into one reference per view. Heads sit at
(-d/2, -d/2) (tier A) and (+d/2, +d/2) (tier C) about the centre: canvas positions follow from the view. Run in the project folder."""
import numpy as np
from PIL import Image
D, PXM, S = 0.30, 3450.0, 2048
Z_CEN, Y_CEN = 0.7765, 0.027
TOP, W_H, W_S = 0.94, 0.238, 0.25
for name, sa, sc_, near_first in (('01_front', -1, 1, 0), ('02_back', 1, -1, 0), ('03_left', -1, 1, 0), ('04_right', 1, -1, 0)):
    can = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    for t, sg in (('a', sa), ('c', sc_)):
        im = Image.open(f'references_head/{t}_{name}.png').convert('RGBA')
        a = np.asarray(im)[..., 3] > 128
        ys, xs = np.where(a)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        # helmet width sets this image's scale; its top is the mesh top
        row = a[: int(y0 + 0.75 * (y1 - y0))]
        cols = np.where(row.any(0))[0]
        width = (cols.max() - cols.min()) / (W_S if name[:2] in ('03', '04') else W_H)
        k = PXM / width
        w = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        cx = (cols.min() + cols.max()) / 2 * k; top = y0 * k
        px = S / 2 + sg * D / 2 * PXM - cx
        py = S / 2 - (TOP - Z_CEN) * PXM - top
        can.alpha_composite(w, (max(int(px), 0), max(int(py), 0))) if px >= 0 and py >= 0 else can.paste(w, (int(px), int(py)), w)
        print(name, t, 'scale', round(k, 3), 'pos', int(px), int(py))
    can.save(f'references_head/duo_{name}.png')
