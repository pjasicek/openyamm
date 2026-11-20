#!/usr/bin/env python3
"""Arm clearance on a clip GLB (user review 2026-10-30: hands and forearms inside the torso in Talk, Bow and Fidget;
MM9's arm clips were authored for MM9's thin bodies). Keeps the clip and turns each arm the least that clears it.

For every key of every clip (the clips have one shared key time track per clip, clips_mm9.py / Blender export):
the forearm and hand/finger vertices of each arm are tested against the rest of the body (arm_hand_gate.py inside
test). Where one is deeper than TOL, the upper arm is rotated about the shoulder joint so the deepest point moves
along the surface normal it is behind: axis = (point - shoulder) x normal, angle = (depth + MARGIN) / lever;
repeated up to ITER times per key. The push direction is horizontal, away from the trunk axis (--root). The correction (rotation vector, world space) is then smoothed over the keys
(Gaussian, sigma SIGMA keys; loops wrap) and capped at MAX_DEG, and written into the upper arm's rotation channel:
local' = Wparent^-1 * Rcorr * Wparent * local. Optionally also the forearm (`--forearm-too`: elbow bend for a hand
that is inside while the forearm is clear). Every other channel is unchanged.
Usage: arm_clear.py <in glb> <out glb> --side L=<token> --side R=<token> [--clips A,B] [--tol 0.004]
       [--margin 0.012] [--max-deg 30] [--sigma 1.5] [--upper UpperArm] [--outer-only]"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from detached_parts_audit import closest_on_triangles

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--side', action='append', required=True)
ap.add_argument('--clips', default='')
ap.add_argument('--skip', default='Dead')
ap.add_argument('--tol', type=float, default=0.004)
ap.add_argument('--margin', type=float, default=0.012)
ap.add_argument('--max-deg', type=float, default=30.0)
ap.add_argument('--sigma', type=float, default=1.5)
ap.add_argument('--iter', type=int, default=5)
ap.add_argument('--upper', default='UpperArm')
ap.add_argument('--hand-names', default='Hand,Finger,Thumb,Index,Middle,Ring,Pinky')
ap.add_argument('--arm-names', default='Clavicle,UpperArm,Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky,Twist')
ap.add_argument('--loops', default='Standing,Walking,Running')
ap.add_argument('--root', default='Pelvis,Spine', help='trunk axis joint (first match)')
ap.add_argument('--test', default='hand', help='hand (hand and finger skin) or arm (hand + forearm)')
ap.add_argument('--outer-only', action='store_true', help='test against outer body faces only (outer_surface.py)')
ap.add_argument('--solids', default='', help='work/pid_dump.npz,<lift>,<pids>: test only against the closed bones with these master part ids (the open vest and strips are not surfaces to be inside of)')
ap.add_argument('--max-depth', type=float, default=0.06)
o = ap.parse_args()
glb = Glb(Path(o.src)); model = Model(glb)
names = [n.get('name') for n in glb.json['nodes']]
idx = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in model.joints]
P = model.primitives
USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
tris, dom, off = [], [], 0
for k in USE:
    pr = P[k]; tris.append(pr['triangles'] + off); off += len(pr['positions'])
    dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
tris = np.concatenate(tris); dom = np.concatenate(dom)
sides = dict(s.split('=', 1) for s in o.side)
hk, ak = o.hand_names.split(','), o.arm_names.split(',')
SID = {}
for s, tok in sides.items():
    arm = [j for j in jn if tok in j and any(k in j for k in ak)]
    test = [j for j in jn if tok in j and (any(k in j for k in hk) or (o.test == 'arm' and 'Forearm' in j))]
    av = np.isin(dom, arm)
    SID[s] = dict(test=np.where(np.isin(dom, test))[0], body_f=np.where(~av[tris].any(1))[0],
                  upper=next(j for j in jn if tok in j and j.endswith(o.upper)))
BARY = np.array([[1 / 3, 1 / 3, 1 / 3], [0.6, 0.2, 0.2], [0.2, 0.6, 0.2], [0.2, 0.2, 0.6]])
if o.outer_only:                                    # a vest lining or the skin under a flap is not a surface to be inside of
    from outer_surface import outer_faces
    _rest = np.concatenate([p[0] for p in [model.skinned_positions(model.world({}))[k] for k in USE]])
    for d in SID.values():
        d['body_f'] = d['body_f'][outer_faces(_rest, tris, d['body_f'])]
if o.solids:
    pth, lift_, ids_ = o.solids.split(',', 2)
    D_ = np.load(pth); co_ = D_['co']
    _rest = np.concatenate([p[0] for p in [model.skinned_positions(model.world({}))[k] for k in USE]])
    tgt_ = np.c_[co_[:, 0], co_[:, 2] + (_rest[:, 1].min() - co_[:, 2].min()), -co_[:, 1]]
    _, near_ = cKDTree(tgt_).query(_rest); vp_ = D_['pid'][near_]; ok_ = np.isin(vp_, [int(x) for x in ids_.split('+')])
    for d in SID.values():
        d['body_f'] = d['body_f'][ok_[tris[d['body_f']]].all(1)]; print('SOLID faces', len(d['body_f']))
ROOT = idx[next(j for j in jn if any(k in j for k in o.root.split(',')))]


def skin(w):
    sp = model.skinned_positions(w)
    return np.concatenate([sp[k][0] for k in USE])


def deepest(X, d):
    """Closest-triangle inside test (hand_bone_gate.py), sign from the nearest triangle's normal: the face samples of the original missed fingers in the long femur triangles."""
    T = X[tris[d['body_f']]]
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    pts = X[d['test']]
    kd = cKDTree(T.mean(1)); d0, _ = kd.query(pts)
    m_ = d0 < 0.09
    if not m_.any():
        return 0.0, None, None
    q = pts[m_]; _, near = kd.query(q, k=min(10, len(T)))
    P_ = np.repeat(q, near.shape[1], 0); c_ = near.ravel()
    cp, _ = closest_on_triangles(P_, T[c_, 0], T[c_, 1], T[c_, 2])
    dd = np.linalg.norm(P_ - cp, axis=1).reshape(near.shape); b_ = dd.argmin(1); r_ = np.arange(len(q))
    c0 = cp.reshape(*near.shape, 3)[r_, b_]; fn = n[near[r_, b_]]
    sg = ((q - c0) * fn).sum(1); dist = dd[r_, b_]
    ins = (sg < -0.003) & (-sg > 0.85 * dist) & (dist < o.max_depth)
    if not ins.any():
        return 0.0, None, None
    k = np.argmax(np.where(ins, dist, 0))
    deep = ins & (dist > 0.7 * dist[k])
    nn = fn[deep].mean(0); nn /= max(np.linalg.norm(nn), 1e-9)
    return float(dist[k]), q[k], nn


def rotvec_matrix(r):
    a = np.linalg.norm(r)
    if a < 1e-12:
        return np.eye(3)
    k = r / a; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def matrix_rotvec(R):
    a = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
    if a < 1e-9:
        return np.zeros(3)
    v = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * np.sin(a))
    return v * a


rep = {}
anims = glb.json['animations']
for ai, an in enumerate(anims):
    clip = an['name']
    if (o.clips and clip not in o.clips.split(',')) or clip in o.skip.split(','):
        continue
    ch = {}
    for c in an['channels']:
        if c['target']['path'] == 'rotation':
            ch[names[c['target']['node']]] = c['sampler']
    times = None
    corr = {s: [] for s in SID}
    before = {s: 0.0 for s in SID}
    for s, d in SID.items():
        smp = an['samplers'][ch[d['upper']]]
        times = glb.accessor(smp['input'])[:, 0]
    for t in times:
        local = model.sample(clip, float(t))
        for s, d in SID.items():
            ui = idx[d['upper']]
            Rc = np.eye(3)
            base_q = local[ui][1].copy()
            for it in range(o.iter):
                w = model.world(local)
                X = skin(w)
                dep, p, nrm = deepest(X, d)
                if it == 0:
                    before[s] = max(before[s], dep)
                if dep < o.tol:
                    break
                sh = w[ui][:3, 3]
                lever = p - sh
                # push horizontally away from the trunk axis: a surface normal alone flipped between a skirt's
                # outside and its two-sided lining and the hand oscillated (Annud Fidget, Talk)
                # (below the shoulders; at the head and neck the surface normal is kept: a hand behind the neck goes
                # out along the neck's normal)
                rootp = w[ROOT][:3, 3]; radial = p - rootp; radial[1] = 0.0
                if np.linalg.norm(radial) > 1e-3 and p[1] < sh[1]:
                    nrm = radial / np.linalg.norm(radial)
                ax = np.cross(lever, nrm); L = np.linalg.norm(lever)
                if np.linalg.norm(ax) < 1e-6 or L < 1e-3:
                    break
                ang = (dep + o.margin) / L
                Rstep = rotvec_matrix(ax / np.linalg.norm(ax) * ang)
                Rc = Rstep @ Rc
                Wp = w[model.parent[ui]][:3, :3]
                Wp = Wp / np.linalg.norm(Wp, axis=0)
                Lq = quaternion_matrix(base_q)
                local[ui][1] = matrix_quaternion(Wp.T @ Rc @ Wp @ Lq)
            corr[s].append(matrix_rotvec(Rc))
    # smooth, cap, write
    loop = clip in o.loops.split(',')
    out_rep = {}
    for s, d in SID.items():
        C = np.array(corr[s])
        if len(C) > 2:
            # ease in/out around each corrected key without averaging directions (averaging cancelled opposite
            # corrections and made some keys worse): each key takes the largest neighbour correction times a falloff
            FALL = (1.0, 0.75, 0.4, 0.15)
            mag = np.linalg.norm(C, axis=1); Cn = C.copy(); best = mag.copy()
            n = len(C)
            for kk in range(n):
                for dd, fw in enumerate(FALL[1:], 1):
                    for jj in (kk - dd, kk + dd):
                        if loop:
                            jj %= n
                        if 0 <= jj < n and mag[jj] * fw > best[kk]:
                            best[kk] = mag[jj] * fw; Cn[kk] = C[jj] * fw
            C = Cn
        mag = np.linalg.norm(C, axis=1)
        cap = np.radians(o.max_deg)
        C = C * np.where(mag > cap, cap / np.maximum(mag, 1e-9), 1)[:, None]
        if loop:
            C = C - np.linspace(0, 1, len(C))[:, None] * (C[-1] - C[0])[None]
        smp = an['samplers'][ch[d['upper']]]
        Q = glb.accessor(smp['output']).astype(np.float64)
        Qn = Q.copy()
        for k, t in enumerate(times):
            local = model.sample(clip, float(t))
            w = model.world(local)
            ui = idx[d['upper']]
            Wp = w[model.parent[ui]][:3, :3]; Wp = Wp / np.linalg.norm(Wp, axis=0)
            Qn[k] = matrix_quaternion(Wp.T @ rotvec_matrix(C[k]) @ Wp @ quaternion_matrix(Q[k]))
            if k and np.dot(Qn[k], Qn[k - 1]) < 0:
                Qn[k] = -Qn[k]
        smp['output'] = glb.append_accessor(Qn, 'VEC4')
        out_rep[s] = {'worst_before_cm': round(before[s] * 100, 1),
                      'max_correction_deg': round(float(np.degrees(np.linalg.norm(C, axis=1).max())), 1),
                      'keys_corrected': int((np.linalg.norm(C, axis=1) > np.radians(0.5)).sum()), 'keys': len(times)}
    # the model caches nothing between clips except samplers read on demand: reload for the next clip's sampling
    model = Model(glb)
    rep[clip] = out_rep
    print('ARMCLEAR', clip, json.dumps(out_rep))
glb.write(o.dst)
json.dump(rep, open(str(o.dst) + '.armclear.json', 'w'), indent=1)
