#!/usr/bin/env python3
"""Per-sample world heights of head, pelvis, both feet and toes, and the lowest LOD0 vertex of each foot, over a clip
(gate runner's pose evaluation, 120 Hz plus the viewer's 48 fps frames). Usage: walk_heights.py <glb> <clip> <out.json>"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared/gates'))
from run_gates import Glb, load_meshes, sample_grid  # noqa: E402
glb, clip_name, out = sys.argv[1:4]
g = Glb(glb)
name, clip, start, end = next(c for c in g.clips() if c[0] == clip_name)
mesh = next(m for m in load_meshes(g) if m.label.endswith('colour0') and 'shadow' not in m.label and '_B/' not in m.label and '_C/' not in m.label)
up = 2  # the gate runner converts to Z up
bones = ['B_Head', 'B_Pelvis', 'B_L_Foot', 'B_R_Foot', 'B_L_Toe0', 'B_R_Toe0']
lw = mesh.weight(['B_L_Foot', 'B_L_Toe0']) > .5; rw = mesh.weight(['B_R_Foot', 'B_R_Toe0']) > .5
res = {}
for label, times in (('120', sample_grid(start, end, 120)), ('48', np.arange(0, round((end - start) * 48) + 1) / 48 + start)):
    poses = g.pose(clip, times)
    rows = []
    for t, pose in zip(times, poses):
        r = {'t': float(t)}
        for b in bones:
            r[b] = float(pose[g.names[b]][up, 3])
        v = mesh.posed(pose)
        r['L_sole'] = float(v[lw, 2].min())
        r['R_sole'] = float(v[rw, 2].min())
        rows.append(r)
    res[label] = rows
Path(out).write_text(json.dumps({'clip': clip_name, 'start': float(start), 'end': float(end), 'samples': res}, indent=1))
h = np.array([r['B_Head'] for r in res['48']]); p = np.array([r['B_Pelvis'] for r in res['48']])
print('CLIP', clip_name, 'duration', round(end - start, 4), 'frames48', len(h) - 1)
for i, r in enumerate(res['48']):
    print('F%02d t=%.4f head %.4f pelvis %.4f Lsole %.4f Rsole %.4f dHead %+.4f dPelvis %+.4f' % (i, r['t'], r['B_Head'], r['B_Pelvis'], r['L_sole'], r['R_sole'], h[i] - h[i - 1] if i else 0, p[i] - p[i - 1] if i else 0))
