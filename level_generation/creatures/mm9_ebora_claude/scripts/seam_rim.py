#!/usr/bin/env python3
"""Neck seam rim on the Concubine torso paint (Concubine face and hair fix, 2026-11-01 evening). The head skin meets the torso
in 22 zigzag edges at the neck base; along them the torso texture's island border carries Meshy's dark padding (luminance
0-35 at 2 % inside the faces on 9 of 22 edges against ~165 skin), drawn in the viewer as a thin dark 'W' at the neck.
Texels of the torso faces within 1.5 cm of the seam darker than 0.85 x skin, and the 6 px of padding around them off the
island (the faces' UVs touch a dark brown blob), are replaced by the nearest good texel of the island, feathered 1 px. Edits textures/<pre>_torso_tone.png in place (run after tone_sr.sh, before tiers_eb.py).
The same seam faces also carry near-black ambient occlusion in the shared ORM images (AO 13-16 of 255 on thin faces of
both sides, a dark zigzag on every tier): with the argument orm, the AO channel of textures/eb_head_orm.png and
eb_torso_orm.png gets the same repair inside the seam zone (faces within 1.5 cm of the seam, nothing else), with 8 px of
padding off the island (the torso island's neck edge sits 2-4 px from an AO-0 region).
Args: <pre> (sr; Ebora's eb colour set is accepted and left alone) | orm"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
pre = sys.argv[1]
D = np.load('work/mesh_sub.npz'); co, tri, uv, mat, comp = D['co'], D['tri'], D['uv'], D['mat'], D['comp']; mn = [str(x) for x in D['matnames']]
hi, ti = mn.index('EboraHead'), mn.index('EboraTorso')
key = np.round(co, 5); _, w = np.unique(key, axis=0, return_inverse=True); w = w.ravel()
eh = {}
for f in np.where(mat == hi)[0]:
    t = w[tri[f]]
    for k in range(3): eh[(min(t[k], t[(k + 1) % 3]), max(t[k], t[(k + 1) % 3]))] = f
seam = []
for f in np.where(mat == ti)[0]:
    t = w[tri[f]]
    for k in range(3):
        if (min(t[k], t[(k + 1) % 3]), max(t[k], t[(k + 1) % 3])) in eh: seam.append((co[tri[f][k]] + co[tri[f][(k + 1) % 3]]) / 2)
seam = np.array(seam)
def repair(p, m_, chan, thr=0.6, value_floor=0.45, pad=3):
    """texels of material m_'s faces within 1.5 cm of the seam whose channel(s) fall under thr x the zone median: nearest good texel"""
    im = Image.open(p); mode = im.mode; img = np.asarray(im.convert('RGB'), np.float32) / 255; H, W = img.shape[:2]
    tf = np.where(mat == m_)[0]
    near = tf[cKDTree(seam).query(co[tri[tf]].mean(1))[0] < 0.015]
    if m_ == hi: near = near[comp[tri[near]].max(1) == 0]     # head skin only (hair hanging by the neck keeps its own AO)
    def raster(faces):
        m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
        for f in faces: d.polygon([(float(uv[i, 0] * W), float((1 - uv[i, 1]) * H)) for i in tri[f]], fill=255)
        return np.asarray(m) > 0
    cover = raster(tf); zone = ndi.binary_dilation(raster(near), iterations=pad)
    other = raster(np.setdiff1d(tf, near)) & ~raster(near)     # texels of other islands are never touched
    v = img @ np.array([0.2126, 0.7152, 0.0722], np.float32) if chan is None else img[..., chan]
    okz = zone & cover & (v > value_floor)
    ref = float(np.median(v[okz])) if okz.any() else 0.6
    bad = zone & ((v < thr * ref) | ~cover) & ~other      # texels off the island inside the zone: padding for the texture filter
    good = cover & ~ndi.binary_dilation(bad, iterations=1) & (v >= thr * ref)
    idx = ndi.distance_transform_edt(~good, return_distances=False, return_indices=True)
    fill = img[idx[0], idx[1]]
    bw = np.clip(ndi.gaussian_filter(bad.astype(np.float32), 0.8) * 1.6, 0, 1)[..., None] * zone[..., None]
    out = img * (1 - bw) + fill * bw
    if chan is not None: out2 = img.copy(); out2[..., chan] = out[..., chan]; out = out2
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype('u1')).convert(mode if mode in ('RGB', 'RGBA', 'L') else 'RGB').save(p)
    print('SEAM RIM', p, 'torso/head faces in zone', len(near), 'repaired texels', int(bad.sum()), 'zone median', round(ref, 3))
if pre == 'orm':
    # 8 px of padding: the torso island's neck edge sits 2-4 px from an AO-0 region, which the filter drew as a dotted dark line
    repair('textures/eb_head_orm.png', hi, 0, pad=8); repair('textures/eb_torso_orm.png', ti, 0, pad=8)
else:
    # the neck faces' UVs touch a dark brown blob above the island (Meshy's paint beyond it): bilinear and mip filtering pulled
    # it in as a brown dotted band along the zigzag. Anything under 0.85 x skin in the zone, and the 6 px around off the
    # island, takes the nearest good skin texel
    repair(f'textures/{pre}_torso_tone.png', ti, None, thr=0.85, pad=6)
