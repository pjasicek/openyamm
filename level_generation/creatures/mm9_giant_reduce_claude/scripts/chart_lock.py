#!/usr/bin/env python3
"""Chart guard for the MeshLab route (fix pass 2026-11-04, after the orchestrator's UV audit found 66 pass-2 LOD0 faces
whose UVs leave the painted charts: wedges on the belt, pauldron rim and chest fur). The texture-aware quadric keeps wedge
UVs but may slide a seam vertex so that a new face's UV triangle reaches into the gutter.
Test (as claude_shared/reduction_uv_audit.py): the source UV triangles of each material rasterised at RES and dilated by
DIL texels; every face of a ladder candidate (work/mesh_r<NN>.npz, material from the u offset) sampled at 91 barycentric
points; a face escapes when more than FRAC of its samples are off the coverage. The source faces within R metres (rest
pose) of each escaping face are added to the keep mask, so the next decimation keeps them exactly.
Usage: chart_lock.py <NN> <keep in .npy> <keep out .npy>   (prints ESCAPING n; 0 = clean)"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.spatial import cKDTree
RES, DIL, FRAC = int(os.environ.get('RES', '2048')), int(os.environ.get('DIL', '2')), float(os.environ.get('FRAC', '0.02'))
R = float(os.environ.get('LOCK_R', '0.03'))
tag, kin, kout = sys.argv[1], sys.argv[2], sys.argv[3]
s = np.load('work/mesh_in.npz'); sf, sv = s['faces'], s['verts']; suv = s['wuv'].reshape(-1, 3, 2)
smat = (suv[:, 0, 0] // 2).astype(int)
cover = {}
for m in np.unique(smat):
    im = Image.new('L', (RES, RES), 0); dr = ImageDraw.Draw(im)
    for t in suv[smat == m]:
        pts = [((u - 2 * m) * RES, v * RES) for u, v in t]
        dr.polygon(pts, fill=255, outline=255)
    cover[m] = ndimage.binary_dilation(np.asarray(im) > 0, iterations=DIL)
k = 12; ii, jj = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); msk = ii + jj <= k
W = np.stack([ii[msk], jj[msk], k - ii[msk] - jj[msk]], 1) / k          # 91 samples
c = np.load(f'work/mesh_r{tag}.npz'); cf, cv = c['faces'], c['verts']; cuv = c['wuv'].reshape(-1, 3, 2)
cmat = (cuv[:, 0, 0] // 2).astype(int)
esc = []
for i in range(len(cf)):
    m = cmat[i]; uv = W @ (cuv[i] - np.array([2 * m, 0]))
    x = np.clip((uv[:, 0] * RES).astype(int), 0, RES - 1); y = np.clip((uv[:, 1] * RES).astype(int), 0, RES - 1)
    if (~cover[m][y, x]).mean() > FRAC:
        esc.append(i)
esc = np.array(esc, int)
keep = np.load(kin).copy(); n0 = int(keep.sum())
if len(esc):
    cen = cv[cf[esc]].mean(1); t = cKDTree(cen)
    d, _ = t.query(sv[sf].mean(1)); keep |= d < R
np.save(kout, keep)
print('ESCAPING', len(esc), 'by material', {int(m): int((cmat[esc] == m).sum()) for m in np.unique(cmat[esc])} if len(esc) else {},
      '| keep', n0, '->', int(keep.sum()))
