"""Blender: list the open boundary loops of the master's mesh (all faces): edges, centre, radius, dominant bone, whether the
adjacent faces are body/head/hand. Args: <blend>"""
import bpy, bmesh, sys, numpy as np
from collections import Counter
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
o = bpy.data.objects['Body']; me = o.data
names = [g.name for g in o.vertex_groups]
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
bm = bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table()
dl = bm.verts.layers.deform.active
bnd = [e for e in bm.edges if e.is_boundary]
seen = set()
for e in bnd:
    if e.index in seen: continue
    loop = []; st = [e]; seen.add(e.index)
    while st:
        x = st.pop(); loop.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y.index not in seen:
                    seen.add(y.index); st.append(y)
    vs = {v for x in loop for v in x.verts}
    P = np.array([v.co[:] for v in vs]); c = P.mean(0)
    bones = Counter(names[max(v[dl].items(), key=lambda t: t[1])[0]] for v in vs if v[dl])
    kind = Counter(('head' if hd[f.index] else 'hand' if hn[f.index] else 'body') for x in loop for f in x.link_faces)
    print('LOOP', len(loop), 'c', c.round(3), 'r %.3f' % np.linalg.norm(P - c, axis=1).mean(), dict(bones.most_common(2)), dict(kind))
