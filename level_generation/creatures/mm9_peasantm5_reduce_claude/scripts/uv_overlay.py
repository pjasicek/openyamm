#!/usr/bin/env python3
"""Head primitive UV layout drawn over its base colour, coloured per welded component -> review/uv_head.png (read-only)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantm5.glb', 'PeasantM5')
name = sys.argv[1] if len(sys.argv) > 1 else 'PeasantM5Head'
d = D[name]; P, T, U = d['P'], d['T'], d['UV']
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl = lab[FT[:, 0]]
img = Image.open(HERE / 'work' / f'tex_{name}_A.png').convert('RGB')
S = img.size[0]; dr = ImageDraw.Draw(img)
cols = [(255, 0, 0), (0, 255, 0), (0, 128, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
for f in range(len(T)):
    pts = [(U[v, 0] * S, U[v, 1] * S) for v in T[f]]
    dr.polygon(pts, outline=cols[fl[f] % len(cols)])
img.save(HERE / 'review' / f'uv_{name}.png'); print('ok', len(T))
