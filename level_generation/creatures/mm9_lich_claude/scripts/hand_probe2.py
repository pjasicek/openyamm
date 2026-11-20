import numpy as np, heapq
from collections import defaultdict
d = np.load('work/step1.npz'); v, f, part = d['v'], d['f'], d['part']
pid = 10
fm = part == pid; ids = np.unique(f[fm]); idx = {int(i): k for k, i in enumerate(ids)}
p = v[ids].copy()
print(len(p), p.min(0).round(3), p.max(0).round(3))
adj = defaultdict(set)
for t in f[fm]:
    for a, b in ((0, 1), (1, 2), (2, 0)):
        i, j = idx[int(t[a])], idx[int(t[b])]; adj[i].add(j); adj[j].add(i)
for z in np.arange(1.14, 0.84, -0.02):
    m = np.abs(p[:, 2] - z) < 0.01
    I = np.nonzero(m)[0]; S = set(I.tolist()); seen = set(); cs = []
    for i in I:
        if int(i) in seen: continue
        st = [int(i)]; seen.add(int(i)); c = []
        while st:
            x = st.pop(); c.append(x)
            for y in adj[x]:
                if y in S and y not in seen: seen.add(y); st.append(y)
        cs.append(c)
    print(round(float(z), 2), [(len(c), p[c].mean(0).round(3).tolist(), round(float((p[c].max(0) - p[c].min(0)).max()), 3)) for c in cs])
