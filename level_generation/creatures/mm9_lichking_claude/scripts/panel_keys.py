#!/usr/bin/env python3
"""Front and back panels: link chains XPanelF1-4 / XPanelB1-4 under the Pelvis, keyed per clip on its own keys.
Base swing = MM9's own cloth motion (Box01 > Box14 on the front, Box17 on the back), read as the sagittal angle of the hanging direction in the Pelvis frame. Then, in the Pelvis's bind frame, each link takes the
least extra angle that keeps every leg, boot, greave and flap point within the panel's width on the inner side by MARGIN, top link first (the rope lies on the hull). Floor: no link tip under FLOOR.
Curves: running maximum (HOLD) and Gaussian (SIGMA) on the clip's keys, circular on loops, never per frame. Args: <in glb> <out glb> <asm npz with comp, part of the uv or plain mesh> <report json>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model, matrix_quaternion
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
from rig_bones import PANELS, panel_bones
IN, OUT, NPZ, REP = sys.argv[1:5]
MARGIN, HOLD, SIGMA, WIDTH, MAXBEND = 0.022, 0.12, 0.04, 0.115, np.radians(80)
MAXA = np.radians(115); FLOOR = 0.02; TIP = 0.20
CLIP_FLOOR = {'Death': -0.075, 'Death2': -0.075, 'Dead': -0.075}      # the floor pass runs later and lifts the corpse by about 9.4 cm
LOOPS = ('Standing', 'Walking', 'Running', 'Backpedal', 'BackpedalRun')
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in m.joints]; ibm = {n: m.inverse_binds[i] for i, n in enumerate(jn)}
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def add(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g.accessors) - 1
D = np.load(NPZ); comp = D['comp']; pn = [str(x) for x in D['names']]
OB = {'F': ('legs', 'boots', 'greaves', 'flapF', 'shoes'), 'B': ('legs', 'boots', 'greaves', 'flapB', 'shoes')}
PEL = 'Bip01 Pelvis'; ip = ix[PEL]; Ibp = ibm[PEL]; Rb = np.linalg.inv(Ibp)[:3, :3]
w0 = m.world({})
pr = m.primitives
def skinned(w):
    return np.vstack([r[0] for r in m.skinned_positions(w)[:len(pr)]])
# which vertices: the GLB splits by material; the mesh npz has per-vertex comp in the same concatenated order only for the uv npz. Rebuild from weights instead:
J = np.vstack([p['joints'] for p in pr]); W_ = np.vstack([p['weights'] for p in pr])
legb = [i for i, n in enumerate(jn) if any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe0'))]
legw = (np.isin(J, legb) * W_).sum(1)
ob_v = np.where(legw > 0.45)[0]
P0 = skinned(w0)
print('obstacle verts', len(ob_v), 'of', len(P0))
Hz = {k: np.array(PANELS[k]) for k in PANELS}
R = json.load(open(HERE / 'work/rig.json')); Py = R['panel_y']
HANG = np.array([0.0, -1.0, 0.0])
def hang_angle(Rrel, Rpar0, fwd):
    """sagittal angle of the hanging direction under a local rotation change"""
    h = Rpar0.T @ HANG; v = Rpar0 @ (Rrel @ h)
    return np.arctan2(v[2] * fwd, -v[1])
def rotx(a):
    c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
report = {}
for an in g.animations:
    ch = next(c for c in an.channels if names[c.target.node] == PEL)
    a = g.accessors[an.samplers[ch.sampler].input]; bv = g.bufferViews[a.bufferView]; o = (bv.byteOffset or 0) + (a.byteOffset or 0)
    ts = np.frombuffer(bytes(blob[o:o + 4 * a.count]), 'f4').copy(); tin = an.samplers[ch.sampler].input
    n = len(ts); loop = an.name in LOOPS
    res = {}
    wbs = [m.world(m.sample(an.name, float(t))) for t in ts]
    for k, fwd in (('F', 1.0), ('B', -1.0)):
        L = np.diff(np.r_[Hz[k], TIP]) * -1.0; nl = len(L)
        base = np.zeros((n, nl)); need = np.zeros((n, nl))
        for f, w in enumerate(wbs):
            Sp = w[ip] @ Ibp
            if k == 'F':
                l1 = np.linalg.inv(w0[ix['Bip01 Pelvis']]) @ w0[ix['Box01']]; c1 = np.linalg.inv(w[ip]) @ w[ix['Box01']]
                r1 = c1[:3, :3] @ l1[:3, :3].T; a1 = hang_angle(r1, w0[ip][:3, :3], fwd)
                l2 = np.linalg.inv(w0[ix['Box01']]) @ w0[ix['Box14']]; c2 = np.linalg.inv(w[ix['Box01']]) @ w[ix['Box14']]
                r2 = c2[:3, :3] @ l2[:3, :3].T; a2 = hang_angle(r2, w0[ix['Box01']][:3, :3], fwd)
                base[f] = [a1, a1, a1 + a2, a1 + a2]
            else:
                l1 = np.linalg.inv(w0[ip]) @ w0[ix['Box17']]; c1 = np.linalg.inv(w[ip]) @ w[ix['Box17']]
                a1 = hang_angle(c1[:3, :3] @ l1[:3, :3].T, w0[ip][:3, :3], fwd); base[f] = [a1 * .7, a1 * .85, a1, a1]
            P = skinned(w)[ob_v]
            Q = (np.linalg.inv(Sp) @ np.c_[P, np.ones(len(P))].T).T[:, :3]       # bind frame of the pelvis
            Rp = Sp[:3, :3]; tilt = np.degrees(np.arccos(np.clip((Rp @ np.array([0, 1.0, 0]))[1], -1, 1)))
            q = Q[np.abs(Q[:, 0]) < (WIDTH if (tilt < 40 or an.name == 'Dead') else 0.075)]        # lying down, cloth falls between the legs, it does not ride a raised thigh
            def droop(a_):
                # gravity: MM9's swing never lifts a link above horizontal
                cand = np.radians(np.arange(-115, 116, 5.0)); y = (Rp @ np.c_[np.zeros(len(cand)), -np.cos(cand), np.sin(cand) * fwd].T).T[:, 1]
                ok_ = cand[y <= 0.02]
                return float(ok_[np.argmin(np.abs(ok_ - a_))]) if len(ok_) else a_
            pz, py = Py[k] * -1.0, Hz[k][0]                                       # hinge: Blender y -> glTF -z
            prev = 0.0; ang = np.zeros(nl)
            cur = np.array([py, pz])                                              # (up, z)
            for i in range(nl):
                d = q[:, [1, 2]] - cur                                            # (up, z) from this hinge
                down, out = -d[:, 0], d[:, 1] * fwd
                dist = np.hypot(down, out)
                sel = (down > 0.0) & (dist < L[i] + 0.09) & (dist > 0.03)
                a_i = droop(float(np.clip(base[f, i], -MAXA, MAXA)))
                if sel.any():
                    aa = np.arctan2(out[sel], down[sel]) + np.arcsin(np.minimum(MARGIN / dist[sel], 1.0))
                    a_i = max(a_i, float(aa.max()))
                a_i = float(np.clip(a_i, prev - MAXBEND, prev + MAXBEND)); a_i = min(a_i, MAXA)
                ang[i] = a_i; prev = a_i
                cur = cur + L[i] * np.array([-np.cos(a_i), np.sin(a_i) * fwd])
            need[f] = ang
        A = need.copy()
        mode = 'wrap' if loop else 'nearest'
        dt = np.median(np.diff(ts)) if n > 1 else 1 / 30
        for i in range(nl):
            A[:, i] = maximum_filter1d(A[:, i], max(1, int(round(HOLD / dt)) | 1), mode=mode)
            A[:, i] = gaussian_filter1d(A[:, i], SIGMA / dt, mode=mode)
        # floor: the chain must not go under it (clips that lie down)
        for f, w in enumerate(wbs):
            Sp = w[ip] @ Ibp; cur = np.array([Hz[k][0], Py[k] * -1.0])
            for i in range(nl):
                for _ in range(12):
                    tip = cur + L[i] * np.array([-np.cos(A[f, i]), np.sin(A[f, i]) * fwd])
                    wy = (Sp @ np.r_[0, tip[0], tip[1], 1])[1]
                    if wy >= CLIP_FLOOR.get(an.name, FLOOR): break
                    wy0 = (Sp @ np.r_[0, cur[0], cur[1], 1])[1]
                    # turn towards whichever side raises the tip
                    t2 = cur + L[i] * np.array([-np.cos(A[f, i] + 0.05), np.sin(A[f, i] + 0.05) * fwd])
                    up = (Sp @ np.r_[0, t2[0], t2[1], 1])[1] > wy
                    A[f, i] += 0.09 if up else -0.09
                cur = cur + L[i] * np.array([-np.cos(A[f, i]), np.sin(A[f, i]) * fwd])
        for i in range(nl): A[:, i] = gaussian_filter1d(A[:, i], SIGMA / dt, mode=mode)
        res[k] = float(np.degrees(np.abs(A).max())); res[k + '_base'] = float(np.degrees(np.abs(base).max()))
        # keys: each link's rotation relative to the previous, about the pelvis-frame X (panel frames = pelvis bind frame)
        bones = panel_bones(k)
        an.channels = [c for c in an.channels if names[c.target.node] not in bones]
        for i, b in enumerate(bones):
            rel = A[:, i] - (A[:, i - 1] if i else 0.0)
            Q = np.zeros((n, 4))
            q0 = np.array(doc['nodes'][ix[b]].get('rotation', [0, 0, 0, 1]), float)
            for f in range(n):
                Rl = Rb.T @ rotx(-rel[f] * fwd) @ Rb
                Rrest = np.eye(3) if i else None
                Rf = Rl if i else Rl
                Q[f] = matrix_quaternion(Rf)
            for f in range(1, n):
                if Q[f] @ Q[f - 1] < 0: Q[f] *= -1
            s = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(Q, 'VEC4'), interpolation='LINEAR'))
            an.channels.append(AnimationChannel(sampler=s, target=AnimationChannelTarget(node=ix[b], path='rotation')))
    report[an.name] = {k: round(v, 1) for k, v in res.items()}
    print('PANEL', an.name, report[an.name], flush=True)
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
json.dump(report, open(REP, 'w'), indent=0)
