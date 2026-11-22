"""Anatomy of the Smart Topology return (work/pieces.npz, piece numbers from prep.py, checked against
review/pieces_*.png and the contact gaps) and the joint positions read from the mesh: ball-joint centres for hips,
knees, shoulders and elbows, closest-point junctions between consecutive pieces elsewhere. Writes work/joints.json
(bones: head, tail, parent, pieces). Run with system python (numpy, scipy)."""
import json, os
import numpy as np
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = np.load(os.path.join(HERE, 'work', 'pieces.npz')); co, lab = d['co'], d['label']
P = {i: co[lab == i] for i in range(lab.max() + 1)}
C = {i: p.mean(0) for i, p in P.items()}


def ball(i):
    """Centre of a near-spherical ball piece: the centre of its bounding box."""
    return (P[i].min(0) + P[i].max(0)) / 2


def junction(a, b):
    t = cKDTree(P[b]); dd, j = t.query(P[a]); k = int(dd.argmin())
    return (P[a][k] + P[b][j[k]]) / 2


def far(i, frm):
    return P[i][np.argmax(np.linalg.norm(P[i] - frm, axis=1))]


MOUTH_BEADS = [39, 40, 43, 44, 45, 46, 47, 49, 50, 51]
bones = {}


def bone(name, head, tail, parent, pieces):
    bones[name] = {'head': [float(x) for x in head], 'tail': [float(x) for x in tail], 'parent': parent,
                   'pieces': [int(p) for p in pieces]}


body_c = C[7]
bone('Body', body_c, body_c + np.array([0, 0, 0.08]), None, [7])
# 6 and 7 overlap over a wide band and the closest pair sits at the front rim: pivot the abdomen just under the hip
# ring's centre and the thorax on the ring's top instead
jab = body_c + np.array([0, 0.02, -0.05])
bone('Abdomen', jab, P[6][np.argmin(P[6][:, 2])], 'Body', [6])
jth = np.array([0, body_c[1] - 0.03, P[7][:, 2].max() - 0.06]); neck = junction(1, 0)
bone('Thorax', jth, neck, 'Body', [0])
bone('Head', neck, C[24], 'Thorax', [1, 10, 21, 12, 23, 11, 24])
mouth = C[15]
bone('Mouth', mouth + np.array([0, 0.02, 0]), mouth + np.array([0, -0.06, 0]), 'Head', [15] + MOUTH_BEADS)
for s, ant, knob in (('L', 18, 54), ('R', 20, 55)):
    root = junction(ant, 24)
    bone(f'Antenna_{s}', root, C[knob], 'Head', [ant, knob])
for s, sh, up, el, fa, hk in (('L', 42, 25, 53, 17, 9), ('R', 38, 22, 52, 19, 8)):
    wrist = junction(fa, hk)
    bone(f'UpperArm_{s}', ball(sh), ball(el), 'Thorax', [sh, up])
    bone(f'ForeArm_{s}', ball(el), wrist, f'UpperArm_{s}', [el, fa])
    bone(f'Hook_{s}', wrist, far(hk, wrist), f'ForeArm_{s}', [hk])
# legs: 1 front, 2 rear; (hip ball, femur, knee ball, shin, foot, extra pieces on the shin)
LEGS = {'L1': (31, 36, 29, 13, 2, []), 'R1': (33, 37, 30, 16, 3, []),
        'L2': (35, 41, 32, 26, 4, [48]), 'R2': (34, 28, 27, 14, 5, [])}
legs = {}
for k, (hip, fem, knee, shin, foot, extra) in LEGS.items():
    ankle = junction(shin, foot)
    f = P[foot]
    horiz = f.copy(); horiz[:, 2] = ankle[2]
    toe = f[np.argmax(np.linalg.norm(horiz - ankle, axis=1))]
    bone(f'Thigh_{k}', ball(hip), ball(knee), 'Body', [hip, fem])
    bone(f'Shin_{k}', ball(knee), ankle, f'Thigh_{k}', [knee, shin] + extra)
    bone(f'Foot_{k}', ankle, np.array([toe[0], toe[1], ankle[2]]), f'Shin_{k}', [foot])
    legs[k] = {'chain': [f'Thigh_{k}', f'Shin_{k}', f'Foot_{k}'], 'ankle': ankle.tolist(),
               'foot_min_z': float(f[:, 2].min())}
used = sorted(p for b in bones.values() for p in b['pieces'])
assert used == list(range(lab.max() + 1)), set(range(lab.max() + 1)) ^ set(used)
for n, b in bones.items():
    print(f"{n:12s} {np.round(b['head'], 3)} -> {np.round(b['tail'], 3)} parent {b['parent']} pieces {b['pieces']}")
json.dump({'bones': bones, 'legs': legs}, open(os.path.join(HERE, 'work', 'joints.json'), 'w'), indent=1)
