#!/usr/bin/env python3
"""Contact sheet of the see-through test (follow-up 4): flat-shaded front faces (painter's order) with the holes in red, for the views
given as az:el (deg; az 0 = front, 90 = her left, 270 = her right). Usage: hole_sheet.py <glb> <lod> <out.png> az:el ..."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
import seethrough as st
g = st.Glb(sys.argv[1]); T, ids = st.lod_tris(g, int(sys.argv[2])); PX, R, CEN = st.PX, st.R, st.CEN
tiles = []
for v in sys.argv[4:]:
    az, el = map(float, v.split(':'))
    hole, idimg, (r, u, fwd) = st.view(T, az, el)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    front = n @ fwd < 0; P = T - CEN; X = (P @ r + R) / PX; Y = (R - P @ u) / PX; zc = (P @ fwd).mean(1)
    S = int(2 * R / PX); im = Image.new('RGB', (S, S), (90, 94, 100)); dr = ImageDraw.Draw(im)
    L = np.array([0.4, 0.6, -0.7]); L = L / np.linalg.norm(L)
    for i in np.nonzero(front)[0][np.argsort(-zc[front])]:
        s = int(60 + 170 * max(0.0, -(n[i] @ (fwd * 0.6 + np.array([0, -0.5, 0])) / 1.0)))
        c = (s, int(s * 0.85), int(s * 0.75)) if ids[i, 0] == 1 else (int(s * 0.7), s, int(s * 0.7))
        dr.polygon([(X[i, k], Y[i, k]) for k in range(3)], fill=c)
    a = np.asarray(im).copy(); a[hole] = [255, 0, 0]
    t = Image.fromarray(a).resize((S // 2, S // 2)); ImageDraw.Draw(t).text((4, 4), f'az {az:.0f} el {el:.0f}  holes {int(hole.sum())}', fill=(255, 255, 0))
    tiles.append(t)
cols = 4; w, h = tiles[0].size; out = Image.new('RGB', (w * cols, h * ((len(tiles) + cols - 1) // cols)))
for k, t in enumerate(tiles): out.paste(t, ((k % cols) * w, (k // cols) * h))
out.save(sys.argv[3]); print('SHEET', sys.argv[3], out.size)
