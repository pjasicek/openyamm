"""Label the body's connected mesh pieces (by shared vertex positions): attribute 'piece' = 0 for the largest piece
(the skin), 1.. for the others in decreasing size; prints each piece's size, centre and dominant bone. Saves in place.
Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
from collections import Counter
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
key = {}
rep = np.arange(len(co))
for i, c in enumerate(np.round(co, 5).tolist()):
    rep[i] = key.setdefault(tuple(c), i)
par = list(range(len(co)))
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
for e in me.edges:
    a_, b_ = find(rep[e.vertices[0]]), find(rep[e.vertices[1]])
    if a_ != b_: par[a_] = b_
for i in range(len(co)):
    par[i] = find(rep[i])
roots = Counter(par)
order = [r for r, _ in roots.most_common()]
idx = {r: k for k, r in enumerate(order)}
piece = np.array([idx[par[i]] for i in range(len(co))], np.int32)
att = me.attributes.get('piece') or me.attributes.new('piece', 'INT', 'POINT')
att.data.foreach_set('value', piece.tolist())
names = [g.name for g in body.vertex_groups]
info = []
for k, r in enumerate(order):
    m = piece == k
    doms = Counter()
    for i in np.nonzero(m)[0][:400]:
        v = me.vertices[int(i)]
        if v.groups: doms[names[max(v.groups, key=lambda g: g.weight).group]] += 1
    mats = Counter(me.materials[p.material_index].name for p in me.polygons if m[p.vertices[0]])
    info.append({'piece': k, 'verts': int(m.sum()), 'centre': co[m].mean(0).round(3).tolist(), 'bone': doms.most_common(1)[0][0] if doms else None, 'mat': dict(mats)})
for x in info: print('PIECE', json.dumps(x))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a[0]))
sys.stdout.flush(); os._exit(0)
