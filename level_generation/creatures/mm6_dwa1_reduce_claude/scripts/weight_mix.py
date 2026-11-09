"""Weight mixing check of a ladder candidate (REA_CAND, default Cand_66): per candidate vertex, the weight vector
against the nearest source vertex of the same connected piece; prints pieces whose vertices disagree (L1 > 0.5).
Usage: blender -b -P weight_mix.py"""
import os, bpy, numpy as np
from mathutils import kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
src = bpy.data.objects['Body']; c = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_66')]
def pieces(me):
    p = list(range(len(me.vertices)))
    def f(i):
        while p[i] != i: p[i] = p[p[i]]; i = p[i]
        return i
    for e in me.edges:
        a, b = f(e.vertices[0]), f(e.vertices[1])
        if a != b: p[a] = b
    return np.array([f(i) for i in range(len(me.vertices))])
def wmat(o):
    names = [g.name for g in o.vertex_groups]; out = []
    for v in o.data.vertices:
        w = {names[g.group]: g.weight for g in v.groups if names[g.group] != 'ReduceProtect' and g.weight > 0}
        t = sum(w.values()) or 1; out.append({k: x / t for k, x in w.items()})
    return names, out
sn, sw = wmat(src); cn, cw = wmat(c)
sco = np.array([v.co[:] for v in src.data.vertices]); cco = np.array([v.co[:] for v in c.data.vertices])
spc = pieces(src.data); cpc = pieces(c.data)
full = kdtree.KDTree(len(sco))
for i, co in enumerate(sco): full.insert(co, i)
full.balance()
bad_total = 0
for pc in np.unique(cpc):
    ids = np.flatnonzero(cpc == pc); sp = np.bincount([spc[full.find(cco[i])[1]] for i in ids]).argmax()
    sids = np.flatnonzero(spc == sp); t = kdtree.KDTree(len(sids))
    for j in sids: t.insert(sco[j], int(j))
    t.balance(); bad = []
    for i in ids:
        j = t.find(cco[i])[1]; a, b = cw[i], sw[j]
        d = sum(abs(a.get(k, 0) - b.get(k, 0)) for k in set(a) | set(b))
        if d > .5: bad.append((d, i, max(a, key=a.get), max(b, key=b.get)))
    bad_total += len(bad)
    if bad:
        z = cco[ids].mean(0)
        print(f'PIECE src {sp} verts {len(ids)} mixed {len(bad)} centre {np.round(z, 3)} e.g. cand {bad[0][2]} vs piece {bad[0][3]} (L1 {bad[0][0]:.2f})')
print('MIXED total', bad_total, 'of', len(cco))
