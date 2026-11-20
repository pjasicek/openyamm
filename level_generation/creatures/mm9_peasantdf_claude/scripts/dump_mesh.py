"""Dump a master blend's Body mesh to npz (job 7 analysis outside Blender): rest positions, triangles (loop vertex ids),
per-corner HeadUV and UVMap, face attributes head/hand/twin, connected component per vertex, vertex normals, and the
weight of each vertex group (names listed). Args: <blend> <out npz>"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
me.calc_loop_triangles()
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
nrm = np.array([tuple(v.normal) for v in me.vertices])
tris = np.array([tuple(t.vertices) for t in me.loop_triangles]); tloops = np.array([tuple(t.loops) for t in me.loop_triangles])
tpoly = np.array([t.polygon_index for t in me.loop_triangles])
def uvl(name):
    l = me.uv_layers.get(name)
    if l is None: return np.zeros((len(me.loops), 2))
    u = np.empty(len(me.loops) * 2); l.data.foreach_get('uv', u); return u.reshape(-1, 2)
fa = {}
for nm in ('head', 'hand', 'twin'):
    at = me.attributes.get(nm)
    if at is None: fa[nm] = np.zeros(len(me.polygons), int); continue
    x = np.empty(len(me.polygons), int); at.data.foreach_get('value', x); fa[nm] = x
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(nv, int); k = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = k
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if comp[o.index] < 0: comp[o.index] = k; st.append(o)
    k += 1
names = [g.name for g in ob.vertex_groups]
W = np.zeros((nv, len(names)), np.float32)
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
bones = {b.name: (np.array(rig.matrix_world @ b.head_local), np.array(rig.matrix_world @ b.tail_local)) for b in rig.data.bones}
np.savez_compressed(a[1], co=co, nrm=nrm, tris=tris, tloops=tloops, tpoly=tpoly, huv=uvl('HeadUV'), buv=uvl('UVMap'),
                    head=fa['head'], hand=fa['hand'], twin=fa['twin'], comp=comp, W=W, names=np.array(names),
                    mw=np.array(ob.matrix_world), bone_names=np.array(list(bones)), bone_heads=np.array([bones[b][0] for b in bones]),
                    bone_tails=np.array([bones[b][1] for b in bones]))
print('DUMPED', nv, len(tris), k, 'groups', len(names))
