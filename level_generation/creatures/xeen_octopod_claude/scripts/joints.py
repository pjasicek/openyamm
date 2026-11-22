#!/usr/bin/env python3
"""Tentacle centrelines and skin weights of the cleaned octopod (work/clean.npz from dump_raw.py clean_v1.blend clean).
Per tentacle k (azimuth from work/clean_info.json, 0 = -Y, + toward +X):
  - its vertices: body vertices whose nearest tentacle axis is k and that lie beyond ALONG0 along it;
  - a geodesic distance over its own surface from the seed ring (ALONG_SEED .. +0.02 m along its axis), binned
    (BIN m) into cross-section rings whose centroids give the centreline (it follows the hooked tip);
  - joints: J0 inside the head base (HUB along, the seed ring's height), then N_SEG bones from J0 to the tip by equal
    arc length of the centreline.
Weights: tentacle vertices on their chain by arc position s (hat functions peaking at bone midpoints: smooth bends),
eased into the head over the web (along HUB_EASE[0]..HUB_EASE[1]); the rest of the body on Head (dome, smoothstep of
height) and Body (the web and the beard's base); suckers rigidly with the body vertex nearest their centre; eyes on Head.
Writes work/rig_v1.json (joints, weights per vertex as [bone, weight] lists)."""
import json, heapq
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
d = np.load(ROOT / 'work/clean.npz'); co = d['co']; tris = d['tris']; fpart = d['fpart']
info = json.load(open(ROOT / 'work/clean_info.json'))
ARMS = np.radians(info['arms_deg'])
N_SEG = 8
ALONG0, ALONG_SEED, HUB = 0.27, 0.30, 0.12
HUB_EASE = (0.20, 0.36)
BIN = 0.025

nv = len(co)
vpart = np.full(nv, -1)
for t, p in zip(tris, fpart):
    for v in t:
        vpart[v] = p if vpart[v] < 0 else min(vpart[v], p)
body = vpart == 0
# adjacency (body triangles only)
adj = [[] for _ in range(nv)]
for t, p in zip(tris, fpart):
    if p != 0: continue
    for i in range(3):
        a, b = t[i], t[(i + 1) % 3]
        L = float(np.linalg.norm(co[a] - co[b]))
        adj[a].append((b, L)); adj[b].append((a, L))

az = np.arctan2(co[:, 0], -co[:, 1])
dk = np.abs(np.angle(np.exp(1j * (az[:, None] - ARMS[None, :]))))
nearest = np.argmin(dk, 1)
dirs = np.stack([np.sin(ARMS), -np.cos(ARMS), np.zeros(8)], -1)
along = co @ dirs.T                                          # (nv, 8)

arms = []
arm_of = -np.ones(nv, int); s_of = np.full(nv, np.nan)
for k in range(8):
    mine = body & (nearest == k) & (along[:, k] > ALONG0)
    seeds = np.where(mine & (along[:, k] < ALONG_SEED + 0.02) & (along[:, k] >= ALONG_SEED))[0]
    g = np.full(nv, np.inf); pq = []
    for s in seeds:
        g[s] = along[s, k] - ALONG_SEED; heapq.heappush(pq, (g[s], s))
    while pq:
        dist, v = heapq.heappop(pq)
        if dist > g[v]: continue
        for w, L in adj[v]:
            if not mine[w]: continue
            nd = dist + L
            if nd < g[w]:
                g[w] = nd; heapq.heappush(pq, (nd, w))
    reach = mine & np.isfinite(g)
    # vertices between ALONG0 and the seed ring: negative s by their axis distance
    pre = reach & (along[:, k] < ALONG_SEED)
    g[pre] = along[pre, k] - ALONG_SEED
    idx = np.where(reach)[0]
    gmax = g[idx].max()
    nb = int(np.ceil(gmax / BIN))
    cl = []
    for b in range(nb):
        sel = idx[(g[idx] >= b * BIN) & (g[idx] < (b + 1) * BIN)]
        if len(sel) >= 3:
            cl.append(co[sel].mean(0))
    tip = co[idx[np.argmax(g[idx])]]
    cl.append(tip)
    cl = np.array(cl)
    # smooth the centreline (keep the ends)
    sm = cl.copy()
    for _ in range(3):
        sm[1:-1] = 0.25 * sm[:-2] + 0.5 * sm[1:-1] + 0.25 * sm[2:]
    seed_c = co[seeds].mean(0)
    j0 = np.array([dirs[k, 0] * HUB, dirs[k, 1] * HUB, seed_c[2]])
    poly = np.vstack([j0, sm])
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); arc = np.concatenate([[0], np.cumsum(seg)])
    targets = np.linspace(0, arc[-1], N_SEG + 1)
    J = np.stack([np.interp(targets, arc, poly[:, c]) for c in range(3)], -1)
    # arc position of the seed ring on the chain (where g = 0)
    s0 = float(np.linalg.norm(seed_c - j0))
    arms.append({'k': k, 'azimuth_deg': float(np.degrees(ARMS[k])), 'joints': J.round(5).tolist(),
                 'length': float(arc[-1]), 'seed_s': s0, 'gmax': float(gmax), 'centreline': sm.round(4).tolist()})
    arm_of[idx] = k
    # chain arc position: s = s0 + g (geodesic approximates arc length beyond the seed ring)
    s_of[idx] = s0 + g[idx]
    print(f'ARM {k} az {np.degrees(ARMS[k]):6.1f} verts {len(idx):4d} length {arc[-1]:.3f} tip {tip.round(3)} '
          f'z-range [{J[:, 2].min():+.3f},{J[:, 2].max():+.3f}]')

BONES = ['Root', 'Body', 'Head'] + [f'Arm{k}_{i + 1}' for k in range(8) for i in range(N_SEG)]
W = [dict() for _ in range(nv)]


def smoothstep(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


for v in np.where(body)[0]:
    z = co[v, 2]
    head_w = float(smoothstep(z, 0.12, 0.26))
    base = {'Head': head_w, 'Body': 1 - head_w}
    k = arm_of[v] if arm_of[v] >= 0 else nearest[v]
    a = along[v, k]
    ease = float(smoothstep(a, *HUB_EASE))
    if arm_of[v] < 0 and a < ALONG0:
        ease = 0.0
    chain = {}
    if ease > 0:
        A = arms[k]; J = np.array(A['joints'])
        sj = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(J, axis=0), axis=1))])
        mids = (sj[:-1] + sj[1:]) / 2
        s = s_of[v] if np.isfinite(s_of[v]) else A['seed_s'] + (a - ALONG_SEED)
        if s <= mids[0]:
            chain = {0: 1.0}
        elif s >= mids[-1]:
            chain = {N_SEG - 1: 1.0}
        else:
            i = int(np.searchsorted(mids, s) - 1)
            f = (s - mids[i]) / (mids[i + 1] - mids[i])
            chain = {i: 1 - f, i + 1: f}
    w = {n: x * (1 - ease) for n, x in base.items() if x * (1 - ease) > 1e-4}
    for i, x in chain.items():
        w[f'Arm{k}_{i + 1}'] = w.get(f'Arm{k}_{i + 1}', 0) + x * ease
    W[v] = w

# suckers: rigid on the nearest body vertex's weights (per piece); eyes on Head
lab = -np.ones(nv, int); par = np.arange(nv)


def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x


for t in tris:
    a = find(t[0])
    for b in t[1:]:
        b = find(b)
        if a != b: par[b] = a
lab = np.array([find(i) for i in range(nv)])
bidx = np.where(body)[0]
for piece in np.unique(lab[vpart == 1]):
    sel = np.where(lab == piece)[0]
    c = co[sel].mean(0)
    nn = bidx[np.argmin(((co[bidx] - c) ** 2).sum(-1))]
    for v in sel:
        W[v] = dict(W[nn])
for v in np.where(vpart == 2)[0]:
    W[v] = {'Head': 1.0}
unw = sum(1 for w in W if not w)
print('UNWEIGHTED', unw)
json.dump({'bones': BONES, 'arms': arms, 'n_seg': N_SEG, 'hub': HUB,
           'weights': [[[n, round(x, 5)] for n, x in w.items()] for w in W]},
          open(ROOT / 'work/rig_v1.json', 'w'))
print('RIG json written')
