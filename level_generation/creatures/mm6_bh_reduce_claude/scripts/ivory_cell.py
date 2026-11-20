#!/usr/bin/env python3
"""Choose a free square of the UV layout for the rebuilt teeth and the values painted there -> work/ivory_cell.json:
the largest unused 2K square (source UV coverage, 4-texel margin to the islands), a UV cell 16 texels
smaller than the painted block on each side (mip margin), base colour as a root-to-tip gradient between the 25th and 90th percentile of the big fangs' clean
ivory texels (graded base colour space), and the fangs' median region mask / metal-roughness values (the face region,
so the teeth follow the same tier ramp as the fangs did), flat normal.
Usage: ivory_cell.py <glb with the textures>"""
import io, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
doc, binary = read_glb(Path(sys.argv[1]))
imgs = {}
for im in doc['images']:
    bv = doc['bufferViews'][im['bufferView']]
    imgs[im['name']] = np.asarray(Image.open(io.BytesIO(binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']])))
base = imgs['bh_a_basecolor_graded']; S = base.shape[0]
d = np.load(HERE / 'work/mesh_in.npz'); uv = d['wuv'].reshape(-1, 3, 2)
cov = Image.new('L', (S, S), 0); dr = ImageDraw.Draw(cov)
for t in uv:
    dr.polygon([(u * S, (1 - v) * S) for u, v in t], fill=255)
free = ~ndimage.binary_dilation(np.asarray(cov) > 0, iterations=4)
free[:2], free[-2:], free[:, :2], free[:, -2:] = False, False, False, False   # keep the block inside the image
dt = ndimage.distance_transform_cdt(free, metric='chessboard')
y, x = np.unravel_index(dt.argmax(), dt.shape); half = int(dt[y, x])
assert half >= 20, f'free square too small: {half}'
ph = min(half, 40); ch = ph - 6
paint = [int(x - ph), int(y - ph), int(x + ph), int(y + ph)]; cell = [int(x - ch), int(y - ch), int(x + ch), int(y + ch)]
# fang ivory texels (graded space) from the fang faces' clean ivory
labels = np.load(HERE / 'work/teeth_labels.npy'); fang = np.where(labels == 1)[0]
B = np.random.default_rng(0).dirichlet((1, 1, 1), 24); u = np.einsum('sk,fkc->fsc', B, uv[fang]).reshape(-1, 2)
px = lambda a: a[np.clip(((1 - u[:, 1]) * a.shape[0]).astype(int), 0, a.shape[0] - 1), np.clip((u[:, 0] * a.shape[1]).astype(int), 0, a.shape[1] - 1)]
col = px(base).astype(float); lum = col.mean(1); ok = (lum > np.percentile(lum, 40)) & (col.max(1) - col.min(1) < 80)
c0 = np.percentile(col[ok], 25, axis=0); c1 = np.percentile(col[ok], 90, axis=0)
mask = np.median(px(imgs['bh_region_mask'])[ok], axis=0); mr = np.median(px(imgs['bh_metal_rough_1k'])[ok], axis=0)
spec = {'size': S, 'paint_px': paint, 'cell_uv': [cell[0] / S, 1 - cell[3] / S, cell[2] / S, 1 - cell[1] / S],
        'paint': {'bh_a_basecolor_graded': {'gradient': [c0.round().tolist(), c1.round().tolist()], 'noise': 3},
                  'bh_region_mask': {'value': mask.round().tolist()},
                  'bh_metal_rough_1k': {'value': mr.round().tolist()},
                  'bh_normal_1k': {'value': [128, 128, 255]}}}
(HERE / 'work/ivory_cell.json').write_text(json.dumps(spec, indent=1)); print(json.dumps(spec))
