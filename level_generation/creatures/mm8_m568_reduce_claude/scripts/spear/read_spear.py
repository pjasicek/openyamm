#!/usr/bin/env python3
"""Spear handling of a creature GLB in its chest's rest-relative space (Blender Z-up; carrier = chest(t) @ chest_rest^-1,
as animate_salamander.py uses it): polearm origin, shaft axis (+Y of the Polearm node), blade-plane axis (+X), each
hand's wrist and its shaft parameter (projection on the shaft, polearm local Y), elbows and shoulders.
Usage: read_spear.py <glb> <out.json> [fps]"""
import json
import sys
import numpy as np
from gltf_pose import Gltf, YUP

g = Gltf(sys.argv[1]); fps = float(sys.argv[3]) if len(sys.argv) > 3 else 24
N = g.names; ids = {k: N[k] for k in ['B_Spine2', 'Polearm', 'B_L_Hand', 'B_R_Hand', 'B_L_Forearm', 'B_R_Forearm',
                                       'B_L_UpperArm', 'B_R_UpperArm', 'B_Pelvis', 'B_Head']}
rest = [YUP @ m for m in g.globals(None, 0)]
out = {'rest': {k: rest[i][:3, 3].tolist() for k, i in ids.items()}, 'clips': {}}
for a in g.doc['animations']:
    name = a['name']; anim = g.animation(name); dur = g.duration(name); frames = []
    for f in range(int(round(dur * fps)) + 1):
        t = min(f / fps, dur); G = [YUP @ m for m in g.globals(anim, t)]
        carrier = G[ids['B_Spine2']] @ np.linalg.inv(rest[ids['B_Spine2']]); inv = np.linalg.inv(carrier)
        rr = lambda i: (inv @ G[i])
        P = rr(ids['Polearm']); o = P[:3, 3]; ax = P[:3, 1] / np.linalg.norm(P[:3, 1]); side = P[:3, 0] / np.linalg.norm(P[:3, 0])
        rec = {'t': t, 'origin': o.tolist(), 'axis': ax.tolist(), 'side': side.tolist(),
               'world_origin': G[ids['Polearm']][:3, 3].tolist(), 'world_axis': (G[ids['Polearm']][:3, 1] / np.linalg.norm(G[ids['Polearm']][:3, 1])).tolist()}
        for sd in 'LR':
            w = rr(ids[f'B_{sd}_Hand'])[:3, 3]
            rec[f'{sd}_wrist'] = w.tolist(); rec[f'{sd}_s'] = float(np.dot(w - o, ax))
            rec[f'{sd}_off'] = float(np.linalg.norm((w - o) - ax * np.dot(w - o, ax)))
            rec[f'{sd}_elbow'] = rr(ids[f'B_{sd}_Forearm'])[:3, 3].tolist(); rec[f'{sd}_shoulder'] = rr(ids[f'B_{sd}_UpperArm'])[:3, 3].tolist()
        rec['pelvis_world'] = G[ids['B_Pelvis']][:3, 3].tolist()
        frames.append(rec)
    out['clips'][name] = {'duration': dur, 'frames': frames}
json.dump(out, open(sys.argv[2], 'w'), indent=0)
for name, c in out['clips'].items():
    fr = c['frames']; s = lambda k: np.array([x[k] for x in fr])
    print(name, round(c['duration'], 4), 'R_s', np.round([s('R_s').min(), s('R_s').max()], 3), 'L_s', np.round([s('L_s').min(), s('L_s').max()], 3),
          'off', np.round([s('R_off').max(), s('L_off').max()], 3), 'origin0', np.round(fr[0]['origin'], 3), 'axis0', np.round(fr[0]['axis'], 3))
print('REST', {k: np.round(v, 3).tolist() for k, v in out['rest'].items()})
