#!/usr/bin/env python3
"""Follow-up 3 (2026-11-12, user on Walk2 from the side: "isnt her head like crouched too forward?"): bring the upper back, neck
and head upright, and calm the walk's arm swing, on the runtime GLB's keys (nothing else changes).

MM9's PeasantFemale walk bends the upper back at Spine2 (+11 deg) and the neck (+6 deg) forward and tips the head back
(-22 deg) so the face stays level: the head hangs ahead of the chest. Here, per clip and joint, the forward excess of the
joint's sagittal angle (its world turn about the body's lateral axis minus its parent's) over Standing's mean is removed by
a fraction k:
  loops (const): one constant correction per clip (the clip mean), so the loop's own small motion is kept as it is;
  gestures (lowpass): the positive excess low-passed (Hann window, seconds) and scaled, zero where the clip eases to the pose.
The head: const clips get one constant turn so the head's mean facing pitch is the target (chin level); gesture clips keep
the head's original world facing (the head turns back by what its parents were corrected).
Arms (const clips only, optional): the upper arm's sagittal swing relative to the chest is scaled about its centre and the
centre moved: arm(t) = centre + shift + scale * (arm(t) - centre), turned about the chest's lateral axis at the shoulder.
Afterwards the half-joint helpers of the changed joints are re-keyed (half_keys.py's rule) on the changed clips.

Usage: head_upright.py <in glb> <out glb> <params json>
params: {"Walk2": {"mode": "const", "k": {"FHP Spine2": 0.85, ...}, "head_pitch": 1.3,
                   "arms": {"scale": {"L": 1.0, "R": 0.75}, "shift": 0}}, "Fidget": {"mode": "lowpass", "window": 0.4, "taper": 0.25, "k": {...}}}"""
import copy, json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model, matrix_quaternion, quaternion_matrix
from pygltflib import GLTF2
from rig_bones import half_pairs

IN, OUT, PAR = sys.argv[1:4]
params = json.loads(Path(PAR).read_text())
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
R0 = m.world({})
X = np.array([1.0, 0, 0]); Y = np.array([0, 1.0, 0])
CHAIN = ['FHP Spine1', 'FHP Spine2', 'FHP Spine3', 'FHP Neck', 'FHP Head']
ARMS = [('FHP L UpperArm', 'FHP L Forearm'), ('FHP R UpperArm', 'FHP R Forearm')]
CHEST = 'FHP Spine3'
BRAID = 'FHP Ponytail1'


def axis_rot(ax, a):
    ax = ax / np.linalg.norm(ax); K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def lateral(W, j):
    """world lateral axis of joint j in this pose (its rest-world x carried by its turn from rest)"""
    return W[ix[j]][:3, :3] @ R0[ix[j]][:3, :3].T @ X


def sag(W, j):
    """sagittal turn of joint j from its rest, deg (+ = forward / chin down)"""
    v = W[ix[j]][:3, :3] @ R0[ix[j]][:3, :3].T @ Y
    return np.degrees(np.arctan2(v[2], v[1]))


def parent_name(j):
    return names[m.parent[ix[j]]]


def head_pitch(W):
    f = W[ix['FHP Head']][:3, :3] @ R0[ix['FHP Head']][:3, :3].T @ np.array([0, 0, 1.0])
    return np.degrees(np.arcsin(np.clip(-f[1], -1, 1)))


def arm_angle(W, u, f):
    """upper arm's sagittal swing relative to the chest, deg (- = behind)"""
    v = W[ix[f]][:3, 3] - W[ix[u]][:3, 3]
    v = (W[ix[CHEST]][:3, :3] @ R0[ix[CHEST]][:3, :3].T).T @ v
    return np.degrees(np.arctan2(v[2], -v[1]))


def braid_back(W):
    """braid end behind the upper chest in the chest's frame, cm"""
    C = W[ix[CHEST]]; Rc = C[:3, :3] @ R0[ix[CHEST]][:3, :3].T
    return -(Rc.T @ (W[ix['FHP Ponytail12']][:3, 3] - C[:3, 3]))[2] * 100


def local_sag(Ws, j):
    return np.array([sag(W, j) - sag(W, parent_name(j)) for W in Ws])


def hann(x, n):
    if n < 2: return x
    w = np.hanning(n + 2)[1:-1]; w /= w.sum(); p = n // 2
    return np.convolve(np.pad(x, (p, n - 1 - p), mode='edge'), w, mode='valid')


stand_ts = m.clip_times('Standing')
stand_W = [m.world(m.sample('Standing', t)) for t in stand_ts]
ref = {j: float(local_sag(stand_W, j).mean()) for j in CHAIN}

g = GLTF2().load(IN); blob = bytearray(g.binary_blob())


def out_view(an, node, path):
    c = next(c for c in an.channels if c.target.node == node and c.target.path == path)
    a = g.accessors[an.samplers[c.sampler].output]; v = g.bufferViews[a.bufferView]
    return (v.byteOffset or 0) + (a.byteOffset or 0), a.count


report = {}
for clip, P in params.items():
    an = next(a for a in g.animations if a.name == clip)
    ts = m.clip_times(clip)
    locs = [m.sample(clip, t) for t in ts]
    Ws = [m.world(L) for L in locs]
    k = P.get('k', {})
    corr = {}
    # gestures: the correction fades in and out over the clip's first and last `taper` seconds (smoothstep), so the clip still
    # starts and ends on its own keys where it hands over to Standing
    tt = np.asarray(ts); tp = P.get('taper', 0.25)
    e = np.clip(np.minimum(tt - tt[0], tt[-1] - tt) / max(tp, 1e-6), 0, 1); taper = e * e * (3 - 2 * e)
    for j, kj in k.items():
        ex = local_sag(Ws, j) - ref[j]
        if P['mode'] == 'const':
            corr[j] = np.full(len(ts), -kj * max(ex.mean(), 0.0))
        else:
            n = max(1, int(round(P.get('window', 0.4) * 30)))
            corr[j] = -kj * hann(np.maximum(ex, 0.0), n) * taper
    changed = set()
    # apply the chain top-down on the sampled locals
    def apply(j, a_deg):
        for i, (L, t) in enumerate(zip(locs, ts)):
            if abs(a_deg[i]) < 1e-9: continue
            W = m.world(L); pj = ix[parent_name(j)]
            Rp = W[pj][:3, :3]; Rj = W[ix[j]][:3, :3]
            Rn = axis_rot(lateral(W, parent_name(j)), np.radians(a_deg[i])) @ Rj
            trs = L.setdefault(ix[j], [p.copy() for p in m.rest[ix[j]]])
            trs[1] = matrix_quaternion(Rp.T @ Rn)
        changed.add(j)
    for j in CHAIN[:-1]:
        if j in corr: apply(j, corr[j])
    Ws1 = [m.world(L) for L in locs]
    if P['mode'] == 'const' and 'head_pitch' in P:
        hp = np.array([head_pitch(W) for W in Ws1])
        corr['FHP Head'] = np.full(len(ts), P['head_pitch'] - hp.mean())
    elif P['mode'] != 'const':
        hp0 = np.array([head_pitch(W) for W in Ws]); hp1 = np.array([head_pitch(W) for W in Ws1])
        corr['FHP Head'] = hp0 - hp1
    if 'FHP Head' in corr:
        apply('FHP Head', corr['FHP Head'])
        # the braid hangs from the back of the head; with the head back over the chest it would float behind the back (v2) or, turned
        # back by the whole head correction, sink into it (v3). Its root turns by a fraction f of the head's correction, f solved so
        # that the braid end (Ponytail12) keeps its clip's mean distance behind the upper chest
        if P.get('braid', True):
            want = np.mean([braid_back(W) for W in Ws])
            base = copy.deepcopy(locs)
            def trial(f):
                locs[:] = copy.deepcopy(base); apply(BRAID, -f * corr['FHP Head'])
                return np.mean([braid_back(m.world(L)) for L in locs]) - want
            f0, f1 = 0.0, 1.0; e0, e1 = trial(f0), trial(f1)
            for _ in range(6):
                if abs(e1 - e0) < 1e-9: break
                f0, e0, f1 = f1, e1, f1 - e1 * (f1 - f0) / (e1 - e0); e1 = trial(f1)
                if abs(e1) < 0.02: break
            corr[BRAID] = -f1 * corr['FHP Head']
    arms = P.get('arms')
    if arms:
        Ws2 = [m.world(L) for L in locs]
        for u, f in ARMS:
            side = u.split()[1]
            sc = arms.get('scale', 1.0); sc = sc.get(side, 1.0) if isinstance(sc, dict) else sc
            sh = arms.get('shift', 0.0); sh = sh.get(side, 0.0) if isinstance(sh, dict) else sh
            a = np.array([arm_angle(W, u, f) for W in Ws2]); c = 0.5 * (a.max() + a.min())
            target = c + sh + sc * (a - c)
            d = target - a
            # turn about the chest's lateral axis at the shoulder: + = forward swing, i.e. a negative turn about +x
            for i, L in enumerate(locs):
                W = m.world(L); pj = ix[parent_name(u)]
                Rn = axis_rot(lateral(W, CHEST), -np.radians(d[i])) @ W[ix[u]][:3, :3]
                trs = L.setdefault(ix[u], [p.copy() for p in m.rest[ix[u]]])
                trs[1] = matrix_quaternion(W[pj][:3, :3].T @ Rn)
            changed.add(u)
            corr[u] = d
    # half-joint helpers of the changed joints (half_keys.py's rule, on this clip's key times)
    jn = [names[j] for j in m.joints]; ibm = {n: m.inverse_binds[i] for i, n in enumerate(jn)}
    from half_keys_rule import helper_local  # noqa: E402
    Wf = [m.world(L) for L in locs]
    hl = {}
    for h, c, pn, _ in half_pairs():
        if c in changed or pn in changed:
            hl[h] = [helper_local(W, ix, ibm, c, pn) for W in Wf]
    # write rotations of the changed joints and the helpers' TRS
    for j in changed:
        o, cnt = out_view(an, ix[j], 'rotation'); assert cnt == len(ts)
        Q = np.array([locs[i][ix[j]][1] for i in range(len(ts))])
        for i in range(1, len(Q)):
            if Q[i] @ Q[i - 1] < 0: Q[i] *= -1
        blob[o:o + Q.size * 4] = Q.astype('f4').tobytes()
    for h, vals in hl.items():
        o, cnt = out_view(an, ix[h], 'translation'); assert cnt == len(ts)
        T = np.array([v[0] for v in vals]); blob[o:o + T.size * 4] = T.astype('f4').tobytes()
        o, cnt = out_view(an, ix[h], 'rotation'); assert cnt == len(ts)
        Q = np.array([v[1] for v in vals])
        for i in range(1, len(Q)):
            if Q[i] @ Q[i - 1] < 0: Q[i] *= -1
        blob[o:o + Q.size * 4] = Q.astype('f4').tobytes()
    report[clip] = {j: [round(float(v.min()), 1), round(float(v.max()), 1)] for j, v in corr.items()}
    report[clip]['helpers'] = sorted(hl)
# every output accessor edited in place must belong to one sampler only
outs = [s.output for a in g.animations for s in a.samplers]
assert len(outs) == len(set(outs)), 'shared output accessors'
g.set_binary_blob(bytes(blob)); g.save(OUT)
print('UPRIGHT', json.dumps(report))
