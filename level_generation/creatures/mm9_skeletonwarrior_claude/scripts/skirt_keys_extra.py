#!/usr/bin/env python3
"""COPY of skirt_keys.py for the dropped MM9 clips (run2-clips-groupD, 2026-10-31), so the accepted script stays as it was.
Differences: Backpedal and BackpedalRun are loops; Death2 ramps in only, like Death; Dead2 = the last key of Death2 (each hold only
when its clip is there); work/skirt_axes.json is not rewritten. OLD = the new clips built on the approved before-skirt body.

Skirt plates on hinge bones (user: "when walking and running, the thigh bones go through the skirt"). MM9's skirt does not move.

Each plate group is rigid on a small bone `Skirt_<group>` at the belt, a child of Bip01 Spine (the thighs' parent). Keys, in the
Spine frame, on the clip's own 30 fps keys:
1. base: the rotation about the hinge that best fits the approved plate (Kabsch, the approved build's skinned plate vertices, so every
   clip keeps its look, now rigid instead of bending);
2. clearance: the least extra turn ALONG THE PLATE'S OWN APPROVED SWING that leaves every femur, knee and boot-top point at least MARGIN
   behind the plate's outer surface. Where the plate is not swinging outward the turn is about its top edge. A first version turned every
   plate radially about its top edge: the numbers passed, the skirt fanned out like a flower up to 75 deg and showed its linings. Rejected;
3. low-pass: the clearance goes through a running maximum (HOLD seconds) and a Gaussian (SIGMA seconds), so a plate rises ahead of the leg
   and settles back with it instead of ticking; circular for the loops, seams closed; a neighbour never stays below NEIGHBOUR of its
   neighbour's turn, which keeps overlapping plates together; base rotations low-passed too. Dead = the last key of Death.
Leg and body channels are not touched. Args: <new glb> <approved glb> <out glb> <report json>"""
import json, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
NEW, OLD, OUT, REP = sys.argv[1:5]
MARGIN, HOLD, SIGMA, SIGMA_BASE, NEIGHBOUR, MAXDEG, STEP = 0.010, 0.05, 0.04, 0.03, 0.0, 62.0, 1.5
LOOPS = ('Standing', 'Walking', 'Running', 'Backpedal', 'BackpedalRun')
FOLLOW = 0.45
CAP_ONESHOT = {'front': 50.0, 'other': 8.0}   # one-shots: uncapped, side and back plates flew out as black wings in Hit and Death
ONESHOT = {'AttackMelee': 0.75}      # a fully raised plate met the left hand (arm gate 11 frames over 1 cm, 3 before)
RING = ['front', 'front_R', 'side_R', 'back_R', 'back', 'back_L', 'side_L', 'front_L']
LIFT = 1.0588
GR = json.load(open(HERE / 'work' / 'skirt_groups.json'))
D = np.load(HERE / 'work' / 'skirt_dump.npz')
gNew, gOld = Glb(NEW), Glb(OLD)
mN, mO = Model(gNew), Model(gOld)
names = [n.get('name') for n in gOld.json['nodes']]
namesN = [n.get('name') for n in gNew.json['nodes']]
tgt = np.c_[D['co'][:, 0], D['co'][:, 2] + LIFT, -D['co'][:, 1]]
tree = cKDTree(tgt)
pr = mO.primitives[0]
rest = mO.skinned_positions(mO.world({}))[0][0]
pid = D['pid'][tree.query(rest)[1]]
tri = pr['triangles']
uv = np.asarray(gOld.accessor(gOld.json['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']))
a = np.abs((uv[tri[:, 1], 0] - uv[tri[:, 0], 0]) * (uv[tri[:, 2], 1] - uv[tri[:, 0], 1]) - (uv[tri[:, 2], 0] - uv[tri[:, 0], 0]) * (uv[tri[:, 1], 1] - uv[tri[:, 0], 1]))
outer = a > 1e-9
glt = lambda p: np.array([p[0], p[2] + LIFT, -p[1]])
glv = lambda p: np.array([p[0], p[2], -p[1]])
SP = names.index('Bip01 Spine')
S0 = mO.world({})[SP]; S0i = np.linalg.inv(S0)
G = {}
for g, b in GR.items():
    v = np.where(np.isin(pid, b['pids']))[0]
    f = tri[np.isin(pid[tri[:, 0]], b['pids']) & outer]
    c = (S0i @ np.r_[glt(b['pivot']), 1])[:3]
    # the thigh swings fore and aft: front and back plates rise straight over it (a diagonal "outward" rolled them edge-on, like wings)
    nn = [0.0, -1.0, 0.0] if g.startswith('front') else [0.0, 1.0, 0.0] if g.startswith('back') else b['normal']
    n = S0i[:3, :3] @ glv(nn)
    y0 = (S0i @ np.c_[rest[v], np.ones(len(v))].T).T[:, :3]
    yf = (S0i @ np.c_[rest, np.ones(len(rest))].T).T[:, :3][f]
    down = S0i[:3, :3] @ np.array([0, -1.0, 0])
    ax = np.cross(down, n); ax /= np.linalg.norm(ax)           # +angle swings the hanging plate toward n
    G[g] = dict(v=v, c=c, n=n, y0=y0, tris=yf, ax=ax, name=g)


def rodr(r):
    th = np.linalg.norm(r)
    if th < 1e-9: return np.eye(3)
    k = r / th; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def log(R):
    th = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
    if th < 1e-6: return np.zeros(3)
    return th / (2 * np.sin(th)) * np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])


def kabsch(P, Q):
    U, s, Vt = np.linalg.svd(P.T @ Q)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    return Vt.T @ np.diag([1, 1, d]) @ U.T


def depth(points, g, R):
    """Largest distance of points beyond the plate (R-rotated about its hinge) plus MARGIN clearance, 0 when clear."""
    c = G[g]['c']; p = (points - c) @ R + c                    # into the plate's rest frame (R^T q)
    T = G[g]['tris']; cen = T.mean(1)
    # only points near the plate
    near = cKDTree(cen).query(p, k=min(16, len(cen)))[1].reshape(len(p), -1)
    a_, b_, c_ = T[near.ravel(), 0], T[near.ravel(), 1], T[near.ravel(), 2]
    pts = np.repeat(p, near.shape[1], 0)
    q, _ = closest_on_triangles(pts, a_, b_, c_)
    d = np.linalg.norm(pts - q, axis=1).reshape(near.shape); bi = d.argmin(1); r = np.arange(len(p))
    f = near[r, bi]; cp = q.reshape(*near.shape, 3)[r, bi]; v = p - cp
    nrm = np.cross(T[f, 1] - T[f, 0], T[f, 2] - T[f, 0]); nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)
    s = np.einsum('ij,ij->i', v, nrm); dist = d[r, bi]
    foot = np.abs(s) > 0.97 * dist                              # the foot lies on the plate, not past its edge
    hit = foot & (s > -MARGIN) & (dist < 0.25)
    return float((s[hit] + MARGIN).max()) if hit.any() else 0.0


def leg_points(mw, x):
    pts = []
    for s, ids in (('R', (3, 37, 12)), ('L', (103, 137, 112))):
        kn = mw[names.index(f'Bip01 {s} Calf')][:3, 3]
        mask = np.isin(pid, ids[:2]) | ((pid == ids[2]) & (np.linalg.norm(x - kn, axis=1) < 0.16))
        pts.append(x[mask])
    return np.vstack(pts)


def swing_axis(r, ax, g=''):
    """Unit axis of the extra turn: fore and aft for front and back plates; side plates: the approved swing when it already goes
    outward, else the plate's top edge; continuous."""
    if g.startswith(('front', 'back')): return ax
    th = np.linalg.norm(r)
    if th < 1e-6: return ax
    u = r / th; out = max(0.0, float(u @ ax)) * min(1.0, th / np.radians(8))
    v = ax * (1 - out) + u * out * 1.6
    return v / np.linalg.norm(v)


def smooth(arr, sigma, loop, dt):
    return gaussian_filter1d(arr, sigma / dt, axis=0, mode='wrap' if loop else 'nearest')


anim = gOld.json['animations']
out = {}; report = {}
for clip in [a_['name'] for a_ in anim]:
    if clip in ('Dead', 'Dead2'): continue
    T = np.array(sorted(mO.clip_times(clip))); n = len(T); dt = (T[-1] - T[0]) / max(1, n - 1); loop = clip in LOOPS
    frames = []
    for t in T:
        w = mO.world(mO.sample(clip, float(t))); x = mO.skinned_positions(w)[0][0]
        Si = np.linalg.inv(w[SP]); y = (Si @ np.c_[x, np.ones(len(x))].T).T[:, :3]
        frames.append((y, (Si @ np.c_[leg_points(w, x), np.ones(len(leg_points(w, x)))].T).T[:, :3]))
    base = {}
    for g, d in G.items():
        r = np.array([log(kabsch(d['y0'] - d['c'], y[d['v']] - d['c'])) for y, _ in frames])
        if loop: r[-1] = r[0]
        base[g] = smooth(r, SIGMA_BASE, loop, dt)
    raw = {g: np.zeros(n) for g in G}
    final = {}
    for it in range(4):
        for g, d in G.items():
            for k, (_, q) in enumerate(frames):
                if it and raw[g][k] >= MAXDEG: continue
                start = 0.0 if it == 0 else final[g][k]
                ang = start
                while ang <= MAXDEG:
                    R = rodr(swing_axis(base[g][k], d['ax'], g) * np.radians(ang)) @ rodr(base[g][k])
                    if depth(q, g, R) == 0.0: break
                    ang += STEP
                raw[g][k] = max(raw[g][k], min(ang, MAXDEG) + (STEP if it else 0))
        final = {}
        for g in G:
            e = raw[g].copy()
            if loop: e[-1] = e[0] = max(e[0], e[-1])
            else: e = np.minimum(e, CAP_ONESHOT['front' if g.startswith('front') else 'other'])
            size = max(1, int(round(2 * (HOLD if loop else 2 * HOLD) / dt)) | 1)   # one-shots: slower, they need no zero and must not snap
            e = maximum_filter1d(e, size, mode='wrap' if loop else 'nearest')
            final[g] = smooth(e, SIGMA if loop else 2 * SIGMA, loop, dt)
        for _ in range(2):
            for i, g in enumerate(RING):
                nb = max(final[RING[i - 1]], final[RING[(i + 1) % 8]], key=lambda a_: a_.max())
                final[g] = np.maximum(final[g], NEIGHBOUR * np.maximum(final[RING[i - 1]], final[RING[(i + 1) % 8]]))
        if not loop:                     # one-shots begin and end on the standing plate
            ramp = np.minimum(1.0, np.minimum(T - T[0], T[-1] - T) / 0.1) if clip not in ('Death', 'Death2') else np.minimum(1.0, (T - T[0]) / 0.1)
            for g in G: final[g] = final[g] * ramp * ONESHOT.get(clip, 1.0)
    rot = {}
    for g, d in G.items():
        # a side plate leans forward with the front plate beside it (FOLLOW of its turn, fore and aft), so the two stay closer
        lead = {'side_R': 'front_R', 'side_L': 'front_L'}.get(g)
        rot[g] = [(rodr(G[lead]['ax'] * np.radians(FOLLOW * final[lead][k])) if lead else np.eye(3))
                  @ rodr(swing_axis(base[g][k], d['ax'], g) * np.radians(final[g][k])) @ rodr(base[g][k]) for k in range(n)]
        if loop: rot[g][-1] = rot[g][0]
    out[clip] = (T, rot)
    report[clip] = {g: round(float(final[g].max()), 1) for g in G}
    print('CLIP', clip, n, report[clip], flush=True)
# Dead / Dead2: the last key of Death / Death2
for dead, death in (('Dead', 'Death'), ('Dead2', 'Death2')):
    if dead in out or death not in out: continue
    T_d = np.array(sorted(mO.clip_times(dead)))
    out[dead] = (T_d, {g: [out[death][1][g][-1]] * len(T_d) for g in G})


def matq(m):
    t = np.trace(m)
    if t > 0:
        s = np.sqrt(t + 1) * 2; q = [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, s / 4]
    else:
        i = int(np.argmax(np.diag(m))); j, k = (i + 1) % 3, (i + 2) % 3
        s = np.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2; q = [0, 0, 0, 0]
        q[i] = s / 4; q[j] = (m[j, i] + m[i, j]) / s; q[k] = (m[k, i] + m[i, k]) / s; q[3] = (m[k, j] - m[j, k]) / s
    q = np.array(q); return q / np.linalg.norm(q)


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])


for an in gNew.json['animations']:
    T, rot = out[an['name']]
    for ch in an['channels']:
        nm = namesN[ch['target']['node']]
        if not nm.startswith('Skirt_') or ch['target']['path'] != 'rotation': continue
        g = nm[len('Skirt_'):]; sm = an['samplers'][ch['sampler']]
        ti = gNew.accessor(sm['input']).ravel()
        q0 = np.array(gNew.json['nodes'][ch['target']['node']].get('rotation', [0, 0, 0, 1]), float)
        vals = np.array([qmul(matq(R), q0) for R in rot[g]])
        if len(ti) != len(vals):
            idx = np.clip(np.searchsorted(T, ti), 0, len(T) - 1); vals = vals[idx]
        for k in range(1, len(vals)):
            if vals[k] @ vals[k - 1] < 0: vals[k] = -vals[k]
        sm['output'] = gNew.append_accessor(vals.astype(np.float32), 'VEC4')
gNew.write(OUT)
json.dump(report, open(REP, 'w'), indent=1)
print('SKIRT keys written', OUT)
