#!/usr/bin/env python3
"""Surface gap between Dagrell bone pieces per clip (coordinator request 2026-10-30): dense samples of each LOD0 triangle
of the XneckB / XtailB pieces against the sampled surface of everything else, so a low-poly vertex spacing does not read
as a gap. Prints each piece's gap to the nearest other piece: worst per clip, and the Standing frame 0 value.
Usage: texpass_necktail_surface.py <glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose

glb = glb_pose.Glb(sys.argv[1])
model = glb_pose.Model(glb)
names = [glb.json['nodes'][j].get('name', str(j)) for j in model.joints]
first = next(p for p in model.primitives if p['skinned'])
prims = [p for p in model.primitives if p['skinned'] and p['node'] == first['node']]
tri, offset, dom = [], 0, []
for p in prims:
    tri.append(p['triangles'] + offset)
    w = np.zeros((len(p['positions']), len(names)))
    for c in range(p['joints'].shape[1]):
        np.add.at(w, (np.arange(len(w)), p['joints'][:, c]), p['weights'][:, c])
    dom.append(w)
    offset += len(p['positions'])
tri = np.concatenate(tri)
dom = np.concatenate(dom)
stop = offset
# surface samples: barycentric grid per triangle
k = 5
ii, jj = np.meshgrid(np.arange(k + 1), np.arange(k + 1))
keep = ii + jj <= k
b = np.stack([ii[keep] / k, jj[keep] / k, 1 - (ii[keep] + jj[keep]) / k], -1)
dom_tri = dom[tri].sum(1).argmax(1)
TARGET = ['XneckB', 'XtailB']
report = {}
for clip in model.clips:
    for t in np.arange(0, model.clip_times(clip)[-1] + 1e-6, 1 / 16):
        pos = np.concatenate([pts for pts, _ in model.skinned_positions(model.world(model.sample(clip, float(t))))])[:stop]
        samples = np.einsum('sk,tkc->tsc', b, pos[tri])
        lab = np.repeat(dom_tri, len(b))
        flat = samples.reshape(-1, 3)
        for bone in TARGET:
            ib = names.index(bone)
            mine, other = flat[lab == ib], flat[lab != ib]
            parent_side = {'XneckB': ('Xneckbase', 'XbackB', 'Xheadpiv'), 'XtailB': ('XtailA', 'XtailC')}[bone]
            for side in parent_side:
                s = flat[lab == names.index(side)]
                if len(s):
                    d = float(cKDTree(s).query(mine)[0].min())
                    row = report.setdefault((bone, side), {})
                    if clip not in row or d > row[clip][0]:
                        row[clip] = (round(d, 4), round(float(t), 3))
for key, row in report.items():
    print(key, 'standing', row.get('Standing'), 'worst', max(row.items(), key=lambda kv: kv[1][0]), {c: v[0] for c, v in row.items()})
