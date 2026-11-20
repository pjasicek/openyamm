"""Rest-pose triangles of the master for texel maps. Args (Blender): <blend> <out npz> [uv layer UVMap]
npz: uv (F,3,2), xyz (F,3,3), head, hand (F)"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; rig = b.parent
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = b.data; M = b.matrix_world
me.calc_loop_triangles()
uvn = a[2] if len(a) > 2 else 'UVMap'
uv = me.uv_layers[uvn].data
hd = np.zeros(len(me.polygons), np.int32); hn = np.zeros(len(me.polygons), np.int32)
me.attributes['head'].data.foreach_get('value', hd); me.attributes['hand'].data.foreach_get('value', hn)
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(me.vertices), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
bm.free()
U, X, H, K, C = [], [], [], [], []
for t in me.loop_triangles:
    U.append([tuple(uv[l].uv) for l in t.loops]); X.append([tuple(M @ me.vertices[v].co) for v in t.vertices])
    H.append(hd[t.polygon_index]); K.append(hn[t.polygon_index]); C.append(comp[t.vertices[0]])
np.savez(a[1], uv=np.array(U, np.float32), xyz=np.array(X, np.float32), head=np.array(H), hand=np.array(K), comp=np.array(C))
print('UVXYZ', len(U))
