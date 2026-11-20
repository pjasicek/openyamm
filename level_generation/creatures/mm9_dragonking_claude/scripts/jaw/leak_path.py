"""Shortest vertex path between the snout top and the chin on the main shell, limited to y < RIP_END: where the
upper and lower jaw still connect. Args: -- <blend> [rip_end]"""
import bpy, sys, os, bmesh, heapq
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mouth_common as M
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); RIP = float(a[1]) if len(a) > 1 else -3.40
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = M.parts(bm); shell = np.bincount(comp).argmax()
CO = np.array([tuple(v.co) for v in bm.verts])
ok = (comp == shell) & (CO[:, 1] < RIP) & (CO[:, 2] > 14.3) & (np.abs(CO[:, 0]) < 1.0)
idx = np.nonzero(ok)[0]
s = idx[np.argmax(CO[idx, 2] - 2 * np.abs(CO[idx, 0]) + 0.3 * (CO[idx, 1] < -4.4))]
t = idx[np.argmin(CO[idx, 2] + 2 * np.abs(CO[idx, 0]))]
dist = {s: 0.0}; prev = {}; pq = [(0.0, s)]
while pq:
    d, u = heapq.heappop(pq)
    if u == t: break
    if d > dist.get(u, 1e9): continue
    for e in bm.verts[u].link_edges:
        w = e.other_vert(bm.verts[u]).index
        if not ok[w]: continue
        nd = d + e.calc_length()
        if nd < dist.get(w, 1e9):
            dist[w] = nd; prev[w] = u; heapq.heappush(pq, (nd, w))
if t not in dist:
    print('NO PATH (jaws separated)'); sys.exit()
path = [t]
while path[-1] != s: path.append(prev[path[-1]])
print('PATH len', len(path))
for i in path[::-1]:
    print(np.round(CO[i], 3))
