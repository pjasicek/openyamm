"""m178 body measurements on the skin shell (piece 0) for the G3 joint fit (Meshy's auto-rig joints were unusable in
depth: the shoulders 22 cm behind the back, the spine on the chest's front surface). Writes work/body_slices.json:
- 'torso': horizontal slice loops z 0.80..1.56 (2 cm): per z every loop (centre, perimeter, x/y extent);
- 'legs': horizontal slice loops z 0.02..0.90 per side (loops whose centre has that sign of x, |x| > 3 cm);
- 'tail': geodesic rings (2 cm bands) from the tail tip (the vertex farthest behind / highest at the back);
- 'arm_<s>': rings perpendicular to the local arm axis from the measured shoulder to the hand tip (as arm_rings.py).
Args: -- <blend>"""
import bpy, bmesh, sys, os, json, heapq
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
ob = bpy.data.objects['Body']; me = ob.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
bm0 = bmesh.new(); bm0.from_mesh(me); bm0.verts.ensure_lookup_table()
bmesh.ops.delete(bm0, geom=[v for v in bm0.verts if pv[v.index] != 0], context='VERTS')
co = np.array([tuple(v.co) for v in bm0.verts])


def rings(p, n):
    bm = bm0.copy()
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=Vector(p), plane_no=Vector(n))
    edges = [e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
    adj = {}
    for e in edges:
        a, b = e.verts
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen, out = set(), []
    for v in adj:
        if v in seen:
            continue
        comp, stack = [], [v]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x); comp.append(x); stack.extend(adj[x])
        if len(comp) < 4:
            continue
        ordered = [comp[0]]; left = set(comp[1:])
        while left:
            nxt = next((y for y in adj[ordered[-1]] if y in left), None)
            if nxt is None:
                break
            ordered.append(nxt); left.discard(nxt)
        op = np.array([tuple(x.co) for x in ordered])
        per = float(np.linalg.norm(np.diff(np.vstack([op, op[:1]]), axis=0), axis=1).sum())
        out.append({'c': op.mean(0).round(4).tolist(), 'per': round(per, 4), 'lo': op.min(0).round(4).tolist(),
                    'hi': op.max(0).round(4).tolist()})
    bm.free()
    return out


OUT = {'torso': {}, 'legs': {}}
for z in np.arange(0.70, 1.58, 0.02):
    OUT['torso'][f'{z:.2f}'] = [r for r in rings((0, 0, z), (0, 0, 1)) if r['c'][1] < -0.2]
for z in np.arange(0.02, 0.92, 0.02):
    OUT['legs'][f'{z:.2f}'] = [r for r in rings((0, 0, z), (0, 0, 1)) if r['c'][1] < -0.2 and abs(r['c'][0]) > 0.03]
# tail: geodesic rings from the tail tip (the skin vertex farthest behind)
E = np.array([tuple(v.index for v in e.verts) for e in bm0.edges])
w = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
ADJ = [[] for _ in range(len(co))]
for (a, b), l in zip(E.tolist(), w.tolist()):
    ADJ[a].append((b, l)); ADJ[b].append((a, l))


def dijkstra(t):
    d = np.full(len(co), np.inf); d[t] = 0.0; h = [(0.0, t)]
    while h:
        dv, v = heapq.heappop(h)
        if dv > d[v]:
            continue
        for u, l in ADJ[v]:
            if dv + l < d[u]:
                d[u] = dv + l; heapq.heappush(h, (d[u], u))
    return d


tip = int(np.argmax(co[:, 1] + 0.3 * co[:, 2]))
d = dijkstra(tip); prof = []
for k in range(0, 110):
    m = (d >= k * 0.02) & (d < (k + 1) * 0.02)
    if m.sum() < 3:
        continue
    c = co[m].mean(0)
    prof.append({'d': round(k * 0.02, 3), 'c': c.round(4).tolist(), 'r': round(float(np.linalg.norm(co[m] - c, axis=1).mean()), 4), 'n': int(m.sum())})
OUT['tail'] = {'tip': co[tip].round(4).tolist(), 'profile': prof}
json.dump(OUT, open(os.path.join(HERE, 'work', 'body_slices.json'), 'w'))
print('SLICES torso', len(OUT['torso']), 'legs', len(OUT['legs']), 'tail bands', len(prof), 'tip', co[tip].round(3).tolist())
