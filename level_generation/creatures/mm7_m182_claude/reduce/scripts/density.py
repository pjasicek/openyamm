#!/usr/bin/env python3
"""Where the v3b LOD0 triangles sit (system Python): per region of work/mesh_in.npz (the welded v3b LOD0) the triangle
count, surface area, density (triangles per dm²) and median triangle area. Regions come from the v3b master
(work/v3b/master_final.npz, matched by position): v3part 0 cdr1 body / wings, 1 grafted head, 2 neck loft, 3 dorsal
blades; the v3b neck patch (refitted join); the v3b wing-root zone (body-material faces whose vertices carry any wing
bone weight: the shoulder skin that follows the wing since v3b). Writes work/density.json."""
import json
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
H = Path(__file__).resolve().parents[1]; P = H.parent
d = np.load(H / 'work/mesh_in.npz'); v, f = d['verts'], d['faces']; mat = (d['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
M = np.load(P / 'work/v3b/master_final.npz'); dd, idx = cKDTree(M['co']).query(v); assert dd.max() < 1e-5, dd.max()
part = M['pa_v3part'][idx]; patch = np.load(P / 'work/v3b/neck_patch.npy')[idx]
wing_bones = [i for i, b in enumerate(M['bones']) if 'Wing' in b]
wingw = M['W'][idx][:, wing_bones].sum(1)
fpart = np.array([np.bincount(part[t], minlength=4).argmax() for t in f])
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
fl = lab[f[:, 0]]; small = np.bincount(fl)[fl] <= 80
area = 0.5 * np.linalg.norm(np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]]), axis=1)
root = (mat == 0) & (wingw[f] > 1e-4).any(1)
regions = {
    'grafted head skin + features (mat 1, joined)': (mat == 1) & ~small,
    'grafted head separate pieces (horns, cheek/frill spikes, eyes, teeth)': (mat == 1) & small,
    'neck join (v3b refitted patch, body/head material)': patch[f].all(1) & (mat != 2) & ~small,
    'dorsal blade row (40 blades)': (fpart == 3),
    'cdr1 body: wing-root shoulder zone (wing weights)': root & ~patch[f].all(1) & (fpart != 3),
    'cdr1 body: rest (trunk, legs, tail, claws)': (mat == 0) & ~root & ~patch[f].all(1) & (fpart != 3),
    'wings (cdr1 membranes, mat 2)': mat == 2,
}
cover = np.zeros(len(f), int)
rep = {}
for name, sel in regions.items():
    sel = sel & (cover == 0); cover[sel] = 1
    rep[name] = {'tris': int(sel.sum()), 'share_pct': round(100 * sel.sum() / len(f), 1), 'area_m2': round(float(area[sel].sum()), 4),
                 'tris_per_dm2': round(float(sel.sum() / max(area[sel].sum() * 100, 1e-9)), 1),
                 'median_tri_area_cm2': round(float(np.median(area[sel]) * 1e4), 2) if sel.any() else 0}
rep['unassigned'] = int((cover == 0).sum()); rep['total'] = len(f)
(H / 'work/density.json').write_text(json.dumps(rep, indent=1) + '\n')
for k, r in rep.items():
    print(k, r)
