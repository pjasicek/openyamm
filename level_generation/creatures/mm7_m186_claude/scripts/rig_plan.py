"""Dragonfly skeleton and skin weights from the Meshy mesh (work/raw_st1.npz, Meshy frame):
- centerline: surface shortest path claw -> head, refined to cross-section centroids (work/centerline_raw.npy);
- chain bones on it: Thorax (root) -> Abd1..Abd9 down to the claw base -> Claw; Thorax -> Neck -> Head;
- the traced line is smoothed and the abdomen joints are spaced evenly by arc length; main-body weights are hat
  functions of each vertex's arc position (nearest sample of the dense centerline) between neighbouring bone centres; separate pieces (spine crest, bristles, mandibles, claw prongs) take the weights of their
  nearest main-body vertex; each wing piece is bound 100 % to its wing bone.
Writes work/rig_plan.json (bones: head/tail/parent in the Meshy frame) and work/weights.npz."""
import json, heapq, collections
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[1]
d = np.load(P / 'work/raw_st1.npz'); co, tri, part = d['co'], d['tri'], d['part']
main = part == 0
adj = collections.defaultdict(list)
for a, b, c in tri:
    for u, v in ((a, b), (b, c), (c, a)):
        if main[u] and main[v]:
            w = np.linalg.norm(co[u] - co[v]); adj[u].append((v, w)); adj[v].append((u, w))
idx = np.nonzero(main)[0]
tail = idx[np.argmin(co[idx, 2])]; head = idx[np.argmin(co[idx, 1])]
dist = {tail: 0}; prev = {}; pq = [(0, tail)]
while pq:
    dd, u = heapq.heappop(pq)
    if dd > dist.get(u, 1e9): continue
    for v, w in adj[u]:
        if dd + w < dist.get(v, 1e9): dist[v] = dd + w; prev[v] = u; heapq.heappush(pq, (dd + w, v))
path = [head]
while path[-1] != tail: path.append(prev[path[-1]])
Pp = co[path[::-1]]
L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pp, axis=0), axis=1))]
s = np.linspace(0, L[-1], 40); C = np.array([np.interp(s, L, Pp[:, k]) for k in range(3)]).T
body = co[idx]
for _ in range(4):
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]; newC = C.copy()
    for i in range(len(C)):
        dv = body - C[i]; along = dv @ T[i]; perp = np.linalg.norm(dv - np.outer(along, T[i]), axis=1)
        sel = (np.abs(along) < 0.008) & (perp < 0.045)
        if sel.sum() > 5: newC[i] = body[sel].mean(0)
    C = newC
np.save(P / 'work/centerline_raw.npy', C)
# smooth the traced centerline (ends fixed) and resample densely by arc length
Cs = C.copy()
for _ in range(6):
    Cs[1:-1] = (Cs[:-2] + 2 * Cs[1:-1] + Cs[2:]) / 4
seg = np.linalg.norm(np.diff(Cs, axis=0), axis=1); arc = np.r_[0, np.cumsum(seg)]
S = np.linspace(0, arc[-1], 400); D = np.array([np.interp(S, arc, Cs[:, k]) for k in range(3)]).T
at = lambda i: float(arc[i])                       # arc position of a traced index
curve = lambda s_: np.array([np.interp(s_, S, D[:, k]) for k in range(3)])
s_claw, s_thorax, s_neck, s_head, s_snout = at(6), at(26), at(28), at(31), at(38)
abd_s = np.linspace(s_thorax, s_claw, 11)          # Abd1 starts at the thorax, Abd10 ends at the claw base
J = lambda s_: curve(s_).tolist()
claw_tip = co[part == 3].mean(0) * .5 + co[part == 6].mean(0) * .5
bones = [('Thorax', None, J(s_thorax), J(s_neck))]
for k in range(10):
    bones.append((f'Abd{k + 1}', 'Thorax' if k == 0 else f'Abd{k}', J(abd_s[k]), J(abd_s[k + 1])))
bones.append(('Claw', 'Abd10', J(s_claw), claw_tip.tolist()))
bones.append(('Neck', 'Thorax', J(s_neck), J(s_head)))
bones.append(('Head', 'Neck', J(s_head), J(s_snout)))
WINGS = {1: 'ForeWing_L', 2: 'ForeWing_R', 4: 'HindWing_L', 5: 'HindWing_R'}
for k, name in WINGS.items():
    p = co[part == k]; ax = np.abs(p[:, 0])
    bones.append((name, 'Thorax', p[ax < ax.min() + 0.02].mean(0).tolist(), p[np.argmax(ax)].tolist()))
names = [b[0] for b in bones]
W = np.zeros((len(co), len(names)), np.float32)
# continuous arc position of each main vertex = arc of its nearest dense centerline sample; bone weights are hat
# functions between neighbouring bone centres along the chain (claw end and head end rigid)
chain = [('Claw', s_claw - 0.03, s_claw)] + [(f'Abd{k}', abd_s[k], abd_s[k - 1]) for k in range(10, 0, -1)] + \
        [('Thorax', s_thorax, s_neck), ('Neck', s_neck, s_head), ('Head', s_head, s_snout + 0.05)]
centres = np.array([(a_ + b_) / 2 for _, a_, b_ in chain])
centres[0] = s_claw - 0.01; centres[-1] = s_head + 0.02
mi = np.nonzero(main)[0]
sv = S[cKDTree(D).query(co[mi])[1]]
for v, s_ in zip(mi, sv):
    j = int(np.clip(np.searchsorted(centres, s_) - 1, 0, len(centres) - 2))
    f = float(np.clip((s_ - centres[j]) / (centres[j + 1] - centres[j]), 0, 1))
    W[v, names.index(chain[j][0])] += 1 - f; W[v, names.index(chain[j + 1][0])] += f
# rigid pieces
tree = cKDTree(co[mi])
for k in range(1, part.max() + 1):
    sel = np.nonzero(part == k)[0]
    if k in WINGS:
        W[sel] = 0; W[sel, names.index(WINGS[k])] = 1; continue
    c = co[sel].mean(0)
    near = mi[tree.query(co[sel])[1]]
    anchor = near[np.argmin(np.linalg.norm(co[near] - c, axis=1))]
    W[sel] = W[anchor]
assert np.allclose(W.sum(1), 1, atol=1e-5), W.sum(1).min()
np.savez(P / 'work/weights.npz', W=W, names=np.array(names))
json.dump({'bones': [(n, p_, list(h), list(t)) for n, p_, h, t in bones], 'centerline': Cs.tolist()}, open(P / 'work/rig_plan.json', 'w'), indent=1)
print('PLAN', len(names), 'bones;', {n: round(float(W[:, i].sum()), 1) for i, n in enumerate(names)})
