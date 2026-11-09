"""Pass 7: boundary loops of each piece of a head npz (co, tri, piece): count, vertex count, bbox. Args: <npz>"""
import sys
import numpy as np
D = np.load(sys.argv[1]); co, tri, pc = D['co'], D['tri'], D['piece']
def loops(t):
    e = np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), 1); u, c = np.unique(e, axis=0, return_counts=True)
    b = u[c == 1]; nm = u[c > 2]
    adj = {}
    for a, b_ in b: adj.setdefault(a, []).append(b_); adj.setdefault(b_, []).append(a)
    seen = set(); out = []
    for s in adj:
        if s in seen: continue
        st = [s]; cur = []; seen.add(s)
        while st:
            x = st.pop(); cur.append(x)
            for y in adj[x]:
                if y not in seen: seen.add(y); st.append(y)
        out.append(np.array(cur))
    return out, len(nm)
for k in np.unique(pc):
    t = tri[(pc[tri] == k).all(1)]; L, nm = loops(t)
    print('PIECE', k, 'faces', len(t), 'loops', len(L), 'nonmanifold edges', nm)
    for l in sorted(L, key=len, reverse=True):
        q = co[l]; print('   loop', len(l), q.min(0).round(3), q.max(0).round(3))
