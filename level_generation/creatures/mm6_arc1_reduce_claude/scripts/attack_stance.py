#!/usr/bin/env python3
"""Archer stance for Attack (and Cast, which shares its accessors): the round-5 clip pins both ankles at the narrow
idle spot while the hips turn ~45 deg, so the knees twist and the right leg locks straight. Here the feet follow the
hip turn: per key, w = hip turn / peak turn (smoothstep); the left (front) foot pivots on its ankle by FRONT_PIVOT x
the turn, the right (rear) foot steps out and back to STANCE_WIDTH m from the left along the turned hip line, lifts
STEP_LIFT m mid-step and pivots by REAR_PIVOT x the turn. The pelvis drops where a leg would exceed MAX_KNEE degrees;
the legs are solved by two-bone IK with the knee over the toes. Upper body, arms, bow, arrow and timing are
untouched; the first and last keys are unchanged (w = 0). Only the existing animated accessors are rewritten
(pelvis translation, thigh/calf/foot rotations). Usage: attack_stance.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Rot
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
FRONT_PIVOT, REAR_PIVOT, STANCE_WIDTH, STEP_LIFT, MAX_KNEE = .55, .9, .21, .03, 173.
FRONT_STEP, FRONT_LIFT = .04, .015   # the left hip moves forward over the planted foot: a short lead-foot advance
src, out = sys.argv[1:3]
doc, binary = R.read_glb(src); binary = bytearray(binary)
names = [n.get('name') for n in doc['nodes']]; node = {n: i for i, n in enumerate(names)}
parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}


def view(a):
    acc = doc['accessors'][a]; bv = doc['bufferViews'][acc['bufferView']]
    k = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[acc['type']]
    o = bv.get('byteOffset', 0) + acc.get('byteOffset', 0)
    assert acc['componentType'] == 5126 and bv.get('byteStride', 4 * k) == 4 * k
    return np.frombuffer(binary, np.float32, acc['count'] * k, o).reshape(acc['count'], k), o


anim = next(a for a in doc['animations'] if a['name'] == 'Attack')
cast = next(a for a in doc['animations'] if a['name'] == 'Cast')
assert [(s['input'], s['output']) for s in anim['samplers']] == [(s['input'], s['output']) for s in cast['samplers']]
chan = {}
for c in anim['channels']:
    s = anim['samplers'][c['sampler']]; chan[(names[c['target']['node']], c['target']['path'])] = (s['input'], s['output'])
times = view(chan[('B_Pelvis', 'rotation')][0])[0][:, 0]; N = len(times)


def track(n, path):
    """Per key value of a node property (constant tracks and unanimated nodes broadcast)."""
    if (n, path) in chan:
        i, o = chan[(n, path)]; t = view(i)[0][:, 0]; v = view(o)[0]
        if len(t) == N:
            return v.copy()
        return np.array([v[min(np.searchsorted(t, x, 'right') - 1, len(v) - 1)] for x in times])
    d = {'translation': [0, 0, 0], 'rotation': [0, 0, 0, 1], 'scale': [1, 1, 1]}[path]
    return np.tile(np.array(doc['nodes'][node[n]].get(path, d), float), (N, 1))


def mat(t, q, s):
    m = np.eye(4); m[:3, :3] = Rot.from_quat(q).as_matrix() * s; m[:3, 3] = t; return m


LEGS = ['B_Pelvis'] + [f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf', 'Foot', 'Toe0')]
TRS = {n: [track(n, p) for p in ('translation', 'rotation', 'scale')] for n in LEGS}
chain = []
i = parent[node['B_Pelvis']]
while i is not None:
    chain.append(i); i = parent.get(i)
rig = np.eye(4)   # static ancestors of the pelvis (Rig and above)
for i in reversed(chain):
    n = doc['nodes'][i]
    rig = rig @ (np.array(n['matrix']).reshape(4, 4).T if 'matrix' in n else
                 mat(n.get('translation', [0, 0, 0]), n.get('rotation', [0, 0, 0, 1]), n.get('scale', [1, 1, 1])))


def world(k, trs=TRS):
    W = {'B_Pelvis': rig @ mat(*(x[k] for x in trs['B_Pelvis']))}
    for s in 'LR':
        p = 'B_Pelvis'
        for b in ('Thigh', 'Calf', 'Foot', 'Toe0'):
            n = f'B_{s}_{b}'; W[n] = W[p] @ mat(*(x[k] for x in trs[n])); p = n
    return W


up = rig[:3, :3] @ np.array([0, 1., 0]); up /= np.linalg.norm(up)   # glTF Y up through the rig transform
flat = lambda v: v - up * (v @ up)
W0 = [world(k) for k in range(N)]
pos = lambda W, n: W[n][:3, 3]


def signed(a, b):
    a, b = flat(a), flat(b); return np.arctan2(np.cross(a, b) @ up, a @ b)


turn = np.array([signed(pos(W0[0], 'B_R_Thigh') - pos(W0[0], 'B_L_Thigh'), pos(W0[k], 'B_R_Thigh') - pos(W0[k], 'B_L_Thigh'))
                 for k in range(N)])
peak = turn[np.argmax(np.abs(turn))]
w = np.clip(turn / (.95 * peak), 0, 1); w = w * w * (3 - 2 * w); w[0] = w[-1] = 0
print('hip turn peak', round(float(np.degrees(peak)), 1), 'deg; w', np.round(w, 2).tolist())
yaw = lambda a: Rot.from_rotvec(up * a)
lenT = {s: np.linalg.norm(TRS[f'B_{s}_Calf'][0][0]) * np.mean(TRS[f'B_{s}_Thigh'][2][0]) for s in 'LR'}
lenC = {s: np.linalg.norm(TRS[f'B_{s}_Foot'][0][0]) * np.mean(TRS[f'B_{s}_Calf'][2][0]) for s in 'LR'}
scale_rig = np.linalg.norm(rig[:3, 0])
lT = {s: lenT[s] * scale_rig for s in 'LR'}; lC = {s: lenC[s] * scale_rig for s in 'LR'}
dmax = {s: np.sqrt(lT[s] ** 2 + lC[s] ** 2 - 2 * lT[s] * lC[s] * np.cos(np.radians(MAX_KNEE))) for s in 'LR'}
rest_l, rest_r = pos(W0[0], 'B_L_Foot'), pos(W0[0], 'B_R_Foot')
NEW = {n: [x.copy() for x in v] for n, v in TRS.items()}
report = []
for k in range(N):
    W = W0[k]
    # foot targets (world): ankle position and rotation
    side = flat(rest_r - rest_l); side /= np.linalg.norm(side)
    ahead = flat(pos(W0[0], 'B_L_Toe0') + pos(W0[0], 'B_R_Toe0') - pos(W0[0], 'B_L_Foot') - pos(W0[0], 'B_R_Foot'))
    ahead /= np.linalg.norm(ahead)
    phase = 4 * w[k] * (1 - w[k])
    lead = rest_l + ahead * FRONT_STEP
    tgt = {'L': (rest_l + ahead * FRONT_STEP * w[k] + up * FRONT_LIFT * phase, yaw(FRONT_PIVOT * peak * w[k]))}
    stance = lead + yaw(peak).apply(side) * STANCE_WIDTH
    stance -= up * ((stance - rest_r) @ up - .0005)   # the right ankle keeps its rest height (+0.5 mm: the pivoted sole
    # dipped 0.1 mm)
    tgt['R'] = (rest_r + (stance - rest_r) * w[k] + up * STEP_LIFT * phase, yaw(REAR_PIVOT * peak * w[k]))
    # pelvis drop so both hip-ankle distances stay within MAX_KNEE
    drop = 0.
    for s in 'LR':
        h, a = pos(W, f'B_{s}_Thigh'), tgt[s][0]
        d = a - h; horiz = np.linalg.norm(flat(d)); vert = -(d @ up)
        need = vert - np.sqrt(max(dmax[s] ** 2 - horiz ** 2, 0))
        drop = max(drop, need)
    drop = max(drop, 0.)
    # pelvis translation in its parent (rig) space
    NEW['B_Pelvis'][0][k] = TRS['B_Pelvis'][0][k] + np.linalg.inv(rig)[:3, :3] @ (-up * drop)
    Wn = world(k, NEW)
    row = [f'{times[k]:.3f}', f'w {w[k]:.2f}', f'drop {drop * 1000:4.1f} mm']
    for s in 'LR':
        T, C, F = f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot'
        H, A = pos(Wn, T), tgt[s][0]
        d = A - H; dist = min(np.linalg.norm(d), (lT[s] + lC[s]) * .9999); u = d / np.linalg.norm(d)
        # knee pole: the original knee offset blended to over the toes (target foot forward) by w, so w = 0
        # reproduces the original leg
        fwd = tgt[s][1].apply(flat(pos(W, f'B_{s}_Toe0') - pos(W, F))); fwd /= np.linalg.norm(fwd)
        ko = pos(W, C) - pos(W, T); la = pos(W, F) - pos(W, T); ko = ko - la * (ko @ la) / (la @ la)
        pole = ko / max(np.linalg.norm(ko), 1e-9) * (1 - w[k]) + fwd * w[k]
        pole = pole - u * (pole @ u); pole /= np.linalg.norm(pole)
        a = (lT[s] ** 2 - lC[s] ** 2 + dist ** 2) / (2 * dist); hgt = np.sqrt(max(lT[s] ** 2 - a ** 2, 0))
        K = H + u * a + pole * hgt
        # thigh: align the old thigh direction and bend plane to the new ones (world rotation), then back to local
        Kold, Aold, Hold = pos(W, C), pos(W, F), pos(W, T)
        t_old, t_new = (Kold - Hold) / np.linalg.norm(Kold - Hold), (K - H) / np.linalg.norm(K - H)
        n_old = np.cross(Kold - Hold, Aold - Kold); n_new = np.cross(K - H, A - K)
        r1 = Rot.align_vectors([t_new, n_new / np.linalg.norm(n_new)], [t_old, n_old / np.linalg.norm(n_old)],
                               weights=[1e6, 1])[0]
        Rt = r1 * Rot.from_matrix(Wn[T][:3, :3] / np.linalg.norm(Wn[T][:3, :3], axis=0))
        Rp = Rot.from_matrix(Wn['B_Pelvis'][:3, :3] / np.linalg.norm(Wn['B_Pelvis'][:3, :3], axis=0))
        NEW[T][1][k] = (Rp.inv() * Rt).as_quat()
        Wn = world(k, NEW)
        # calf: minimal rotation of its direction onto the new knee -> ankle
        cd = pos(Wn, F) - pos(Wn, C); cn = A - pos(Wn, C)
        r2 = Rot.align_vectors([cn / np.linalg.norm(cn)], [cd / np.linalg.norm(cd)])[0]
        Rc = r2 * Rot.from_matrix(Wn[C][:3, :3] / np.linalg.norm(Wn[C][:3, :3], axis=0))
        NEW[C][1][k] = (Rt.inv() * Rc).as_quat()
        Wn = world(k, NEW)
        # foot: original world rotation turned by the pivot
        Rf = tgt[s][1] * Rot.from_matrix(W[F][:3, :3] / np.linalg.norm(W[F][:3, :3], axis=0))
        NEW[F][1][k] = (Rc.inv() * Rf).as_quat()
        Wn = world(k, NEW)
        err = np.linalg.norm(pos(Wn, F) - A)
        kd = np.degrees(np.arccos(np.clip(((pos(Wn, T) - pos(Wn, C)) @ (pos(Wn, F) - pos(Wn, C))) /
                                           (np.linalg.norm(pos(Wn, T) - pos(Wn, C)) * np.linalg.norm(pos(Wn, F) - pos(Wn, C))), -1, 1)))
        row.append(f'{s}: knee {kd:5.1f} ankle err {err * 1000:4.1f} mm')
    report.append(' '.join(row))
print('\n'.join(report[::4] + [report[-1]]))
# keep the quaternion sign continuous, then write the animated accessors in place
for n, path in [('B_Pelvis', 'translation')] + [(f'B_{s}_{b}', 'rotation') for s in 'LR' for b in ('Thigh', 'Calf', 'Foot')]:
    i, o = chan[(n, path)]
    assert len(view(i)[0]) == N, (n, path)
    v = NEW[n][0 if path == 'translation' else 1].astype(np.float32)
    if path == 'rotation':
        for k in range(1, N):
            if v[k] @ v[k - 1] < 0:
                v[k] = -v[k]
    arr, off = view(o); assert arr.shape == v.shape
    binary[off:off + v.nbytes] = v.tobytes()
    for k in (0, N - 1):   # boundary keys are unchanged
        assert np.allclose(np.abs(v[k] @ TRS[n][1][k]) if path == 'rotation' else 1, 1, atol=1e-5) and \
            (path == 'rotation' or np.allclose(v[k], TRS[n][0][k], atol=1e-6)), (n, path, k)
R.write_glb(out, doc, bytes(binary))
print('WROTE', out)
