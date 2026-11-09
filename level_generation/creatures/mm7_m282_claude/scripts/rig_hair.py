"""Hair-snake chains on the Medusa rig: work/rig_v2.blend -> work/rig_v3.blend (+ work/hair.json).
Each hair-snake piece (step1 piece ids, rig_medusa.HAIR) gets a two-bone chain Hair_<k>_1/2 (child of Head) along its
own centreline: geodesic distance over the piece from its scalp end (the vertices nearest the skull centre), band
centroids at 0, 0.35 and 1.0 of the piece's length. Weights replace the old height blend: Head at the root, then the
chain by geodesic position (linear between Head at s=0.12 L, bone 1 at 0.45 L, bone 2 at 0.85 L).
anim_medusa.py poses the chains: hanging snakes partly follow the chest (gravity), a slow writhe, and a floor rule
(each bone end kept above the floor) so the corpse's snakes rest on the floor instead of passing through it."""
import bpy, os, json, heapq
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(HERE, 'work', *p)
bpy.ops.wm.open_mainfile(filepath=W('rig_v2.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
HAIR = [1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 23, 24, 35]
co = np.array([tuple(v.co) for v in me.vertices]); pv = np.zeros(len(co), np.int32)
me.attributes['piece'].data.foreach_get('value', pv)
adj = [[] for _ in co]
for e in me.edges:
    a, b = e.vertices; adj[a].append(b); adj[b].append(a)
SKULL = np.array([0.0, 0.21, 1.62])


def geodesic(ids, seeds):
    allowed = set(int(i) for i in ids); dist = {int(s): 0.0 for s in seeds}; q = [(0.0, int(s)) for s in seeds]
    heapq.heapify(q)
    while q:
        d, v = heapq.heappop(q)
        if d > dist[v] + 1e-12:
            continue
        for w in adj[v]:
            if w in allowed:
                nd = d + float(np.linalg.norm(co[w] - co[v]))
                if nd < dist.get(w, 1e9):
                    dist[w] = nd; heapq.heappush(q, (nd, w))
    return np.array([dist.get(int(i), 1e9) for i in ids])


chains = []
for k, p in enumerate(HAIR):
    ids = np.where(pv == p)[0]
    dsk = np.linalg.norm(co[ids] - SKULL, axis=1)
    seeds = ids[np.argsort(dsk)[:max(3, len(ids) // 30)]]
    g = geodesic(ids, seeds); g[g > 1e8] = g[g < 1e8].max()
    L = float(np.percentile(g, 98))
    pts = []
    for f in (0.0, 0.35, 1.0):
        m = np.abs(g - f * L) < max(0.02, L * 0.08)
        pts.append(co[ids[m]].mean(0) if m.any() else co[ids[np.argmin(np.abs(g - f * L))]])
    det = bool(np.linalg.norm(pts[0] - SKULL) > 0.16)
    if det:                                                 # a floating side curl: its chain starts at the skull so it can swing
        pts = [SKULL + (pts[0] - SKULL) * 0.45, pts[0], pts[2]]
    c = co[ids].mean(0)
    kind = 'side' if abs(c[0]) > 0.17 else ('back' if c[1] > 0.30 else ('front' if c[1] < 0.16 and c[2] < 1.5 else 'top'))
    chains.append({'piece': p, 'ids': ids, 'g': g, 'L': L, 'pts': pts, 'kind': kind, 'detached': det})
    print('HAIR', p, 'verts', len(ids), 'len %.3f' % L, kind, np.round(pts[0], 3), np.round(pts[-1], 3))
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for k, c in enumerate(chains):
    for j in (1, 2):
        b = eb.new(f'Hair_{k:02d}_{j}')
        b.head = Vector(c['pts'][j - 1]); b.tail = Vector(c['pts'][j])
        if (b.tail - b.head).length < 0.01:
            b.tail = b.head + Vector((0, 0, 0.02))
        b.align_roll(Vector((0, 0, 1)) if abs((b.tail - b.head).normalized().z) < 0.9 else Vector((0, -1, 0)))
        b.parent = eb['Head'] if j == 1 else eb[f'Hair_{k:02d}_1']; b.use_connect = j == 2
bpy.ops.object.mode_set(mode='OBJECT')
for k, c in enumerate(chains):
    for j in (1, 2):
        if f'Hair_{k:02d}_{j}' not in body.vertex_groups:
            body.vertex_groups.new(name=f'Hair_{k:02d}_{j}')
gH = body.vertex_groups['Head']
for k, c in enumerate(chains):
    g1, g2 = body.vertex_groups[f'Hair_{k:02d}_1'], body.vertex_groups[f'Hair_{k:02d}_2']
    detached = c['detached']
    for v, s in zip(c['ids'], c['g'] / max(c['L'], 1e-4)):
        v = int(v)
        if detached:
            s = 0.45 + 0.4 * s                               # rigid on bone 1 at its inner end, bending into bone 2
        for grp in body.vertex_groups:
            grp.remove([v])
        if s <= 0.12:
            w = (1.0, 0.0, 0.0)
        elif s <= 0.45:
            f = (s - 0.12) / 0.33; w = (1 - f, f, 0.0)
        elif s <= 0.85:
            f = (s - 0.45) / 0.40; w = (0.0, 1 - f, f)
        else:
            w = (0.0, 0.0, 1.0)
        for grp, x in zip((gH, g1, g2), w):
            if x > 1e-4:
                grp.add([v], x, 'REPLACE')
json.dump([{'k': k, 'piece': c['piece'], 'kind': c['kind'], 'L': c['L'], 'pts': [list(map(float, p)) for p in c['pts']]}
           for k, c in enumerate(chains)], open(W('hair.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=W('rig_v3.blend'))
print('SAVED rig_v3 hair chains', len(chains))
