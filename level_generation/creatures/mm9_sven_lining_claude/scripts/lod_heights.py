#!/usr/bin/env python3
"""LOD heights and floor contact by number (lining check): for each LOD mesh (LOD0 + extras openyamm_lods) of two GLBs,
the lowest and highest posed point over every key time of every clip (and the rest bounds). Prints both and the largest
difference. Usage: lod_heights.py <installed glb> <candidate glb> [out json]"""
import json
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402


def lod_prims(model, mesh_index, node_index):
    out = []
    for p in model.glb.json['meshes'][mesh_index]['primitives']:
        a = p['attributes']
        w = model.glb.accessor(a['WEIGHTS_0']).astype(np.float64)
        out.append({'node': node_index, 'positions': model.glb.accessor(a['POSITION']).astype(np.float64),
                    'triangles': model.glb.accessor(p['indices']).astype(np.int64).reshape(-1, 3), 'skinned': True,
                    'joints': model.glb.accessor(a['JOINTS_0']).astype(np.int64),
                    'weights': w / np.maximum(w.sum(1, keepdims=True), 1e-12)})
    return out


def heights(path):
    m = Model(Glb(path))
    doc = m.glb.json
    ni = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == 'Sven' and 'mesh' in n)
    mi = doc['nodes'][ni]['mesh']
    res = {}
    for lod, mesh in enumerate([mi] + doc['meshes'][mi]['extras']['openyamm_lods']):
        m.primitives = lod_prims(m, mesh, ni)
        r = res[f'LOD{lod}'] = {}
        for clip in m.clips:
            lo, hi = 9.0, -9.0
            for t in m.clip_times(clip):
                for pts, _ in m.skinned_positions(m.world(m.sample(clip, t))):
                    lo = min(lo, float(pts[:, 1].min())); hi = max(hi, float(pts[:, 1].max()))
            r[clip] = [round(lo, 5), round(hi, 5)]
    return res


a, b = heights(sys.argv[1]), heights(sys.argv[2])
worst = 0.0
for lod in a:
    for clip in a[lod]:
        d = max(abs(a[lod][clip][0] - b[lod][clip][0]), abs(a[lod][clip][1] - b[lod][clip][1]))
        worst = max(worst, d)
        flag = '' if d < 1e-5 else f'  DIFF {d * 1000:.2f} mm'
        print(f'{lod} {clip:12s} installed low/high {a[lod][clip]} candidate {b[lod][clip]}{flag}')
print(f'LOD_HEIGHTS largest difference {worst * 1000:.3f} mm')
if len(sys.argv) > 3:
    Path(sys.argv[3]).write_text(json.dumps({'installed': a, 'candidate': b, 'max_diff_mm': worst * 1000}, indent=1))
