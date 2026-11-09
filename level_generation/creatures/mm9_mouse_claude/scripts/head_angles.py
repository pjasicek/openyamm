#!/usr/bin/env python3
"""Head orientation against MM9, every shared clip at 48 fps (Standing/stand, Running/run, Death/die): the world
rotation of Bone05, Bone08 and Bone06 from their rest, ours against MM9's, applied to the forward and up axes (max angle
per clip); the clips are time-scaled onto each other. The head's vertices follow these joints. Also mirror symmetry.
Usage: head_angles.py <our glb> <mm9 glb> [report.json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model


class Head:
    def __init__(self, path):
        self.m = Model(Glb(path))
        rest = self.m.skinned_positions(self.m.world({}))
        self.k = int(np.argmax([len(x[0]) for x in rest]))
        self.p0 = rest[self.k][0]
        self.joints = [self.m.glb.json['nodes'][j]['name'] for j in self.m.glb.json['skins'][0]['joints']]
        p = self.p0
        self.snout = int(np.argmax(p[:, 2]))        # glTF +Z is the head
        head = (p[:, 2] > p[self.snout, 2] - 0.045) & (p[:, 2] < p[self.snout, 2] - 0.015)
        self.top = int(np.flatnonzero(head)[np.argmax(p[head, 1] - 2 * np.abs(p[head, 0]))])

    def axes(self, clip, t):
        posed = self.m.skinned_positions(self.m.world(self.m.sample(clip, t)))[self.k][0]
        d = posed[self.snout] - posed[self.top]
        return d / np.linalg.norm(d), posed


def angle(a, b):
    return np.degrees(np.arccos(np.clip(a @ b, -1, 1)))


def rotations(h, clip, t, names):
    w = h.m.world(h.m.sample(clip, t))
    out = {}
    for n in names:
        i = next(k for k, node in enumerate(h.m.glb.json['nodes']) if node.get('name') == n)
        m = np.asarray(w[i])[:3, :3]
        u, _, vt = np.linalg.svd(m)
        out[n] = u @ vt
    return out


ours, mm9 = Head(sys.argv[1]), Head(sys.argv[2])
rep = {}
JOINTS = ('Bone05', 'Bone08', 'Bone06')
rest = {'ours': rotations(ours, 'Standing', 0.0, JOINTS), 'mm9': rotations(mm9, 'stand', 0.0, JOINTS)}
for role, src in (('Standing', 'stand'), ('Running', 'run'), ('Death', 'die')):
    Ta, Tb = ours.m.clip_times(role)[-1], mm9.m.clip_times(src)[-1]
    n = int(Ta * 48)
    worst = {j: [0.0, 0.0, 0.0] for j in JOINTS}   # snout direction, up vector, MM9 turn
    for k in range(n + 1):
        u = k / max(n, 1)
        a = rotations(ours, role, u * Ta, JOINTS)
        b = rotations(mm9, src, u * Tb, JOINTS)
        for j in JOINTS:
            da, db = a[j] @ rest['ours'][j].T, b[j] @ rest['mm9'][j].T
            f, up = np.array([0, 0, 1.0]), np.array([0, 1.0, 0])
            worst[j][0] = max(worst[j][0], angle(da @ f, db @ f))
            worst[j][1] = max(worst[j][1], angle(da @ up, db @ up))
            worst[j][2] = max(worst[j][2], angle(db @ f, f))
    rep[role] = {j: {'snout_vs_mm9': round(v[0], 2), 'up_vs_mm9': round(v[1], 2), 'mm9_turn': round(v[2], 1)}
                 for j, v in worst.items()}
p = mm9.p0
body = p[p[:, 2] > 0.0]
from scipy.spatial import cKDTree
d = cKDTree(p).query(body * [-1, 1, 1])[0]
rep['mm9_body_mirror_max_mm'] = round(float(d.max() * 1000), 2)
# ours: the surface, not the vertices (the decimated mesh has no vertex-to-vertex mirror): dense samples, mirrored
tris = np.asarray(ours.m.skinned_positions(ours.m.world({}))[ours.k][1]).reshape(-1, 3)
p = ours.p0
rng = np.random.default_rng(1)
area = np.linalg.norm(np.cross(p[tris[:, 1]] - p[tris[:, 0]], p[tris[:, 2]] - p[tris[:, 0]]), axis=1)
pick = rng.choice(len(tris), 400000, p=area / area.sum())
u, v = rng.random(len(pick)), rng.random(len(pick))
flip = u + v > 1
u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
q = p[tris[pick, 0]] + u[:, None] * (p[tris[pick, 1]] - p[tris[pick, 0]]) + v[:, None] * (p[tris[pick, 2]] - p[tris[pick, 0]])
front = q[:, 2] > 0.0
d = cKDTree(q).query(q[front] * [-1, 1, 1])[0]
rep['ours_body_mirror_surface_p99_mm'] = round(float(np.percentile(d, 99) * 1000), 2)
rep['ours_body_mirror_surface_max_mm'] = round(float(d.max() * 1000), 2)
print(json.dumps(rep, indent=1))
if len(sys.argv) > 3:
    json.dump(rep, open(sys.argv[3], 'w'), indent=1)
