#!/usr/bin/env python3
"""Level planted Troll soles flat on the floor (user: "feet not on ground but angled"; the source idle rolled each boot
13-19 deg onto one edge, 7 cm of sole spread). After the MM6 Knight's flatten_feet.py: per foot the sole is the
foot/toe-weighted LOD0 vertices within SOLE_H of the lowest bind-pose vertex (plane and heel-to-toe axis carried in
foot-bone space). Per frame of each listed clip the foot bone is rotated about the ankle so the sole lies flat
(mode full: roll and pitch; roll: roll only; walk: full, ramped in and out over RAMP frames at both ends of each
planted interval so heel strike and toe-off stay), weighted by how planted the foot is (lowest sole below PLANT_LO:
full, above PLANT_HI: none). Then a two-bone IK on thigh and calf (knee kept in its own bend plane) moves the ankle
vertically so the lowest sole point reaches the floor (0) by the same weight; the foot keeps its levelled world
orientation. The pelvis, root motion and every other channel stay. Clips as name:mode.
Heights, sole planes and the report use the skinned lower boot (calf, foot and toe weights), not a rigid foot-space
sole: the heel sole is about half calf-weighted. Sole spread = height range of the skinned bottom 2 cm band.
Usage: flatten_feet_ik.py <in.glb> <out.glb> <clip:mode,...> [--measure]"""
import os
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

SOLE_H, PLANT_LO, PLANT_HI = 0.02, 0.03, 0.08
FEET = ('B_L_Foot', 'B_R_Foot')
CT = {5126: ('f', 4), 5125: ('I', 4), 5123: ('H', 2), 5121: ('B', 1)}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def acc(doc, b, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]; f, s = CT[a['componentType']]; n = NC[a['type']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0); stride = v.get('byteStride', s * n)
    out = np.zeros((a['count'], n), {'f': np.float32, 'I': np.uint32, 'H': np.uint16, 'B': np.uint8}[f])
    for k in range(a['count']):
        out[k] = struct.unpack_from('<' + f * n, b, off + k * stride)
    if a.get('normalized') and f != 'f':
        out = out / float(np.iinfo(out.dtype).max)
    return out


def q2m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def m2q(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1) * 2; q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(m))); j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2; q = [0, 0, 0, 0]
        q[i] = s / 4; q[j] = (m[j, i] + m[i, j]) / s; q[k] = (m[k, i] + m[i, k]) / s; q[3] = (m[k, j] - m[j, k]) / s
    q = np.array(q); return q / np.linalg.norm(q)


def trs(t, r, s):
    m = np.eye(4); m[:3, :3] = q2m(r) * s; m[:3, 3] = t; return m


def align(a, b):
    """Rotation matrix taking unit vector a onto unit vector b."""
    v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k / (1 + c)


def about(axis, ang):
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(ang) * k + (1 - np.cos(ang)) * k @ k


def roll_fix(n, f):
    """Rotation about the heel-to-toe axis f taking the sole normal n into the vertical plane through f."""
    f = f / np.linalg.norm(f); up = np.array([0., 1., 0.])
    a = n - (n @ f) * f; u = up - (up @ f) * f
    if np.linalg.norm(a) < 1e-6 or np.linalg.norm(u) < 1e-6:
        return 0.0
    a /= np.linalg.norm(a); u /= np.linalg.norm(u)
    return float(np.arctan2(np.cross(a, u) @ f, a @ u))


def slerp_id(m, w):
    """Rotation m scaled to fraction w of its angle."""
    ang = np.arccos(np.clip((np.trace(m) - 1) / 2, -1, 1))
    if ang < 1e-6:
        return np.eye(3)
    axis = np.array([m[2, 1] - m[1, 2], m[0, 2] - m[2, 0], m[1, 0] - m[0, 1]]) / (2 * np.sin(ang))
    a = ang * w; k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * k + (1 - np.cos(a)) * k @ k


args = [a for a in sys.argv[1:] if not a.startswith('--')]; measure = '--measure' in sys.argv
src, dst = Path(args[0]), Path(args[1])
clips = dict((c.split(':') + ['roll'])[:2] for c in (args[2] if len(args) > 2 else 'Standing:full').split(','))
RAMP = 2
IK_HI = 0.05
SMOOTH = int(os.environ.get('FEET_SMOOTH', '2'))
LOOPS = ('Standing', 'Walking', 'Running', 'Fidget')
KNEE_MIN = float(os.environ.get('KNEE_MIN', '25'))
LIMITED = {}
doc, b = read_glb(src); b = bytearray(b)
nodes = doc['nodes']; names = [n.get('name') for n in nodes]
parent = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}
skin = doc['skins'][0]; joints = skin['joints']; ibm = acc(doc, b, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
mesh_node = next(n for n in nodes if n.get('name') == 'Troll'); prim = doc['meshes'][mesh_node['mesh']]['primitives'][0]
pos = acc(doc, b, prim['attributes']['POSITION']).astype(np.float64)
jw = [(acc(doc, b, prim['attributes'][f'JOINTS_{k}']), acc(doc, b, prim['attributes'][f'WEIGHTS_{k}']))
      for k in range(2) if f'JOINTS_{k}' in prim['attributes']]
sole = {}
BOOT = {}
BOOT_H = 0.04
for foot in FEET:
    fi = names.index(foot); toe = names.index(foot.replace('Foot', 'Toe0'))
    wsum = sum(((np.isin(np.array(joints)[j.astype(int)], [fi, toe])) * w).sum(1) for j, w in jw)
    vs = pos[wsum > .5]; low = vs[:, 1].min(); pts = vs[vs[:, 1] < low + SOLE_H]
    c = pts.mean(0); vt = np.linalg.svd(pts - c)[2]; n = vt[2] if vt[2][1] > 0 else -vt[2]
    j = joints.index(fi); R0 = ibm[j][:3, :3]
    local = R0 @ n; local /= np.linalg.norm(local)
    flocal = R0 @ vt[0]; flocal /= np.linalg.norm(flocal)
    sole[foot] = (fi, (ibm[j] @ np.append(pts, np.ones((len(pts), 1)), 1).T).T[:, :3], local, flocal)
    # lower boot for skinned heights: vertices within BOOT_H of the sole, skinned by calf, foot and toe (heel sole
    # vertices carry about half calf weight; a rigid foot-space sole missed them sinking 2.5 cm)
    calf = names.index(foot.replace('Foot', 'Calf')); wsel = np.zeros((len(pos), 3))
    for jj, ww in jw:
        jn = np.array(joints)[jj.astype(int)]
        for k, bone in enumerate((calf, fi, toe)):
            wsel[:, k] += ((jn == bone) * ww).sum(1)
    boot = (pos[:, 1] < low + BOOT_H) & (wsel.sum(1) > .9) & (wsel[:, 1] + wsel[:, 2] > .2)
    bw = wsel[boot] / wsel[boot].sum(1, keepdims=True); bv = np.append(pos[boot], np.ones((boot.sum(), 1)), 1)
    IB = [ibm[joints.index(x)] for x in (calf, fi, toe)]
    BOOT[foot] = (toe, bw, [(Ib @ bv.T).T for Ib in IB], pos[boot][:, 1] < low + SOLE_H)


def globals_at(anim, f):
    loc = {i: (np.array(n.get('translation', [0, 0, 0]), float), np.array(n.get('rotation', [0, 0, 0, 1]), float),
               np.array(n.get('scale', [1, 1, 1]), float)) for i, n in enumerate(nodes)}
    for ch in anim['channels']:
        i = ch['target']['node']; p = ch['target']['path']
        if p not in ('translation', 'rotation', 'scale'):
            continue
        v = sample(anim, ch['sampler'], times[anim['name']][f], p); t, r, s = loc[i]
        loc[i] = (v if p == 'translation' else t, v if p == 'rotation' else r, v if p == 'scale' else s)
    g = {}

    def G(i):
        if i not in g:
            m = trs(*loc[i]); g[i] = (G(parent[i]) @ m) if i in parent else m
        return g[i]
    return G, loc


cache, times, master = {}, {}, {}
for anim in doc['animations']:
    for si, s in enumerate(anim['samplers']):
        cache[(anim['name'], si)] = (acc(doc, b, s['input'])[:, 0].astype(np.float64), acc(doc, b, s['output']).astype(np.float64))
    master[anim['name']] = max((s['input'] for s in anim['samplers']), key=lambda i: doc['accessors'][i]['count'])
    times[anim['name']] = acc(doc, b, master[anim['name']])[:, 0].astype(np.float64)


def sample(anim, si, t, path):
    ts, vs = cache[(anim['name'], si)]
    k = int(np.searchsorted(ts, t, 'right')) - 1
    if k < 0:
        return vs[0]
    if k >= len(ts) - 1:
        return vs[-1]
    u = (t - ts[k]) / (ts[k + 1] - ts[k]); a, c = vs[k], vs[k + 1]
    if path == 'rotation':
        c = c if a @ c >= 0 else -c; q = a * (1 - u) + c * u; return q / np.linalg.norm(q)
    return a * (1 - u) + c * u


unit = lambda m: m / np.linalg.norm(m, axis=0)
foot_of = {names.index(f): f for f in FEET}


def ramp_weights(lows):
    """walk mode: planted weight ramped up/down over RAMP frames at both ends of each planted run (cyclic clip)."""
    n = len(lows); planted = lows < PLANT_LO; w = np.zeros(n)
    if planted.all():
        return np.ones(n)
    for i in range(n):
        if planted[i]:
            back = next(k for k in range(1, n) if not planted[(i - k) % n]); fwd = next(k for k in range(1, n) if not planted[(i + k) % n])
            w[i] = min(1.0, min(back, fwd) / (RAMP + 1))
    return w


report = {}
for anim in doc['animations']:
    name = anim['name']; T = times[name]; nframes = len(T)
    edit = name in clips and not measure; mode = clips.get(name, '')
    rot_ch = {ch['target']['node']: ch['sampler'] for ch in anim['channels'] if ch['target']['path'] == 'rotation'}
    new = {i: np.array([sample(anim, rot_ch[i], t_, 'rotation') for t_ in T]) for i in rot_ch}
    stats = {f: [] for f in FEET}
    # first pass: per-frame planted weights (levelling and IK), smoothed over time ([1 2 1] / 4 twice, cyclic for
    # loops) so the correction fades in and out over a few frames instead of switching as a foot lifts
    W, WI = {}, {}
    if edit:
        for foot, (fi, pts, nloc, floc) in sole.items():
            lows = []
            for f in range(nframes):
                G, _ = globals_at(anim, f); M = G(fi); lows.append(((M[:3, :3] @ pts.T).T + M[:3, 3])[:, 1].min())
            lows = np.array(lows)
            w = np.clip((PLANT_HI - lows) / (PLANT_HI - PLANT_LO), 0, 1); wi = np.clip((IK_HI - lows) / (IK_HI - PLANT_LO), 0, 1)
            if mode == 'walk':
                r = ramp_weights(lows); w, wi = np.minimum(w, r), np.minimum(wi, r)
            for _ in range(SMOOTH):
                for arr in (w, wi):
                    if name in LOOPS:
                        arr[:] = (np.roll(arr, 1) + 2 * arr + np.roll(arr, -1)) / 4
                    else:
                        pad = np.r_[arr[0], arr, arr[-1]]; arr[:] = (pad[:-2] + 2 * pad[1:-1] + pad[2:]) / 4
            W[foot], WI[foot] = w, wi
    def solve(G, fi, pts, nloc, floc, w, wi):
        """Levelled foot world rotation, new thigh/calf world rotations and the resulting knee flex (deg)."""
        M = G(fi); S = unit(M[:3, :3]); nw = S @ nloc; fw = S @ floc
        if mode in ('full', 'walk'):
            C = slerp_id(align(nw / np.linalg.norm(nw), np.array([0., 1., 0.])), w)
        else:
            C = about(fw / np.linalg.norm(fw), np.radians(roll_fix(nw, fw)) * w)
        Rg = C @ S; calf = parent[fi]; thigh = parent[calf]
        A = M[:3, 3]; K = G(calf)[:3, 3]; H = G(thigh)[:3, 3]
        # roll the foot flat about the sole point it stands on (the ankle moves on a short arc around it), then put
        # the lowest levelled sole point on the floor; two-bone IK, knee kept in its own bend plane
        wp = (M[:3, :3] @ pts.T).T + A; pivot = wp[wp[:, 1].argmin()]
        At = pivot + C @ (A - pivot); h = ((C @ M[:3, :3] @ pts.T).T + At)[:, 1].min()
        At = A + (At - A) * wi + np.array([0., -h * wi, 0.])
        target = (1 - wi) * skinned_low(G, fi, unit(G(parent[fi])[:3, :3]), K, S, A)
        n0 = plane_normal(skinned(G, fi, unit(G(parent[fi])[:3, :3]), K, S, A)[1])
        goal = slerp_id(align(n0, np.array([0., 1., 0.])), w) @ n0 if mode in ('full', 'walk') else None
        for _ in range(4):
            T2, C2, K2, At2, flex = ik(G, fi, A, K, H, At)
            if goal is not None:
                # heel sole vertices carry calf weight: turn the foot further until the skinned sole plane
                # reaches the levelled orientation
                ns = plane_normal(skinned(G, fi, C2, K2, Rg, At2)[1]); Rg = align(ns, goal) @ Rg
            At = At + np.array([0., (target - skinned_low(G, fi, C2, K2, Rg, At2)) * (1 if wi > 0 else 0), 0.])
        T2, C2, K2, At2, flex = ik(G, fi, A, K, H, At)
        return Rg, T2, C2, flex, thigh, calf

    def ik(G, fi, A, K, H, At):
        calf = parent[fi]; thigh = parent[calf]
        L1, L2 = np.linalg.norm(K - H), np.linalg.norm(A - K)
        d = np.clip(np.linalg.norm(At - H), abs(L1 - L2) + 1e-5, L1 + L2 - 1e-5)
        u = (At - H) / np.linalg.norm(At - H); v = (K - H) - ((K - H) @ u) * u; v /= np.linalg.norm(v)
        a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); K2 = H + a * u + np.sqrt(max(L1 * L1 - a * a, 0)) * v
        Q1 = align((K - H) / L1, (K2 - H) / L1)
        T2 = Q1 @ unit(G(thigh)[:3, :3]); Q2 = align(Q1 @ (A - K) / L2, (At - K2) / np.linalg.norm(At - K2))
        C2 = Q2 @ Q1 @ unit(G(calf)[:3, :3])
        At2 = K2 + (At - K2) / np.linalg.norm(At - K2) * L2
        flex = np.degrees(np.arccos(np.clip(((K2 - H) @ (At2 - K2)) / (L1 * L2), -1, 1)))
        return T2, C2, K2, At2, flex

    def skinned(G, fi, Rc, Kc, Rf, Af):
        """Skinned lower-boot points with the calf at (Rc, Kc) and the foot at (Rf, Af); the toe keeps its local
        transform under the foot. Returns all points and the bottom band (the sole)."""
        toe, bw, locs, band = BOOT[foot_of[fi]]
        Mc = np.eye(4); Mc[:3, :3] = Rc; Mc[:3, 3] = Kc; Mf = np.eye(4); Mf[:3, :3] = Rf; Mf[:3, 3] = Af
        Mt = Mf @ (np.linalg.inv(G(fi)) @ G(toe))
        p = sum(bw[:, k:k + 1] * (M_ @ locs[k].T).T[:, :3] for k, M_ in enumerate((Mc, Mf, Mt)))
        return p, p[band]

    def skinned_low(G, fi, Rc, Kc, Rf, Af):
        return skinned(G, fi, Rc, Kc, Rf, Af)[0][:, 1].min()

    def plane_normal(q):
        c = q.mean(0); n = np.linalg.svd(q - c)[2][2]
        return n if n[1] > 0 else -n

    # second pass: the largest fraction of the correction per frame that keeps the knee bent by KNEE_MIN (a locked
    # straight knee where the ankle cannot reach), min-filtered over 3 frames and smoothed like the weights
    if edit:
        for foot, (fi, pts, nloc, floc) in sole.items():
            frac = np.ones(nframes)
            for f in range(nframes):
                if W[foot][f] <= 1e-4:
                    continue
                G, _ = globals_at(anim, f)
                if solve(G, fi, pts, nloc, floc, W[foot][f], WI[foot][f])[3] >= KNEE_MIN:
                    continue
                lo, hi = 0.0, 1.0
                for _ in range(10):
                    mid = (lo + hi) / 2
                    if solve(G, fi, pts, nloc, floc, W[foot][f] * mid, WI[foot][f] * mid)[3] >= KNEE_MIN:
                        lo = mid
                    else:
                        hi = mid
                frac[f] = lo
            cyc = name in LOOPS
            frac = np.minimum.reduce([np.roll(frac, k) if cyc else np.r_[frac[:1], frac[:-1]] if k == 1 else np.r_[frac[1:], frac[-1:]] if k == -1 else frac for k in (-1, 0, 1)])
            for _ in range(SMOOTH):
                frac = (np.roll(frac, 1) + 2 * frac + np.roll(frac, -1)) / 4 if cyc else (np.r_[frac[0], frac[:-1]] + 2 * frac + np.r_[frac[1:], frac[-1]]) / 4
            W[foot] = W[foot] * frac; WI[foot] = WI[foot] * frac; LIMITED[(name, foot)] = int((frac < .99).sum())
    for f in range(nframes):
        G, loc = globals_at(anim, f)
        for foot, (fi, pts, nloc, floc) in sole.items():
            M = G(fi); S = unit(M[:3, :3])
            allp, band = skinned(G, fi, unit(G(parent[fi])[:3, :3]), G(parent[fi])[:3, 3], S, M[:3, 3])
            nsk = plane_normal(band); low = allp[:, 1].min()
            stats[foot].append((np.degrees(np.arccos(np.clip(nsk[1], -1, 1))), low, band[:, 1].max() - band[:, 1].min()))
            if not edit or W[foot][f] <= 1e-4:
                continue
            Rg, T2, C2, flex, thigh, calf = solve(G, fi, pts, nloc, floc, W[foot][f], WI[foot][f])
            P = unit(G(parent[thigh])[:3, :3])
            for i, Rnew, Rpar in ((thigh, T2, P), (calf, C2, T2), (fi, Rg, C2)):
                q = m2q(Rpar.T @ Rnew); q = q if q @ new[i][f] >= 0 else -q; new[i][f] = q
    for foot in FEET:
        a = np.array(stats[foot]); pl = a[:, 1] < PLANT_LO
        report.setdefault(name, {})[foot] = {'tilt_max': round(float(a[:, 0].max()), 1), 'planted_frames': int(pl.sum()), 'frames': len(a),
            'planted_tilt_mean': round(float(a[pl, 0].mean()), 1) if pl.any() else None,
            'planted_tilt_max': round(float(a[pl, 0].max()), 1) if pl.any() else None,
            'planted_low_min_cm': round(float(a[pl, 1].min() * 100), 2) if pl.any() else None,
            'planted_low_max_cm': round(float(a[pl, 1].max() * 100), 2) if pl.any() else None,
            'sole_spread_mean_cm': round(float(a[pl, 2].mean() * 100), 2) if pl.any() else None}
        r = report[name][foot]
        print(f"{name:9s} {foot}: planted {r['planted_frames']}/{r['frames']} tilt mean {r['planted_tilt_mean']} max {r['planted_tilt_max']} deg,"
              f" lowest sole {r['planted_low_min_cm']}..{r['planted_low_max_cm']} cm, spread {r['sole_spread_mean_cm']} cm{'  -> levelled ' + mode if edit else ''}")
    if edit:
        for i in (names.index(x) for x in ('B_L_Thigh', 'B_L_Calf', 'B_L_Foot', 'B_R_Thigh', 'B_R_Calf', 'B_R_Foot')):
            data = new[i].astype(np.float32).tobytes()
            while len(b) % 4:
                b.append(0)
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(b), 'byteLength': len(data)}); b += data
            doc['accessors'].append({'bufferView': len(doc['bufferViews']) - 1, 'componentType': 5126, 'count': nframes, 'type': 'VEC4'})
            anim['samplers'][rot_ch[i]].update(output=len(doc['accessors']) - 1, input=master[name], interpolation='LINEAR')
import json  # noqa: E402
if LIMITED:
    print('KNEE-LIMITED frames', {f'{k[0]}:{k[1]}': v for k, v in LIMITED.items() if v})
if os.environ.get('FEET_REPORT'):
    Path(os.environ['FEET_REPORT']).write_text(json.dumps(report, indent=1) + '\n')
if not measure:
    doc['buffers'][0]['byteLength'] = len(b)
    write_glb(dst, doc, bytes(b)); print('WROTE', dst)
