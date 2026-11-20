"""Beholder skeleton and weights from the Meshy mesh (work/raw_st1.npz, Meshy frame).
Pieces: 0 head (with drool), 11 central eyeball, 15-33 teeth, tentacles 1,2,3,4,5,6,9,10 and a short back
tentacle 14, eye stalks 7,8,12,13 (stalk and eyeball in one piece).
Every chain piece is traced from its attachment (the vertex nearest the head centre) to its geodesically farthest
vertex: surface shortest path, refined to cross-section centroids and smoothed; its bones split the line evenly by
arc length and its vertices take hat weights of their arc position (as the dragonfly abdomen). Head, teeth and drool
are rigid to Head, the eyeball to EyeBall. Writes work/rig_plan.json and work/weights.npz."""
import json, heapq, collections
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[1]
d = np.load(P / 'work/raw_st1.npz'); co, tri, part = d['co'], d['tri'], d['part']
centre = co[part == 0].mean(0)
TENT = [1, 2, 3, 4, 5, 6, 9, 10, 14]
STALK = [7, 8, 12, 13]
adj = collections.defaultdict(list)
for a, b, c in tri:
    for u, v in ((a, b), (b, c), (c, a)):
        if part[u] == part[v]:
            w = np.linalg.norm(co[u] - co[v]); adj[u].append((v, w)); adj[v].append((u, w))


def dijkstra(src):
    dist = {src: 0.0}; prev = {}; pq = [(0.0, src)]
    while pq:
        dd, u = heapq.heappop(pq)
        if dd > dist.get(u, 1e9): continue
        for v, w in adj[u]:
            if dd + w < dist.get(v, 1e9): dist[v] = dd + w; prev[v] = u; heapq.heappush(pq, (dd + w, v))
    return dist, prev


def trace(k, samples=30):
    idx = np.nonzero(part == k)[0]; pts = co[idx]
    start = idx[np.argmin(np.linalg.norm(pts - centre, axis=1))]
    dist, prev = dijkstra(start)
    end = max(dist, key=dist.get)
    path = [end]
    while path[-1] != start: path.append(prev[path[-1]])
    Pp = co[path[::-1]]
    L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pp, axis=0), axis=1))]
    s = np.linspace(0, L[-1], samples); C = np.array([np.interp(s, L, Pp[:, j]) for j in range(3)]).T
    for _ in range(3):
        T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]; nc = C.copy()
        for i in range(1, len(C) - 1):
            dv = pts - C[i]; al = dv @ T[i]; pe = np.linalg.norm(dv - np.outer(al, T[i]), axis=1)
            sel = (np.abs(al) < 0.006) & (pe < 0.03)
            if sel.sum() > 4: nc[i] = pts[sel].mean(0)
        C = nc
    for _ in range(4): C[1:-1] = (C[:-2] + 2 * C[1:-1] + C[2:]) / 4
    seg = np.linalg.norm(np.diff(C, axis=0), axis=1); arc = np.r_[0, np.cumsum(seg)]
    S = np.linspace(0, arc[-1], 300); D = np.array([np.interp(S, arc, C[:, j]) for j in range(3)]).T
    return idx, S, D


bones = []; chains = {}
body_low = co[part == 0][:, 2].min()
bones.append(('Body', None, [float(centre[0]), float(centre[1]), float(body_low + 0.05)], centre.tolist()))
bones.append(('Head', 'Body', centre.tolist(), [float(centre[0]), float(centre[1]), float(co[part == 0][:, 2].max())]))
eye = co[part == 11]; ec = eye.mean(0); front = eye[np.argmin(eye[:, 1])]
bones.append(('EyeBall', 'Head', ec.tolist(), (ec + (front - ec) / np.linalg.norm(front - ec) * 0.05).tolist()))
bones.append(('EyeSocket', 'EyeBall', front.tolist(), (front + np.array([0, -0.02, 0])).tolist()))
ang = {k: np.arctan2(co[part == k][:, 0].mean() - centre[0], -(co[part == k][:, 1].mean() - centre[1])) for k in TENT + STALK}
order_t = sorted(TENT, key=lambda k: ang[k]); order_s = sorted(STALK, key=lambda k: ang[k])
for prefix, pieces, nb in (('Tentacle', order_t, 5), ('Stalk', order_s, 2)):
    for n, k in enumerate(pieces, 1):
        idx, S, D = trace(k)
        nbk = 3 if k == 14 else nb
        js = np.linspace(0, S[-1], nbk + 1)
        names = [f'{prefix}{n}_{j + 1}' for j in range(nbk)]
        curve = lambda s_: np.array([np.interp(s_, S, D[:, j]) for j in range(3)])
        for j in range(nbk):
            bones.append((names[j], 'Head' if j == 0 else names[j - 1], curve(js[j]).tolist(), curve(js[j + 1]).tolist()))
        chains[k] = (idx, S, D, js, names)
names_all = [b[0] for b in bones]
W = np.zeros((len(co), len(names_all)), np.float32)
for k, (idx, S, D, js, names) in chains.items():
    sv = S[cKDTree(D).query(co[idx])[1]]
    centres = (js[:-1] + js[1:]) / 2
    centres[0] = 0.0; centres[-1] = js[-1]                  # root and tip ends rigid to their bones
    for v, s_ in zip(idx, sv):
        if len(names) == 1:
            W[v, names_all.index(names[0])] = 1; continue
        j = int(np.clip(np.searchsorted(centres, s_) - 1, 0, len(centres) - 2))
        f = float(np.clip((s_ - centres[j]) / (centres[j + 1] - centres[j]), 0, 1))
        W[v, names_all.index(names[j])] += 1 - f; W[v, names_all.index(names[j + 1])] += f
    # the root of each chain is hidden inside the head: its first few mm follow the head
    root = sv < 0.012
    W[idx[root]] = 0; W[idx[root], names_all.index('Head')] = 1
for k in range(part.max() + 1):
    if k in chains: continue
    sel = part == k
    W[sel] = 0; W[sel, names_all.index('EyeBall' if k == 11 else 'Head')] = 1
assert np.allclose(W.sum(1), 1, atol=1e-5)
np.savez(P / 'work/weights.npz', W=W, names=np.array(names_all))
json.dump({'bones': [(n, p_, list(map(float, h)), list(map(float, t))) for n, p_, h, t in bones],
           'tentacles': {f'Tentacle{n}': int(k) for n, k in enumerate(order_t, 1)},
           'stalks': {f'Stalk{n}': int(k) for n, k in enumerate(order_s, 1)}}, open(P / 'work/rig_plan.json', 'w'), indent=1)
print('PLAN', len(names_all), 'bones', json.load(open(P / 'work/rig_plan.json'))['tentacles'], json.load(open(P / 'work/rig_plan.json'))['stalks'])
