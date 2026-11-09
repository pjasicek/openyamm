#!/usr/bin/env python3
"""Hands out of the body on keys (run 2, 2026-10-31), after arm_out.py and half_keys.py. Replaces arm_bump.py here.

Per clip and side: the contact episodes at 48 fps (hand, finger and forearm vertices behind an outer body face that is
not on that arm, as arm_hand_gate.py's exact test, but measured to 15 cm so a deep hand never reads as clear). Episodes
closer than two ramps share one window. Per window: a raised-cosine window w(t) with a flat top over the contact and
ramps of up to RAMP seconds, ending before the clip's last key (one-shots end on MM9's pose, so the correction is zero
at both clip ends). Two constant axes, chosen at the deepest frame so the deepest point moves along a direction d:
the upper arm turns about a1 (in its parent's frame) by bu * w(t) and the hand about a2 (in the forearm's frame) by
bh * w(t). d is tried as the depth-weighted mean normal of the entered faces, as straight out to the side, and as their
mean. Amplitudes come from a grid; among those that clear the window to under TARGET, the one with the least added
upper-arm speed (bu / ramp) wins, then the least wrist bend. The upper arm's and hand's half-joint helpers are
rewritten in the solve; run half_keys.py afterwards for the exact helpers.
Nothing is smoothed afterwards and no key moves outside its window, so the clear hand stays clear and the added angular
speed is at most amplitude * pi / (2 * ramp).
Clips run in parallel (one process each); within a clip the corrections are analytic and stack.
Args: <in glb> <out glb> <report json> [clip:side[:ramp] ...]   (no jobs: every clip and side with a contact)
(colloidal warrior) HC_BIG=1 extends the grid to 48 deg upper arm, 60 deg wrist for the hand scooping slime from its belly."""
import json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from pygltflib import GLTF2, Accessor, BufferView
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model, matrix_quaternion
from detached_parts_audit import closest_on_triangles
from outer_surface import outer_faces
SRC, DST, REP = sys.argv[1:4]; JOBS = sys.argv[4:]
RAMP, RMIN, TARGET, CONTACT, FPS = 0.4, 0.25, 0.007, 0.008, 48.0
MAXSPEED = 0.9          # deg per 48 fps frame the upper arm may gain: the jitter gate allows 1.0 over MM9
import os
MAXSPEED_CLIP = dict(x.split('=') for x in os.environ.get('HC_MAXSPEED', '').split(',') if x)      # e.g. Death2=0.4: a stricter cap where the clip's own fast frames add to it
ARM = ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Twist')
HANDF = ('Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
def qaxis(ax, a):
    return np.r_[ax * np.sin(a / 2), np.cos(a / 2)]
def half_rot(R):
    a = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
    if a < 1e-6: return np.eye(3)
    v = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * np.sin(a)) if a < np.pi - 1e-3 else None
    if v is None:
        w, V = np.linalg.eigh((R + R.T) / 2); v = V[:, w.argmax()]
    t = a / 2; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K


class Rig:
    def __init__(self, path):
        self.m = m = Model(Glb(Path(path))); self.names = names = [n.get('name') for n in m.glb.json['nodes']]
        self.idx = {n: i for i, n in enumerate(names)}; jn = [names[j] for j in m.joints]
        self.ibm = {n: m.inverse_binds[i] for i, n in enumerate(jn)}
        P = m.primitives; self.USE = USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
        tris, dom, off = [], [], 0
        for k in USE:
            pr = P[k]; tris.append(pr['triangles'] + off); off += len(pr['positions'])
            dom.append(np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]))
        self.tris = np.concatenate(tris); self.dom = np.concatenate(dom)
        self.rest = self.skin(m.world({}))

    def skin(self, w):
        sp = self.m.skinned_positions(w); return np.concatenate([sp[k][0] for k in self.USE])

    def helper(self, loc, w, h, c, p):
        """half_keys.py's helper local for child c under parent p, from world matrices w"""
        ix, ibm = self.idx, self.ibm
        Sp = w[ix[p]] @ ibm[p]; Sc = w[ix[c]] @ ibm[c]
        Sh = Sp[:3, :3] @ half_rot(Sp[:3, :3].T @ Sc[:3, :3]); Bc = np.linalg.inv(ibm[c])
        Wh = np.eye(4); Wh[:3, :3] = Sh @ Bc[:3, :3]; Wh[:3, 3] = w[ix[c]][:3, 3]
        L = np.linalg.inv(w[ix[p]]) @ Wh
        tr = list(loc.get(ix[h], [x.copy() for x in self.m.rest[ix[h]]]))
        tr[0] = L[:3, 3]; tr[1] = matrix_quaternion(L[:3, :3]); loc[ix[h]] = tr


rig = Rig(SRC); m = rig.m; idx = rig.idx; tris = rig.tris; dom = rig.dom


def side_sets(s):
    tok = f' {s} '
    av = np.array([tok in d and any(k in d for k in ARM) for d in dom])
    hv = np.where(np.array([tok in d and any(k in d for k in HANDF) for d in dom]))[0]
    bf = np.where(~av[tris].any(1))[0]; bf = bf[outer_faces(rig.rest, tris, bf)]
    return hv, bf


def depth(X, hv, bf):
    T = X[tris[bf]]; a, b, c = T[:, 0], T[:, 1], T[:, 2]
    n = np.cross(b - a, c - a); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    pts = X[hv]; _, near = cKDTree((a + b + c) / 3).query(pts, k=40)
    rp = np.repeat(pts, near.shape[1], 0)
    q, _ = closest_on_triangles(rp, a[near.ravel()], b[near.ravel()], c[near.ravel()])
    d = np.linalg.norm(rp - q, axis=1).reshape(near.shape); best = d.argmin(1); r = np.arange(len(pts))
    f = near[r, best]; side = np.einsum('ij,ij->i', pts - q.reshape(*near.shape, 3)[r, best], n[f])
    return np.where((side < 0) & (d[r, best] <= 0.15), -side, 0.0), n[f]


g = GLTF2().load(SRC); blob = bytearray(g.binary_blob())
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]; n = {'SCALAR': 1, 'VEC4': 4, 'VEC3': 3}[a.type]
    return np.frombuffer(bytes(blob), 'f4', a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n).astype(np.float64)
def put(arr):
    global blob
    while len(blob) % 4: blob.append(0)
    o_ = len(blob); d = np.asarray(arr, 'f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o_, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type='VEC4'))
    return len(g.accessors) - 1
def rot_samplers(clip):
    an = next(a for a in g.animations if a.name == clip)
    return {ch.target.node: an.samplers[ch.sampler] for ch in an.channels if ch.target.path == 'rotation'}


def window_from(fs, fe, Rin, Rout):
    def w(t):
        u = np.clip((t - (fs - Rin)) / Rin, 0, 1); v = np.clip(((fe + Rout) - t) / Rout, 0, 1)
        return (0.5 - 0.5 * np.cos(np.pi * u)) * (0.5 - 0.5 * np.cos(np.pi * v))
    w.params = (fs, fe, Rin, Rout)
    return w


HOLD_END = [c for c in os.environ.get('HC_HOLD_END', '').split(',') if c]      # (colloidal) death clips whose contact lasts to the
                                                                                # end: the correction holds there instead of returning to MM9's last pose


def make_window(t0, t1, dur, ramp, hold=False):
    """raised-cosine ramps of RMIN..ramp seconds; a contact nearer a clip end than RMIN gets a ramp that is still running
    there (the solve then needs a larger amplitude) rather than a fast one"""
    Rin = max(min(ramp, t0), RMIN); fs = max(t0, Rin)
    if hold and t1 > dur - 0.3:
        return window_from(fs, dur + 2.0, Rin, 1.0), Rin, 1.0
    Rout = max(min(ramp, dur - 0.04 - t1), RMIN); fe = min(t1, dur - 0.04 - Rout)
    return window_from(fs, fe, Rin, Rout), Rin, Rout


def posed(clip, t, corr):
    """world and skin at t with corrections [(w, ua, axu, bu, hd, axh, bh)] applied, helpers of the arm rewritten"""
    loc = m.sample(clip, float(t))
    for (w, s, axu, bu, axh, bh) in corr:
        k = w(t)
        if k <= 0: continue
        ua, hd = idx[f'Bip01 {s} UpperArm'], idx[f'Bip01 {s} Hand']
        loc[ua] = [loc[ua][0], qmul(qaxis(axu, bu * k), loc[ua][1])] + list(loc[ua][2:])
        loc[hd] = [loc[hd][0], qmul(qaxis(axh, bh * k), loc[hd][1])] + list(loc[hd][2:])
    if corr:
        w = m.world(loc)
        for s in {c[1] for c in corr}:
            rig.helper(loc, w, f'Bip01 {s} UpperArm_h', f'Bip01 {s} UpperArm', f'Bip01 {s} Clavicle')
            rig.helper(loc, w, f'Bip01 {s} Forearm_h', f'Bip01 {s} Forearm', f'Bip01 {s} UpperArm')
            rig.helper(loc, w, f'Bip01 {s} Hand_h', f'Bip01 {s} Hand', f'Bip01 {s} Forearm')
    w = m.world(loc)
    return w, rig.skin(w)


def solve_clip(clip, sides):
    """every contact of one clip, L then R; returns [(side, window, axu, bu, axh, bh, report)]. Corrections stack: the
    second side and later episodes are solved with the earlier ones applied."""
    done, reps = [], {}
    dur = max(m.clip_times(clip)); tf = np.arange(0, dur + 1e-6, 1 / FPS)
    for s, ramp in sides:
        hv, bf = side_sets(s)
        ua, fa, hd = idx[f'Bip01 {s} UpperArm'], idx[f'Bip01 {s} Forearm'], idx[f'Bip01 {s} Hand']; pa = m.parent[ua]
        prev = [c[:6] for c in done]
        dep = np.zeros(len(tf)); nrm = np.zeros((len(tf), 3)); tip = np.zeros((len(tf), 3)); wl = [None] * len(tf)
        for k, t in enumerate(tf):
            w, X = posed(clip, t, prev)
            d_, n_ = depth(X, hv, bf); i = int(d_.argmax()); dep[k] = d_[i]; nrm[k] = n_[i]; tip[k] = X[hv[i]]; wl[k] = w
        cont = np.where(dep > CONTACT)[0]
        if not len(cont):
            continue
        eps = [[cont[0], cont[0]]]
        for k in cont[1:]:
            if (k - eps[-1][1]) / FPS <= 2 * ramp: eps[-1][1] = k      # one window over contacts whose ramps would overlap (split windows on Death2 R left the 0.06 s contact unsolvable)
            else: eps.append([k, k])
        for e0, e1 in eps:
            prev = [c[:6] for c in done]
            sl = slice(e0, e1 + 1); kw = e0 + int(dep[sl].argmax())
            wt = dep[sl][:, None]; nmean = (nrm[sl] * wt).sum(0); nmean /= np.linalg.norm(nmean)
            w = wl[kw]
            lat = w[idx['Bip01 L Thigh']][:3, 3] - w[idx['Bip01 R Thigh']][:3, 3]; lat /= np.linalg.norm(lat)
            lat = lat if s == 'L' else -lat
            mix = nmean + lat; mix /= np.linalg.norm(mix)
            win, Rin, Rout = make_window(tf[e0], tf[e1], dur, ramp, clip in HOLD_END)
            span = [float(t) for t in tf if win(t) > 0]; coarse = span[::2]
            S, Wr = w[ua][:3, 3], w[hd][:3, 3]; P = tip[kw]
            fr = lambda n: w[n][:3, :3] / np.linalg.norm(w[n][:3, :3], axis=0)
            per_deg = np.pi / (2 * min(Rin, Rout)) / FPS            # added deg per frame for each degree of amplitude
            sols = []
            for dname, d in (('normal', nmean), ('side', lat), ('mix', mix)):
                a1 = np.cross(P - S, d); a1 /= max(np.linalg.norm(a1), 1e-9)
                a2 = np.cross(P - Wr, d); a2 /= max(np.linalg.norm(a2), 1e-9)
                axu = fr(pa).T @ a1; axh = fr(fa).T @ a2
                for bu_d in ((0, 3, 6, 9, 12, 16, 20, 25) + ((30, 35, 40, 48) if os.environ.get('HC_BIG') else ()) + ((56, 64, 72, 80) if os.environ.get('HC_HUGE') else ())):
                    for bh_d in ((0, 5, 10, 15, 20, 25, 30, 35, 40) + ((50, 60) if os.environ.get('HC_BIG') else ())):
                        if bu_d == 0 and bh_d == 0: continue
                        corr = prev + [(win, s, axu, np.radians(bu_d), axh, np.radians(bh_d))]
                        worst = max(depth(posed(clip, t, corr)[1], hv, bf)[0].max() for t in coarse)
                        if worst < TARGET:
                            sols.append((bu_d * per_deg > float(MAXSPEED_CLIP.get(clip, MAXSPEED)), bu_d * per_deg + 0.03 * bh_d, dname, bu_d, bh_d, axu, axh)); break
                    if sols and sols[-1][4] == 0 and sols[-1][3] == bu_d: break
            ok = None
            for sol in sorted(sols, key=lambda x: (x[0], x[1])):
                corr = prev + [(win, s, sol[5], np.radians(sol[3]), sol[6], np.radians(sol[4]))]
                worst = max(depth(posed(clip, t, corr)[1], hv, bf)[0].max() for t in span)
                if worst < TARGET * 1.6:
                    ok = (sol, worst); break
            key = f'{clip}:{s}:{tf[e0]:.2f}'
            if ok is None:
                reps[key] = dict(before_cm=round(float(dep[sl].max()) * 100, 1), fixed=False); print('NOFIX', clip, s, reps[key], flush=True)
                continue
            sol, worst = ok
            r = dict(before_cm=round(float(dep[sl].max()) * 100, 1), contact=[round(float(tf[e0]), 3), round(float(tf[e1]), 3)],
                     ramps=[round(float(Rin), 3), round(float(Rout), 3)], direction=sol[2], upper_arm_deg=sol[3], wrist_deg=sol[4],
                     after_cm=round(float(worst) * 100, 2), upper_arm_added_deg_per_frame48=round(sol[3] * per_deg, 2),
                     wrist_added_deg_per_frame48=round(sol[4] * per_deg, 2))
            reps[key] = r; print('CLEAR', clip, s, r, flush=True)
            done.append((win, s, sol[5], np.radians(sol[3]), sol[6], np.radians(sol[4])))
    return clip, [(c[1], c[0].params, c[2], c[3], c[4], c[5]) for c in done], reps


def run(job):
    clip, sides = job
    return solve_clip(clip, sides)


if __name__ == '__main__':
    from multiprocessing import Pool
    want = {}
    for j in (x.split(':') for x in JOBS):
        want.setdefault(j[0], []).append((j[1], float(j[2]) if len(j) > 2 else RAMP))
    if not want:
        want = {c: [('L', RAMP), ('R', RAMP)] for c in m.clips if c != 'Dead'}
    with Pool(min(len(want), 12)) as pool:
        results = pool.map(run, list(want.items()))
    report = {}
    for clip, corrs, reps in results:
        report.update(reps)
        tr = rot_samplers(clip)
        for s, wp, axu, bu, axh, bh in corrs:
            win = window_from(*wp)
            ua, hd = idx[f'Bip01 {s} UpperArm'], idx[f'Bip01 {s} Hand']
            ts = acc(tr[ua].input)[:, 0]; Qua, Qh = acc(tr[ua].output).copy(), acc(tr[hd].output).copy()
            for k, t in enumerate(ts):
                b = win(t)
                if b > 0:
                    Qua[k] = qmul(qaxis(axu, bu * b), Qua[k]); Qh[k] = qmul(qaxis(axh, bh * b), Qh[k])
            tr[ua].output = put(Qua); tr[hd].output = put(Qh)
    g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(DST)
    json.dump(report, open(REP, 'w'), indent=1)
    print('DONE', len(report), 'unfixed', sum(1 for v in report.values() if v.get('fixed') is False))
