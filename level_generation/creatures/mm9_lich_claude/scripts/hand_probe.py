import sys, numpy as np, heapq
from collections import defaultdict
d = np.load('work/step1.npz'); v, f, part = d['v'], d['f'], d['part']
J = dict(zip(d['bn'].tolist(), d['J']))
for pid in (3, 10):
    fm = part == pid; ids = np.unique(f[fm]); idx = {int(i): k for k, i in enumerate(ids)}
    p = v[ids]; print('part', pid, len(ids), p.min(0).round(3), p.max(0).round(3))
    adj = defaultdict(list)
    for t in f[fm]:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            i, j = idx[int(t[a])], idx[int(t[b])]; w = np.linalg.norm(p[i] - p[j]); adj[i].append((j, w)); adj[j].append((i, w))
    # start: the end of the open forearm ring = highest z region near loop
    deg = defaultdict(int)
    from collections import Counter
    ec = Counter()
    for t in f[fm]:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            ec[tuple(sorted((int(t[a]), int(t[b]))))] += 1
    ring = sorted({idx[x] for e, c in ec.items() if c == 1 for x in e})
    print(' ring verts', len(ring), p[ring].mean(0).round(3))
    D = np.full(len(p), 1e9); h = []
    for r in ring:
        D[r] = 0; heapq.heappush(h, (0, r))
    while h:
        x, i = heapq.heappop(h)
        if x > D[i]: continue
        for j, w in adj[i]:
            if x + w < D[j]: D[j] = x + w; heapq.heappush(h, (D[j], j))
    print(' max geodesic', D.max().round(3))
    for t in np.arange(0.1, D.max(), 0.02):
        keep = D > t; seen = set(); comps = []
        for i in np.nonzero(keep)[0]:
            if i in seen: continue
            st = [i]; seen.add(i); c = []
            while st:
                x = st.pop(); c.append(x)
                for j, _ in adj[x]:
                    if keep[j] and j not in seen: seen.add(j); st.append(j)
            comps.append(c)
        if len(comps) > 1:
            print(f'  t={t:.2f}', [ (len(c), p[c].mean(0).round(2).tolist(), round(float(D[c].max()),2)) for c in comps])
