#!/usr/bin/env python3
"""Hand rest on the body (2026-10-30, Forad v3 Talk: MM9's hand-on-heart gesture sank into the HD body's chest and
vest; arm_clear.py's per-key upper-arm turn lifted the hand to the face and jittered). Keeps MM9's hand where it is
and moves it out of the body by a smooth push along one horizontal direction, through a two-bone solve.

Per key: the hand and finger points of one arm distal of the wrist (the graft stub inside the cuff is not tested)
are cast along d = the horizontal direction from the trunk axis (Spine3) to the wrist, against the outer body
surface (outer_surface.py, bind pose classification; neither arm is body). The front-most hit within 15 cm behind
or 3 cm in front of a point is the surface it rests on; the push is the largest (hit - point).d + CLEARANCE.
The push magnitudes s are then a curve over MM9's own wrist path (not time: 2026-10-30, a push that faded while MM9's
arm paused read as the shoulder moving by itself): a running maximum over +/- HOLD_PATH of wrist travel (the push
holds through a contact) and a Gaussian low-pass (SIGMA_PATH); every key then reaches wrist + s d with a two-step
solve (elbow bend only as far as the reach must change, then the least whole-arm swing about the shoulder) and the
hand keeps its world rotation (MM9's palm orientation). No key is solved on its own. Iterated ITER times (the pushed hand is cast again, the extra push added to the curve). A side may tilt its push
below d (`@<deg>`): a hand that MM9 laid high on a thin chest then comes to rest lower on the deeper one.
Usage: hand_rest.py <in glb> <out glb> --clip Talk --side L=<token>[@<tilt deg>] [--side R=<token>] [--clearance 0.015]
       [--hold-path 0.05] [--sigma-path 0.03] [--iter 3] [--surface-joints Spine,Pelvis,Clavicle] [--max-push 0.04]
       [--sigma-dir 0.2]"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
from outer_surface import outer_faces

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--clip', action='append', required=True)
ap.add_argument('--side', action='append', required=True)
ap.add_argument('--clearance', type=float, default=0.015)
ap.add_argument('--iter', type=int, default=3)
ap.add_argument('--hold-path', type=float, default=0.05, help='m of MM9 wrist travel')
ap.add_argument('--sigma-path', type=float, default=0.03, help='m of MM9 wrist travel')
ap.add_argument('--path-time', type=float, default=0.0003, help='m added per key (a pause still advances)')
ap.add_argument('--sigma-time', type=float, default=0.07, help='s, Gaussian over time after the path filter')
ap.add_argument('--hold-time', type=float, default=0.0, help='s, running maximum over time before that Gaussian')
ap.add_argument('--max-push', type=float, default=0.0, help='m, cap of the raw need per key (0: none): on a flared '
                'skirt the horizontal cast reads several times the true depth (Yrsa Fidget 9.7 cm cast, 2.7 cm deep)')
ap.add_argument('--sigma-dir', type=float, default=0.0, help='s, Gaussian over the push direction (0: per key); the '
                'horizontal trunk-to-wrist direction swings fast when the wrist passes close to the trunk axis')
ap.add_argument('--normal-dir', action='store_true', help='push along the mean surface normal under the hand (a lying body), not the horizontal')
ap.add_argument('--surface-joints', default='', help='rest only on faces of these joints (substrings)')
ap.add_argument('--body-extra', default='', help='arm joints that count as body for this clip (substrings; the other arm a hand comes against)')
ap.add_argument('--hand-names', default='Hand,Finger,Thumb,Index,Middle,Ring,Pinky')
ap.add_argument('--arm-names', default='Clavicle,UpperArm,Forearm,Hand,Finger,Thumb,Index,Middle,Ring,Pinky,Twist')
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
hk, ak = o.hand_names.split(','), o.arm_names.split(',')
extra = [k for k in o.body_extra.split(',') if k]
arm_any = np.isin(dom, [j for j in jn if any(k in j for k in ak) and not any(k in j for k in extra)])


def skin(w):
    sp = model.skinned_positions(w)
    return np.concatenate([sp[k][0] for k in USE])


REST = skin(model.world({}))
body_f = np.where(~arm_any[tris].any(1))[0]          # neither arm is body: the trunk, head and legs
body_f = body_f[outer_faces(REST, tris, body_f)]
if o.surface_joints:                                 # only these parts are rested on (e.g. the trunk, not the chin)
    body_f = body_f[np.isin(dom[tris[body_f]], [j for j in jn if any(k in j for k in o.surface_joints.split(','))]).all(1)]
BARY = np.array([[1 / 3, 1 / 3, 1 / 3], [0.6, 0.2, 0.2], [0.2, 0.6, 0.2], [0.2, 0.2, 0.6]])
SID = {}
for s in o.side:
    key, tok = s.split('=', 1)
    tok, tilt = (tok.split('@') + ['0'])[:2]           # optional '@<deg>': the push also lowers the hand (deg below d)
    find = lambda end: next(j for j in jn if tok in j and j.endswith(end))
    SID[key] = dict(tilt=np.radians(float(tilt)), ua=idx[find('UpperArm')], fa=idx[find('Forearm')], hd=idx[find('Hand')],
                    test=np.where(np.isin(dom, [j for j in jn if tok in j and any(k in j for k in hk)]))[0])


def rot(m):
    r = m[:3, :3]
    return r / np.linalg.norm(r, axis=0)


def min_rot(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(np.dot(a, b)); sn = np.linalg.norm(v)
    if sn < 1e-9:
        return np.eye(3)
    k = v / sn; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    ang = np.arctan2(sn, c)
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def solve(local, d, target):
    """New local rotations (ua, fa, hd) reaching `target` with the wrist; the hand keeps its world rotation.
    Two steps that stay smooth when the arm is nearly straight (an elbow pole rebuilt from the bent elbow flipped
    there and the shoulder wobbled while the hand held still): the elbow bends or opens about its own bend axis only
    as far as the shoulder-to-wrist distance must change, then the whole arm swings about the shoulder by the least
    rotation that carries the wrist onto the target."""
    w = model.world(local)
    S, E, W = w[d['ua']][:3, 3], w[d['fa']][:3, 3], w[d['hd']][:3, 3]
    a, b = np.linalg.norm(E - S), np.linalg.norm(W - E)
    dt = min(max(np.linalg.norm(target - S), abs(a - b) + 1e-4), a + b - 1e-4)
    dc = np.linalg.norm(W - S)
    R2 = np.eye(3)
    if abs(dt - dc) > 1e-6:
        n = np.cross(E - S, W - E)
        if np.linalg.norm(n) < 1e-6:                    # straight arm: bend toward the target side
            n = np.cross(W - S, target - W)
        n /= max(np.linalg.norm(n), 1e-12)
        th_c = np.arccos(np.clip((a * a + b * b - dc * dc) / (2 * a * b), -1, 1))
        th_t = np.arccos(np.clip((a * a + b * b - dt * dt) / (2 * a * b), -1, 1))
        best = None
        for sg in (1, -1):
            r = rotvec(n * sg * (th_t - th_c))
            err = abs(np.linalg.norm(E + r @ (W - E) - S) - dt)
            if best is None or err < best[0]:
                best = (err, r)
        R2 = best[1]
    W2 = E + R2 @ (W - E)
    C1 = min_rot(W2 - S, target - S)
    Pp, UA, FA, HD = rot(w[model.parent[d['ua']]]), rot(w[d['ua']]), rot(w[d['fa']]), rot(w[d['hd']])
    L1 = quaternion_matrix(local[d['ua']][1])
    FA2 = C1 @ R2 @ FA
    return (matrix_quaternion(Pp.T @ C1 @ Pp @ L1), matrix_quaternion(UA.T @ R2 @ FA),
            matrix_quaternion(FA2.T @ HD))


def rotvec(r):
    a = np.linalg.norm(r)
    if a < 1e-12:
        return np.eye(3)
    k = r / a; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


SPINE = idx[next(j for j in jn if j.endswith('Spine3') or j.endswith('Spine2'))]
TB = tris[body_f]


def push_needed(local, d):
    """(push m, direction) for the hand to sit CLEARANCE in front of the outer surface along d."""
    w = model.world(local); X = skin(w)
    W = w[d['hd']][:3, 3]; F = rot(w[d['hd']])
    pts = X[d['test']]
    ax = F[:, np.argmax([np.ptp((pts - W) @ F[:, i]) for i in range(3)])]
    if np.median((pts - W) @ ax) < 0:
        ax = -ax
    pts = pts[(pts - W) @ ax > 0.005]
    r = W - w[SPINE][:3, 3]; r[1] = 0.0                  # glTF y up: horizontal from the trunk axis to the wrist
    dirn = r / max(np.linalg.norm(r), 1e-9)
    if o.normal_dir:
        Tt = X[TB]; ce = Tt.mean(1); nn_ = np.cross(Tt[:, 1] - Tt[:, 0], Tt[:, 2] - Tt[:, 0]); nn_ /= np.maximum(np.linalg.norm(nn_, axis=1, keepdims=True), 1e-12)
        m_ = pts.mean(0); ds = np.linalg.norm(ce - m_, axis=1); near_ = ds < max(0.12, float(ds.min()) + 0.04)
        if near_.any():
            dirn = nn_[near_].sum(0); dirn /= max(np.linalg.norm(dirn), 1e-9)
    # 2D frame perpendicular to dirn
    e1 = np.cross(dirn, [0.31, 0.9, 0.3]); e1 /= np.linalg.norm(e1); e2 = np.cross(dirn, e1)
    T = X[TB]
    t2 = np.stack([T @ e1, T @ e2], -1); tz = T @ dirn
    p2 = np.stack([pts @ e1, pts @ e2], -1); pz = pts @ dirn
    lo, hi = p2.min(0) - 0.01, p2.max(0) + 0.01
    cand = np.where((t2.max(1) >= lo).all(1) & (t2.min(1) <= hi).all(1))[0]
    if not len(cand):
        return 0.0, dirn
    A, B, C = t2[cand, 0], t2[cand, 1], t2[cand, 2]
    v0, v1 = B - A, C - A
    den = v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0]
    good = np.abs(den) > 1e-12
    q = p2[:, None, :] - A[None]
    u = (q[..., 0] * v1[None, :, 1] - q[..., 1] * v1[None, :, 0]) / np.where(good, den, 1)[None]
    v = (v0[None, :, 0] * q[..., 1] - v0[None, :, 1] * q[..., 0]) / np.where(good, den, 1)[None]
    inside = good[None] & (u >= 0) & (v >= 0) & (u + v <= 1)
    z = tz[cand, 0][None] + u * (tz[cand, 1] - tz[cand, 0])[None] + v * (tz[cand, 2] - tz[cand, 0])[None]
    rel = z - pz[:, None]                               # > 0: the surface is in front of the point
    ok = inside & (rel < 0.25) & (rel > -0.03)
    if not ok.any():
        return 0.0, dirn
    need = np.where(ok, rel, -np.inf).max(1) + o.clearance
    return float(max(need.max(), 0.0)), dirn


def smooth_curve(s, path, DT):
    """Low-pass of the push over MM9's own wrist path, not over time: the push only changes while MM9's arm moves, so
    a still arm stays still (a push fading over a pause read as the shoulder drifting on its own). `path` is the
    cumulative wrist travel per key (m) plus a slow time term so a long pause still lets a contact end. Running
    maximum over +/- HOLD_PATH, then a Gaussian of SIGMA_PATH, on a uniform path grid, then a running maximum of +/- HOLD_TIME s and a Gaussian of SIGMA_TIME s (fast reaches)."""
    g = np.linspace(path[0], path[-1], max(len(path) * 4, 2))
    sg = np.interp(g, path, s)
    step = (g[1] - g[0]) if len(g) > 1 else 1.0
    h = max(1, int(round(o.hold_path / step)))
    m = np.array([sg[max(0, i - h):i + h + 1].max() for i in range(len(sg))])
    m = gaussian_filter1d(m, max(o.sigma_path / step, 0.5), mode='nearest')
    c = np.interp(path, g, m)
    # and a short time low-pass on top: where MM9's wrist travels fast the path window spans only a key or two
    h = max(0, int(round(o.hold_time / DT)))
    c = np.array([c[max(0, i - h):i + h + 1].max() for i in range(len(c))])
    return np.maximum(gaussian_filter1d(c, o.sigma_time / DT, mode='nearest'), 0.0)


def wrist_path(locals_, d):
    P = np.array([model.world(l)[d['hd']][:3, 3] for l in locals_])
    step = np.r_[0.0, np.linalg.norm(np.diff(P, axis=0), axis=1)] + o.path_time
    return np.cumsum(step)


def pose_with(local, d, push, dirn):
    trial = {k: [x.copy() for x in v] for k, v in local.items()}
    if push > 1e-5:
        q = solve(local, d, model.world(local)[d['hd']][:3, 3] + dirn * push)
        for kk, qq in zip(('ua', 'fa', 'hd'), q):
            trial[d[kk]][1] = qq
    return trial


rep = {}
for clip in o.clip:
    an = glb.json['animations'][model.clips[clip]]
    ch = {names[c['target']['node']]: c['sampler'] for c in an['channels'] if c['target']['path'] == 'rotation'}
    out = {}
    for key, d in SID.items():
        smp = {k: an['samplers'][ch[names[d[k]]]] for k in ('ua', 'fa', 'hd')}
        times = glb.accessor(smp['ua']['input'])[:, 0]
        for k in ('fa', 'hd'):
            assert np.allclose(glb.accessor(smp[k]['input'])[:, 0], times), 'arm channels must share key times'
        locals_ = [model.sample(clip, float(t)) for t in times]
        dirs = [np.cos(d['tilt']) * dn + np.sin(d['tilt']) * np.array([0.0, -1.0, 0.0])
                for dn in (push_needed(l, d)[1] for l in locals_)]
        path = wrist_path(locals_, d)
        DT = float(np.median(np.diff(times))) if len(times) > 1 else 1 / 30
        if o.sigma_dir > 0:
            dirs = gaussian_filter1d(np.array(dirs), o.sigma_dir / DT, axis=0, mode='nearest')
            dirs = list(dirs / np.linalg.norm(dirs, axis=1, keepdims=True))
        curve = np.zeros(len(times)); raw0 = None; total = np.zeros(len(times))
        for it in range(o.iter):
            extra = np.array([push_needed(pose_with(l, d, c, dn), d)[0] for l, c, dn in zip(locals_, curve, dirs)])
            if raw0 is None:
                raw0 = extra.copy()
            if extra.max() < 0.002:
                break
            total = total + extra                       # the raw need grows; the curve is always one smoothing of it
            if o.max_push > 0:
                total = np.minimum(total, o.max_push)
            curve = smooth_curve(total, path, DT)
        Q = {k: glb.accessor(smp[k]['output']).astype(np.float64).copy() for k in smp}
        for t_i, (l, c, dn) in enumerate(zip(locals_, curve, dirs)):
            if c > 1e-5:
                q = solve(l, d, model.world(l)[d['hd']][:3, 3] + dn * c)
                for kk, qq in zip(('ua', 'fa', 'hd'), q):
                    Q[kk][t_i] = qq
        for kk in Q:
            for t_i in range(1, len(times)):
                if np.dot(Q[kk][t_i], Q[kk][t_i - 1]) < 0:
                    Q[kk][t_i] = -Q[kk][t_i]
            smp[kk]['output'] = glb.append_accessor(Q[kk], 'VEC4')
        model = Model(glb)
        left = np.array([push_needed(l, d)[0] for l in [model.sample(clip, float(t)) for t in times]])
        out[key] = {'need_before_cm': round(float(raw0.max()) * 100, 1), 'max_push_cm': round(float(curve.max()) * 100, 1),
                    'keys_pushed': int((curve > 1e-3).sum()), 'keys': len(times),
                    'need_after_cm': round(float(max(left.max() - o.clearance, 0)) * 100, 1),
                    'curve_cm': [round(float(x) * 100, 1) for x in curve], 'raw_cm': [round(float(x) * 100, 1) for x in raw0]}
    rep[clip] = out
    print('HANDREST', clip, json.dumps({k: {a: b for a, b in v.items() if not a.endswith('_cm') or not isinstance(b, list)} for k, v in out.items()}))
glb.write(o.dst)
json.dump(rep, open(str(o.dst) + '.handrest.json', 'w'), indent=1)
