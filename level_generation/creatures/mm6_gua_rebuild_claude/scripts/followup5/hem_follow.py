#!/usr/bin/env python3
"""Mail hem in the gaits (follow-up 5, user 2026-11-12: "the hem flares like a skirt and the legs pass through it").

Cause: the hem hangs on six rigid hinges at the belt (rig_gua.py) keyed by skirt_keys.py. With a running maximum over
0.17 s, a 4-6 cm margin and 85 % of the neighbours' swing, all six stood at 58-68 deg through the whole of Walking, Walk2,
Jog and Running: a bell. A rigid hinge at the belt cannot follow a thigh anyway: the knee rises under the front panel
and the flexing thigh's front rolls up into the band under the belt, so the thighs still came through (the "cyan blob",
painted through the trousers' mail-painted top, was this).

Fix: the mail follows the thighs, as a tunic does, in those four clips only.
  * Eight follow bones are added, all keyed to their rest (identity) in every other clip, so every other clip deforms
    exactly as before: `Skirt_XX_T` (child of each hinge, rest = the hinge) and `Skirt_Band_L/R` (children of Bip01 Spine,
    rest = Spine). In the four gaits each is keyed to move rigidly with the thigh on its side (FL/SL/BL and the left band
    follow the left thigh).
  * The mail below the belt hands a share of its hinge weight to the hinge's follow bone and of its Spine weight to the
    band bone of its side: 0 at the hinge line, ALPHA at DEPTH below it and deeper, every LOD and shadow mesh.
  * In those four clips the hinges start at rest and swing (any direction, along the face normal) only where a thigh is
    still outside the cloth at a 60 fps pose (skirt_gate.py's test), then a 3-frame hold and a light blur.
Args: <in glb> <out glb> [report json]"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree
from glbtool import Glb, Model, repack
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared'))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared' / 'floor'))
from detached_parts_audit import closest_on_triangles  # noqa: E402
from glb_pose import matrix_quaternion, slerp  # noqa: E402

IN, OUT = sys.argv[1:3]
GAITS = ('Walking', 'Walk2', 'Jog', 'Running', 'Standing', 'Fidget', 'Attack', 'Attack2')
BETA, MAXDEG, MARGIN = 0.7, 45.0, 0.006
BAND_STEP, BAND_LEVELS, BAND_MAX = 0.03, 3, 0.05   # band rows every ~3 cm under the hinge line; push at most 5 cm
RING = ['Skirt_FR', 'Skirt_FL', 'Skirt_SL', 'Skirt_BL', 'Skirt_BR', 'Skirt_SR']
g = Glb(IN); doc = g.json
names = [n.get('name') for n in doc['nodes']]
skin = doc['skins'][0]
SP = names.index('Bip01 Spine')
THIGH = {'L': names.index('Bip01 L Thigh'), 'R': names.index('Bip01 R Thigh')}

jn = [names[j] for j in skin['joints']]

# ---- band bones: the mail's Spine share under the belt (no new influence, so every other clip deforms as before) ----
_w = Model(g).world({})
HINGE_Y = float(np.mean([_w[names.index(n)][1, 3] for n in RING])); HIP_Z = float(_w[THIGH['L']][2, 3])
BAND = {}                                                           # node -> (side L/C/R, level, front/back)
ibm = g.accessor(skin['inverseBindMatrices']).reshape(-1, 16)
sp_j = jn.index('Bip01 Spine'); sk_j = [jn.index(n) for n in RING]
for side in 'LCR':
    for lv in range(1, BAND_LEVELS + 1):
        for fb in 'FB':
            nm = f'Skirt_Band_{side}{lv}{fb}'; assert nm not in names
            doc['nodes'].append({'name': nm}); ni = len(doc['nodes']) - 1; names.append(nm)
            doc['nodes'][SP].setdefault('children', []).append(ni)
            skin['joints'].append(ni); ibm = np.r_[ibm, ibm[sp_j][None]]; BAND[ni] = (side, lv, fb)
skin['inverseBindMatrices'] = g.append_accessor(ibm.astype(np.float32), 'MAT4')
jn = [names[j] for j in skin['joints']]
done = {}; moved = 0
for me in doc['meshes']:
    for pr in me['primitives']:
        a = pr['attributes']; key = (a['POSITION'], a['JOINTS_0'])
        if key not in done:
            P = g.accessor(a['POSITION']); J0 = g.accessor(a['JOINTS_0']).astype(np.uint8)
            W0 = g.accessor(a['WEIGHTS_0'])
            sw = (np.isin(J0, sk_j) * W0).sum(1)
            lv = np.clip(np.round((HINGE_Y - P[:, 1]) / BAND_STEP), 0, BAND_LEVELS).astype(int)
            side = np.where(P[:, 0] > 0.02, 'L', np.where(P[:, 0] < -0.02, 'R', 'C'))
            fb = np.where(P[:, 2] > HIP_Z, 'F', 'B')
            Jn = J0.copy()
            for v in np.where((sw > 0.01) & (lv > 0))[0]:
                for k in range(4):
                    if J0[v, k] == sp_j and W0[v, k] > 0:
                        Jn[v, k] = jn.index(f'Skirt_Band_{side[v]}{lv[v]}{fb[v]}'); moved += 1
            view = doc['bufferViews'][doc['accessors'][a['JOINTS_0']]['bufferView']]
            g.bin += b'\0' * (-len(g.bin) % 4)
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(g.bin), 'byteLength': Jn.nbytes}); g.bin += Jn.tobytes()
            acc = dict(doc['accessors'][a['JOINTS_0']]); acc['bufferView'] = len(doc['bufferViews']) - 1; acc.pop('byteOffset', None)
            doc['accessors'].append(acc); doc['buffers'][0]['byteLength'] = len(g.bin)
            done[key] = len(doc['accessors']) - 1
        a['JOINTS_0'] = done[key]
print('HEM band bones', len(BAND), 'Spine influences moved to them', moved)

# ---- keys ---------------------------------------------------------------------------------------------------------
m = Model(g)
w0 = m.world({})
pr0 = m.primitives[0]; J, W = pr0['joints'], pr0['weights']; rest = m.skinned_positions(w0)[0][0]
spine_up = np.linalg.inv(w0[SP])[:3, :3] @ np.array([0, 1.0, 0])
legall = np.where((np.isin(J, [i for i, n in enumerate(jn) if 'Thigh' in n or 'Calf' in n]) * W).sum(1) > 0.5)[0]
TRI = np.asarray(pr0['triangles']).reshape(-1, 3)
swv = (np.isin(J, [jn.index(n) for n in jn if n.startswith('Skirt_')]) * W).sum(1)
FACE = np.where((swv[TRI] > 0.01).all(1))[0]
ft0 = rest[TRI[FACE]]; n0 = np.cross(ft0[:, 1] - ft0[:, 0], ft0[:, 2] - ft0[:, 0]); n0 /= np.maximum(np.linalg.norm(n0, axis=1, keepdims=True), 1e-12)
FACE = FACE[((n0 * (ft0.mean(1) * [1, 0, 1])).sum(1) > 0) & (np.abs(n0[:, 1]) < 0.6)]
HW = np.stack([(W * (J == jn.index(nm))).sum(1) for nm in RING], 1)
FHW = HW[TRI[FACE]].mean(1)
HN = [names.index(nm) for nm in RING]
Q0 = [np.array(doc['nodes'][i].get('rotation', [0, 0, 0, 1]), float) for i in HN]
BN = list(BAND)
FBW = np.stack([(W * (J == jn.index(names[b]))).sum(1) for b in BN], 1)[TRI[FACE]].mean(1)


def rot_q(ax, a):
    s = np.sin(a / 2); return np.array([ax[0] * s, ax[1] * s, ax[2] * s, np.cos(a / 2)])


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


def rv_q(rv):
    a = float(np.linalg.norm(rv))
    return np.array([0, 0, 0, 1.0]) if a < 1e-9 else rot_q(rv / a, a)


def pose_local(clip, t, RV, TB):
    """Clip TRS with the hinges at rotation vectors RV (6, 3) (Spine frame) and the follow bones on their thighs."""
    loc = m.sample(clip, t)
    w = m.world(loc)
    for k, i in enumerate(HN):
        th = THIGH[RING[k][-1]]
        L = np.linalg.inv(w[SP]) @ w[th] @ np.linalg.inv(w0[th]) @ w0[i]          # the hinge carried rigidly by its thigh
        R = L[:3, :3] / np.linalg.norm(L[:3, :3], axis=0)
        tr0, q0 = np.array(m.rest[i][0], float), Q0[k]
        tb = tr0 + BETA * (L[:3, 3] - tr0); qb = slerp(q0, matrix_quaternion(R), BETA)
        loc[i] = [tb, qmul(rv_q(RV[k]), qb), np.ones(3)]
    for k, b in enumerate(BN):
        loc[b] = [TB[k].copy(), np.array([0, 0, 0, 1.0]), np.ones(3)]
    return loc


def through(clip, t, RV, TB, band=True):
    loc = pose_local(clip, t, RV, TB); w = m.world(loc); x = m.skinned_positions(w)[0][0]; ft = x[TRI[FACE]]
    c_ = ft.mean(1); n_ = np.cross(ft[:, 1] - ft[:, 0], ft[:, 2] - ft[:, 0]); n_ /= np.maximum(np.linalg.norm(n_, axis=1, keepdims=True), 1e-12)
    q = x[legall]; _, near = cKDTree(c_).query(q, k=24); pts = np.repeat(q, 24, 0)
    qq, _ = closest_on_triangles(pts, ft[near.ravel(), 0], ft[near.ravel(), 1], ft[near.ravel(), 2])
    dd = np.linalg.norm(pts - qq, axis=1).reshape(near.shape); b = dd.argmin(1); r = np.arange(len(q))
    fid = near[r, b]; cp = qq.reshape(*near.shape, 3)[r, b]; s_ = np.einsum('ij,ij->i', q - cp, n_[fid]); dist = dd[r, b]
    th = (s_ > -MARGIN) & (s_ > 0.98 * dist - MARGIN) & (dist < 0.2)
    out = np.zeros((6, 3)); outb = np.zeros((len(BN), 3)); Rs = w[SP][:3, :3].T / np.linalg.norm(w[SP][:3, 0]) ** 2
    worst = float(s_[th].max()) if th.any() else 0.0
    for i in np.where(th)[0]:
        wb = FBW[fid[i]]
        if band and wb.sum() > 0.25:                                     # the band under the belt: push it out along the normal
            d = Rs @ n_[fid[i]] * (s_[i] + MARGIN) / wb.sum() * 0.7
            for k in np.where(wb > 0.02)[0]:
                v = d * wb[k] / wb.max()
                if np.linalg.norm(v) > np.linalg.norm(outb[k]): outb[k] = v
            continue
        wv = FHW[fid[i]]
        if wv.sum() < 0.15: continue
        N = Rs @ n_[fid[i]]; N /= np.linalg.norm(N); ax = np.cross(-spine_up, N); na = np.linalg.norm(ax)
        if na < 0.2: continue
        mag = (s_[i] + MARGIN) / 0.09 * wv / wv.sum() ** 2                # lever ~9 cm, scaled by how much the hinge moves the face
        for k in range(6):
            if mag[k] > np.linalg.norm(out[k]): out[k] = ax / na * min(mag[k], np.radians(8))
    return out, outb, worst


rep = {}
for an in doc['animations']:
    clip = an['name']
    if clip not in GAITS: continue
    dur = m.clip_times(clip)[-1]; n = int(round(dur * 60)); T = np.linspace(0, dur, n + 1)
    RV = np.zeros((len(T), 6, 3)); TB = np.zeros((len(T), len(BN), 3)); left = []
    for f, t in enumerate(T[:-1]):
        for it in range(24):                                             # hinges first; the band only for what they cannot reach
            push, pushb, worst = through(clip, float(t), RV[f], TB[f], band=it >= 10)
            if not push.any() and not pushb.any():
                if it < 10: continue
                break
            RV[f] += push; TB[f] += pushb
            mg = np.linalg.norm(RV[f], axis=1, keepdims=True); RV[f] *= np.minimum(1, np.radians(MAXDEG) / np.maximum(mg, 1e-9))
            mg = np.linalg.norm(TB[f], axis=1, keepdims=True); TB[f] *= np.minimum(1, BAND_MAX / np.maximum(mg, 1e-9))
        left.append(worst)

    def hold_blur(X):
        core = X[:-1]; mg = np.linalg.norm(core, axis=2)
        pick = np.argmax([np.roll(mg, k, 0) for k in (-1, 0, 1)], 0)
        H3 = np.choose(pick[..., None], [np.roll(core, k, 0) for k in (-1, 0, 1)])
        Y = gaussian_filter1d(H3, 1.0, axis=0, mode='wrap'); return np.r_[Y, Y[:1]]
    RV = hold_blur(RV); TB = hold_blur(TB)
    an['channels'] = [c for c in an['channels'] if not names[c['target']['node']].startswith('Skirt_')]
    tacc = g.append_accessor(T.astype(np.float32), 'SCALAR')
    Qh = [[] for _ in RING]; Th = [[] for _ in RING]; Qb = {b: [] for b in BAND}; Tb = {b: [] for b in BAND}
    for f, t in enumerate(T):
        loc = pose_local(clip, float(t), RV[f], TB[f])
        for k, i in enumerate(HN): Qh[k].append(loc[i][1]); Th[k].append(loc[i][0])
        for b in BAND: Qb[b].append(loc[b][1]); Tb[b].append(loc[b][0])

    def add(node, path, vals, kind):
        vals = np.array(vals, np.float64)
        if path == 'rotation':
            vals /= np.linalg.norm(vals, axis=1, keepdims=True)
            for j in range(1, len(vals)):
                if vals[j] @ vals[j - 1] < 0: vals[j] = -vals[j]
        an['samplers'].append(dict(input=tacc, output=g.append_accessor(vals.astype(np.float32), kind), interpolation='LINEAR'))
        an['channels'].append(dict(sampler=len(an['samplers']) - 1, target=dict(node=node, path=path)))
    for k, i in enumerate(HN): add(i, 'rotation', Qh[k], 'VEC4'); add(i, 'translation', Th[k], 'VEC3')
    for b in BAND:
        if np.abs(np.array(Tb[b])).max() > 1e-5: add(b, 'translation', Tb[b], 'VEC3')
    deg = np.degrees(np.linalg.norm(RV, axis=2))
    rep[clip] = {'hinge_deg_mean_max': {RING[k]: [round(float(deg[:, k].mean()), 1), round(float(deg[:, k].max()), 1)] for k in range(6)},
                 'band_push_cm_max': round(100 * float(np.linalg.norm(TB, axis=2).max()), 1), 'unsolved_frames': int(sum(x > 0.002 for x in left)), 'unsolved_max_cm': round(100 * max(left), 2)}
    print('HEM', clip, rep[clip], flush=True)
repack(g); g.write(OUT)
if len(sys.argv) > 3: json.dump(rep, open(sys.argv[3], 'w'), indent=1)
print('HEM written', OUT)
