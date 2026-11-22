"""Finger centrelines from the skin (work/clean_v2.blend): geodesic distance from the palm centre on the skin graph,
fingertips = its five strongest local maxima; per tip, iso-distance rings every 5 mm (the ring component nearest the
previous centre) give centre and radius until the ring widens into the palm. Writes work/fingers.json."""
import bpy, os, json, heapq
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
me = bpy.data.objects['Hand'].data
pa = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', pa)
co = np.array([tuple(v.co) for v in me.vertices])
skinv = set()
for p in me.polygons:
    if pa[p.index] in (0, 1): skinv.update(p.vertices)
adj = {v: set() for v in skinv}
for e in me.edges:
    a, b = e.vertices
    if a in skinv and b in skinv: adj[a].add(b); adj[b].add(a)


def dijkstra(src):
    d = {src: 0.0}; h = [(0.0, src)]
    while h:
        x, v = heapq.heappop(h)
        if x > d[v]: continue
        for o in adj[v]:
            y = x + float(np.linalg.norm(co[o] - co[v]))
            if y < d.get(o, 1e9): d[o] = y; heapq.heappush(h, (y, o))
    return d


M = json.load(open(os.path.join(HERE, 'work', 'mouth.json')))
O = np.array(M['O'])
sk = np.array(sorted(skinv))
seed = int(sk[np.argmin(np.linalg.norm(co[sk] - O, axis=1))])
g = dijkstra(seed)
# local maxima within 6 cm geodesic
cand = sorted(skinv, key=lambda v: -g[v])
tips = []
for v in cand:
    if g[v] < 0.12: break
    if co[v][1] > -0.06: continue          # fingertips curl toward the palm side (-Y); back-of-hand bumps are not tips
    if all(np.linalg.norm(co[v] - co[t]) > 0.07 for t in tips):
        # local max check: no vertex within 3 cm euclidean has larger g
        near = sk[np.linalg.norm(co[sk] - co[v], axis=1) < 0.03]
        if all(g[int(u)] <= g[v] + 1e-9 for u in near):
            tips.append(v)
print('TIPS', [(int(t), np.round(co[t], 3).tolist(), round(g[t], 3)) for t in tips])
out = {}
edges = [(a, b) for a in adj for b in adj[a] if a < b]
for t in tips:
    gt = dijkstra(t)
    prev = co[t]; cents = []; radii = []
    for dd in np.arange(0.006, 0.50, 0.005):
        pts = []; ev = []
        for a, b in edges:
            ga, gb = gt[a], gt[b]
            if (ga - dd) * (gb - dd) < 0:
                w = (dd - ga) / (gb - ga); pts.append(co[a] + (co[b] - co[a]) * w); ev.append((a, b))
        if len(pts) < 3: continue
        pts = np.array(pts)
        # components of the contour: crossing edges sharing a face-neighbour vertex are linked (cheap: by distance)
        lab = -np.ones(len(pts), int); k = 0
        for i in range(len(pts)):
            if lab[i] >= 0: continue
            st = [i]; lab[i] = k
            while st:
                x = st.pop()
                near = np.nonzero((lab < 0) & (np.linalg.norm(pts - pts[x], axis=1) < 0.02))[0]
                for j in near: lab[j] = k; st.append(j)
            k += 1
        best = min(range(k), key=lambda c: np.linalg.norm(pts[lab == c].mean(0) - prev))
        P = pts[lab == best]; cc = P.mean(0); rr = float(np.linalg.norm(P - cc, axis=1).mean())
        cents.append(cc.tolist()); radii.append(rr); prev = cc
    out[str(t)] = {'tip': co[t].tolist(), 'centres': cents, 'radii': radii}
    print('FINGER', t, np.round(co[t], 3).tolist(), 'radii', ' '.join(f'{r*100:.1f}' for r in radii[:45]))
json.dump({'seed': seed, 'fingers': out}, open(os.path.join(HERE, 'work', 'fingers.json'), 'w'))
