#!/usr/bin/env python3
"""Painted thin bands of the shirt/vest (part 0 of work/glb_sets_a.npz) for make_sets_hom.py PAINT: a face is flagged when any of
seven barycentric UV samples hits the vest border (body region mask alpha > 0.3) or a red belt texel of the phom2_a paint
(work/tex_PHOM1_A_C.png: r > 90 and r > 2.2 g and r > 2.2 b). a50 smeared both into a dark wedge on the left flank.
-> work/paint_keep.npy (bool per GLB LOD0 face, file primitive order). Usage: paint_keep.py (after tex_extract.py, make_sets_hom.py a)"""
import io
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, b, nd, D = glbio.load(HERE / 'before' / 'mm9_phom1.glb', 'PHOM1')
s = np.load(HERE / 'work' / 'glb_sets_a.npz'); n0 = len(D['PHOM1_A']['T']); part = s['part'][:n0]
d = D['PHOM1_A']; T, U = d['T'], d['UV']


def image(i):
    im = doc['images'][i]; v = doc['bufferViews'][im['bufferView']]; o = v.get('byteOffset', 0)
    return Image.open(io.BytesIO(b[o:o + v['byteLength']]))


M = {m['name']: m for m in doc['materials']}
mask = np.asarray(image(M['PHOM1_A']['extras']['openyamm_region_mask']['index']).convert('RGBA'), float) / 255
C = np.asarray(Image.open(HERE / 'work' / 'tex_PHOM1_A_C.png').convert('RGB'), float)
bary = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float); bary /= bary.sum(1, keepdims=True)
uv = np.einsum('kc,fcd->fkd', bary, U[T])


def samp(img):
    H, W = img.shape[:2]; x = np.clip((uv[..., 0] * W).astype(int), 0, W - 1); y = np.clip((uv[..., 1] * H).astype(int), 0, H - 1)
    return img[y, x]


border = (samp(mask)[..., 3] > 0.3).any(1)
c = samp(C); belt = ((c[..., 0] > 90) & (c[..., 0] > 2.2 * c[..., 1]) & (c[..., 0] > 2.2 * c[..., 2])).any(1)
out = np.r_[(border | belt) & (part == 0), np.zeros(len(D['PHOM1Head_A']['T']), bool)]
print('border', int((border & (part == 0)).sum()), 'belt', int((belt & (part == 0)).sum()), 'flagged', int(out.sum()))
np.save(HERE / 'work' / 'paint_keep_check.npy' if len(sys.argv) > 1 else HERE / 'work' / 'paint_keep.npy', out)
