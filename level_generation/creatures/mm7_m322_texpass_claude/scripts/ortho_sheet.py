"""Bind-pose orthographic before | after sheet with the engine colour (region ramps applied as viewer_variants.bake),
for quick checks of a composed map set before building the GLB.
Usage: ortho_sheet.py <maps prefix> <out png> <tier index 0-8> [view:cx:cy:half ...]"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb import Glb  # noqa: E402
from viewer_variants import bake  # noqa: E402
import ortho  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
prefix, out, tier = sys.argv[1], sys.argv[2], int(sys.argv[3])
shots = [a.split(':') for a in sys.argv[4:]] or [['front', '0', '1.45', '0.3'], ['quarter', '0', '1.45', '0.3'],
                                                   ['back', '0', '1.3', '0.45'], ['front', '0', '1.6', '0.09']]
L = np.load(HERE / 'work' / 'uv_fine.npz')
d = np.load(HERE / 'work' / 'lod0_before.npz')
g = Glb(HERE / 'work' / 'before_texpass' / 'mm7_m322.glb')
ramps = g.doc['materials'][tier]['extras']['openyamm_region_ramps']
old = bake(g.image(0).convert('RGB'), g.image(3), ramps).astype(np.float64)
new = bake(Image.open(f'{prefix}_basecolor.png').convert('RGB'), Image.open(f'{prefix}_region_mask.png'),
           ramps).astype(np.float64)
rows = []
for img, uv in ((old, d['uv'][d['tri']]), (new, L['uv'])):
    rows.append(np.concatenate([ortho.render(img, uv, L['xyz'], v, (float(cx), float(cy)), float(h), 420, shade=0.35)
                                for v, cx, cy, h in shots], 1))
Image.fromarray(np.clip(np.concatenate(rows, 0), 0, 255).astype(np.uint8)).save(out)
print('SHEET', out, g.doc['materials'][tier]['name'])
