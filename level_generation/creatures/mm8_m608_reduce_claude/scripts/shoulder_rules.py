#!/usr/bin/env python3
"""The creature's shoulder contract (mm8_m608_codex/scripts/shoulder_audit.py) on a GLB, per body colour/shadow mesh:
no face mixes arm (UpperArm/Forearm/Hand) and torso (Chest/Waist/Neck/Head) influences, and every front shoulder-cap
vertex is fully on its UpperArm bone. Usage: shoulder_rules.py <glb>"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes
d, raw = read_glb(Path(sys.argv[1]))
def val(i):
    a = d['accessors'][i]
    x = np.frombuffer(accessor_bytes(d, raw, i), dtype={5121: 'u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[a['componentType']]).reshape(a['count'], -1)
    return x / {5121: 255., 5123: 65535.}[a['componentType']] if a.get('normalized') else x
node = next(n for n in d['nodes'] if n.get('name') == 'Juggernaut'); names = [d['nodes'][j]['name'] for j in d['skins'][node['skin']]['joints']]
arm = np.array([n.startswith(('UpperArm_', 'Forearm_', 'Hand_')) for n in names]); torso = np.array([n in ('Chest', 'Waist', 'Neck', 'Head') for n in names])
main = d['meshes'][node['mesh']]; ids = [node['mesh']] + main['extras']['openyamm_lods'] + main['extras']['openyamm_shadow_lods']
for mi in ids:
    p = d['meshes'][mi]['primitives'][0]; J = val(p['attributes']['JOINTS_0']).astype(int); W = val(p['attributes']['WEIGHTS_0']); I = val(p['indices']).reshape(-1, 3).astype(int)
    P = val(p['attributes']['POSITION']); bl = np.stack([P[:, 0], -P[:, 2], P[:, 1]], 1)
    on = W > 1e-6; va = (arm[J] & on).any(1); vt = (torso[J] & on).any(1)
    mixed = int((va[I].any(1) & vt[I].any(1)).sum())
    bad = 0; ncap = 0
    for side, s in (('L', 1), ('R', -1)):
        cap = (bl[:, 0] * s > .16) & (bl[:, 0] * s < .245) & (bl[:, 2] > .73) & (bl[:, 2] < .81) & (bl[:, 1] < .035)
        k = names.index('UpperArm_' + side); full = ((J == k) & (W > .9999)).any(1)
        ncap += int(cap.sum()); bad += int((cap & ~full).sum())
    print(d['meshes'][mi]['name'], 'tris', len(I), 'arm-torso faces', mixed, 'cap verts', ncap, 'not rigid', bad)
