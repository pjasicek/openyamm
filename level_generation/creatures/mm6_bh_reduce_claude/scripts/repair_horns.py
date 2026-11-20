#!/usr/bin/env python3
"""Repair the Meshy texturing gaps on the horns: wide near-black blobs (tier A ramped luminance < 45, kept by a
morphological opening of radius 4 texels at 2K so the thin ring stripes stay) take the values of the nearest clean
texel of the same horn in rest-pose 3D, in all four shared maps (base colour, region mask, normal, metal/roughness)
at their own resolutions. The HD references have uniform grey horns; the gaps sit on surfaces no reference view saw.
Second pass (rule "neutral", on the first pass's ramped colours): the remaining grey camouflage mottles, dark and
neutral (luminance < 90, red - green < 12; the ring stripes are reddish), opened with radius 3.
Also used on the face region (group 1, rule dark): its near-black blobs sit on hidden surfaces (inner lips, behind
the brow), and reduced faces whose UVs drift onto them showed as black slivers.
Usage: repair_horns.py <in.glb> <ramped tier A base colour png> <out.glb> [dark|neutral] [group, default 2 horns]"""
import io, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from texel_raster import raster  # noqa: E402
from build_actor_lods import read_glb, write_glb  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
src, ramped, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
d = np.load(HERE / 'work/mesh_in.npz'); v, f = d['verts'], d['faces']; uv = d['wuv'].reshape(-1, 3, 2)
horns = np.where(np.load(HERE / 'work/groups_bh.npy') == (int(sys.argv[5]) if len(sys.argv) > 5 else 2))[0]
ref = np.asarray(Image.open(ramped).convert('RGB')).astype(float); RH, RW = ref.shape[:2]
R, C, I, P = raster(uv, v[f], horns, RW, RH)
RULE = sys.argv[4] if len(sys.argv) > 4 else 'dark'
lum = ref[R, C].mean(1); rg = ref[R, C, 0] - ref[R, C, 1]
sel = lum < 45 if RULE == 'dark' else (lum < 90) & (rg < 12)
dark = np.zeros((RH, RW), bool); dark[R[sel], C[sel]] = True
size = 9 if RULE == 'dark' else 7
gap = ndimage.binary_dilation(ndimage.binary_opening(dark, structure=np.ones((size, size), bool)), iterations=2) & dark
print('GAP texels at 2K', int(gap.sum()))


def repair(a):
    h, w = a.shape[:2]; s = RH // h
    r, c, i, p = raster(uv, v[f], horns, w, h)
    g = gap.reshape(h, s, w, s).any((1, 3)) if s > 1 else gap
    dk = dark.reshape(h, s, w, s).all((1, 3)) if s > 1 else dark
    bad = g[r, c]; good = ~bad & ~dk[r, c]
    side = np.sign(p[:, 0])
    out = a.copy(); n = 0
    for sd in (1, -1):
        gi = np.where(good & (side == sd))[0]; bi = np.where(bad & (side == sd))[0]
        if not len(bi):
            continue
        _, nn = cKDTree(p[gi]).query(p[bi])
        out[r[bi], c[bi]] = a[r[gi[nn]], c[gi[nn]]]; n += len(bi)
    return out, n


doc, binary = read_glb(src); new = {}
for im in doc['images']:
    bv = doc['bufferViews'][im['bufferView']]
    pil = Image.open(io.BytesIO(binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]))
    a, n = repair(np.asarray(pil).copy())
    buf = io.BytesIO(); Image.fromarray(a, pil.mode).save(buf, 'PNG', optimize=True); new[im['bufferView']] = buf.getvalue()
    print('REPAIRED', im.get('name'), a.shape, n, 'texels')
nb = bytearray()
for k, bv in enumerate(doc['bufferViews']):
    data = new.get(k, bytes(binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]))
    nb += b'\0' * (-len(nb) % 4); bv['byteOffset'] = len(nb); bv['byteLength'] = len(data); nb += data
write_glb(out, doc, bytes(nb)); print('WROTE', out)
