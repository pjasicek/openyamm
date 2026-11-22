"""Anatomy and joints of the scorpion's Smart Topology return (work/pieces.npz from prep.py; piece numbers checked
against review/pieces_*.png). 17 closed pieces: 0 body + tail, 1/2 left/right pedipalp with its claw (one piece each),
3-10 the eight walking legs (one piece each, no segment breaks), 11/12/13/16 the four chelicerae, 14/15 the eyes.
Joints are read from the mesh: leg and pedipalp centrelines from geodesic-distance bins away from their junction with
the body (knee = the leg's highest point, ankle = the strongest downward turn after it); the tail joints are the
constrictions between its five segments and the bulb (review/zoom_tail_side.png, read on the 5 cm grid); the movable
claw finger is the front finger, found geodesically from its tip.

Weights (work/weights.npz, rigid exoskeleton with ~1 cm blends at joints): each vertex may only use its piece's bones;
among those it takes exp(-(d_i - d_min) / 0.008) over the distances d_i to the bone segments, two largest kept and
normalised; the front claw finger region (geodesic) goes to Finger_s with a 4 cm ramp at its base.
Writes work/joints.json (bones: head, tail, parent) and work/weights.npz (bone names, per-vertex index/weight pairs).
Run with system python (numpy, scipy)."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo

HERE = geo.HERE
co, lab = geo.co, geo.lab
bones = {}


def bone(name, head, tail, parent):
    bones[name] = {'head': [float(x) for x in head], 'tail': [float(x) for x in tail], 'parent': parent}


# ---- body and tail (piece 0) ---------------------------------------------------------------------------------
bone('Body', (0, 0.0, 0.18), (0, -0.14, 0.18), None)
bone('Abdomen', (0, 0.36, 0.19), (0, 0.70, 0.25), 'Body')
TAIL = [(0.70, 0.30), (0.68, 0.457), (0.653, 0.617), (0.52, 0.70), (0.353, 0.763), (0.173, 0.723)]
for k in range(5):
    (y0, z0), (y1, z1) = TAIL[k], TAIL[k + 1]
    bone(f'Tail{k + 1}', (0, y0, z0), (0, y1, z1), 'Abdomen' if k == 0 else f'Tail{k}')
idx0 = geo.piece(0)
hi = idx0[co[idx0, 2] > 0.45]
STING = co[hi[np.argmin(co[hi, 1])]]
bone('Stinger', (0, *TAIL[-1]), STING, 'Tail5')

# ---- walking legs: L = +X (the creature's left, forward -Y); 1 front .. 4 rear --------------------------------
LEGS = {'L1': 9, 'R1': 10, 'L2': 7, 'R2': 5, 'L3': 6, 'R3': 8, 'L4': 3, 'R4': 4}
legs = {}
for k, p in LEGS.items():
    a, _, _ = geo.junction(p, 0)
    d = geo.gdist([a]); idx = geo.piece(p)
    cl = np.array([c for _, c, _ in geo.centreline(idx, d, nb=20)])
    hip = cl[0]
    tipv = idx[np.argmax(np.linalg.norm(co[idx] - hip, axis=1))]
    tip = co[tipv]
    ik = int(np.argmax(cl[:, 2]))
    knee = cl[ik]
    best, ia = -1, ik + 2
    for i in range(ik + 1, len(cl) - 2):
        u = cl[i] - cl[i - 1]; v = cl[i + 1] - cl[i]
        ang = np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1))
        if v[2] < 0 and ang > best:
            best, ia = ang, i
    ankle = cl[ia]
    bone(f'Femur_{k}', hip, knee, 'Body')
    bone(f'Tibia_{k}', knee, ankle, f'Femur_{k}')
    bone(f'Tarsus_{k}', ankle, tip, f'Tibia_{k}')
    legs[k] = {'piece': p, 'chain': [f'Femur_{k}', f'Tibia_{k}', f'Tarsus_{k}'], 'tip': tip.tolist(),
               'tip_vertex': int(tipv), 'tip_z': float(tip[2])}

# ---- pedipalps ----------------------------------------------------------------------------------------------
claws = {}
FINGER = {}
for s, p in (('L', 1), ('R', 2)):
    a, _, _ = geo.junction(p, 0)
    d = geo.gdist([a]); idx = geo.piece(p)
    cl = geo.centreline(idx, d, nb=24)
    sv = np.array([x for x, _, _ in cl]); cv = np.array([c for _, c, _ in cl])
    at = lambda s0: cv[int(np.argmin(np.abs(sv - s0)))]
    shoulder, elbow, wrist = cv[0], at(0.54), at(0.97)
    # finger tips: the front finger tip is the farthest point from the root; the back finger tip is the vertex
    # spatially nearest to it among the vertices far from it along the surface
    t1 = idx[np.argmax(d[idx])]
    dF = geo.gdist([t1])
    far = idx[dF[idx] > 0.15]
    t2 = far[np.argmin(np.linalg.norm(co[far] - co[t1], axis=1))]
    dB = geo.gdist([t2])
    # the front finger: nearer its own tip than the back tip along the surface and within 0.32 m of geodesic
    # distance from its tip (measured: the centroid's radius jumps into the palm there); 6 cm ramp at its base
    reg = idx[(dF[idx] < dB[idx]) & (dF[idx] < 0.32)]
    wf = np.clip((0.31 - dF[reg]) / 0.06, 0, 1)
    fbase = co[reg[dF[reg] > 0.27]].mean(0)
    bset = idx[(dB[idx] < dF[idx]) & (dB[idx] > 0.27) & (dB[idx] < 0.32)]
    bbase = co[bset].mean(0)
    Lf = 0.32
    palm = co[idx[(co[idx, 1] < wrist[1] - 0.03) & (dF[idx] > 0.34) & (dB[idx] > 0.34)]].mean(0)
    n = np.cross(co[t1] - fbase, co[t2] - bbase); n /= np.linalg.norm(n)
    bone(f'Arm1_{s}', shoulder, elbow, 'Body')
    bone(f'Arm2_{s}', elbow, wrist, f'Arm1_{s}')
    bone(f'Chela_{s}', wrist, palm + (palm - wrist) * 0.6, f'Arm2_{s}')
    bone(f'Finger_{s}', fbase, co[t1], f'Chela_{s}')
    FINGER[s] = (reg, wf)
    claws[s] = {'piece': p, 'front_tip': co[t1].tolist(), 'back_tip': co[t2].tolist(), 'finger_base': fbase.tolist(),
                'palm': palm.tolist(), 'hinge_normal': n.tolist(), 'finger_len': Lf,
                'finger_vertices': int((wf > 0).sum())}
    print(f'CLAW {s} shoulder {np.round(shoulder, 3)} elbow {np.round(elbow, 3)} wrist {np.round(wrist, 3)} palm '
          f'{np.round(palm, 3)} front tip {np.round(co[t1], 3)} back tip {np.round(co[t2], 3)} base {np.round(fbase, 3)} '
          f'L {Lf:.3f} n {np.round(n, 2)}')

# ---- weights ------------------------------------------------------------------------------------------------
ALLOWED = {0: ['Body', 'Abdomen', 'Tail1', 'Tail2', 'Tail3', 'Tail4', 'Tail5', 'Stinger']}
for k, p in LEGS.items():
    ALLOWED[p] = legs[k]['chain']
for s, p in (('L', 1), ('R', 2)):
    ALLOWED[p] = [f'Arm1_{s}', f'Arm2_{s}', f'Chela_{s}']
RIGID = {11: 'Body', 12: 'Body', 13: 'Body', 16: 'Body', 14: 'Body', 15: 'Body'}
names = list(bones)
NI = {n: i for i, n in enumerate(names)}


def seg_dist(P, a, b):
    a = np.array(a); b = np.array(b); ab = b - a
    t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


W = np.zeros((len(co), len(names)), np.float32)
for p in range(lab.max() + 1):
    idx = geo.piece(p)
    if p in RIGID:
        W[idx, NI[RIGID[p]]] = 1.0
        continue
    al = ALLOWED[p]
    if p == 0:
        # trunk (spine segment) against the tail bones by distance; the trunk share split Body/Abdomen by y
        al = ['Trunk'] + al[2:]
        segs = [((0, -0.55, 0.18), (0, 0.70, 0.25))] + [(bones[n]['head'], bones[n]['tail']) for n in al[1:]]
    else:
        segs = [(bones[n]['head'], bones[n]['tail']) for n in al]
    D = np.stack([seg_dist(co[idx], a, b) for a, b in segs], 1)
    E = np.exp(-(D - D.min(1, keepdims=True)) / 0.008)
    E /= E.sum(1, keepdims=True)
    for j, n in enumerate(al):
        if n == 'Trunk':
            t = np.clip((co[idx, 1] - 0.30) / 0.12, 0, 1); t = t * t * (3 - 2 * t)
            W[idx, NI['Body']] = E[:, j] * (1 - t); W[idx, NI['Abdomen']] = E[:, j] * t
        else:
            W[idx, NI[n]] = E[:, j]
for s, (reg, wf) in FINGER.items():
    W[reg] *= (1 - wf)[:, None]
    W[reg, NI[f'Finger_{s}']] = wf
# keep two largest influences, normalise
order = np.argsort(-W, 1)[:, :2]
top = np.take_along_axis(W, order, 1)
top /= top.sum(1, keepdims=True)
np.savez(os.path.join(HERE, 'work', 'weights.npz'), names=np.array(names), index=order, weight=top)
for n, b in bones.items():
    print(f"BONE {n:11s} {np.round(b['head'], 3)} -> {np.round(b['tail'], 3)} parent {b['parent']}")
dom = np.array(names)[order[:, 0]]
print('DOMINANT', {n: int((dom == n).sum()) for n in names})
json.dump({'bones': bones, 'legs': legs, 'claws': claws}, open(os.path.join(HERE, 'work', 'joints.json'), 'w'),
          indent=1)
