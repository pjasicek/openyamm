"""The goose hat for the male attachment: the hat parts of the female master (geometry and Meshy paint of her head set), moved to the male head,
new UV atlas of their own. Args (Blender): <female blend> <out blend> <out npz> <scale> <brim z> <dy>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
s, zb, dy = float(a[3]), float(a[4]), float(a[5])
ys = float(a[6]) if len(a) > 6 else 1.0
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared')))
import uv_atlas
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data; M = b.matrix_world
for pb in b.parent.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
CO = np.array([tuple(M @ v.co) for v in me.vertices])
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0: continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0: comp[y.index] = cid; st.append(y)
    cid += 1
hat = [k for k in range(cid) if CO[comp == k, 2].min() > 0.705 and np.abs(CO[comp == k, 0]).max() < 0.2]
print('GOOSE parts', hat, [int((comp == k).sum()) for k in hat])
bmesh.ops.delete(bm, geom=[f for f in bm.faces if comp[f.verts[0].index] not in hat], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
nm = bpy.data.meshes.new('Hat'); bm.to_mesh(nm); bm.free()
h = bpy.data.objects.new('Hat', nm); bpy.context.scene.collection.objects.link(h)
for ln in [l.name for l in nm.uv_layers if l.name not in ('HeadUV',)]:
    nm.uv_layers.remove(nm.uv_layers[ln])
nm.uv_layers['HeadUV'].name = 'OldUV'
co = np.array([tuple(M @ v.co) for v in nm.vertices])
lo, hi = co.min(0), co.max(0)
q = (co - np.array([.5 * (lo[0] + hi[0]), .5 * (lo[1] + hi[1]), lo[2]])) * s
q[:, 1] *= ys
q += np.array([0, dy, zb])
for v, p in zip(nm.vertices, q): v.co = Vector(p.tolist())
for o in list(bpy.data.objects):
    if o is not h: bpy.data.objects.remove(o)
for g in list(h.vertex_groups): h.vertex_groups.remove(g)
bpy.context.view_layer.objects.active = h; h.select_set(True)
old = np.array([tuple(l.uv) for l in nm.uv_layers['OldUV'].data])
oldtri = None
rep = uv_atlas.unwrap(h, fine=250, steps=0)
nm.calc_loop_triangles()
uvn = nm.uv_layers['UVMap'].data
U = [[tuple(uvn[l].uv) for l in t.loops] for t in nm.loop_triangles]; O = [[tuple(old[l]) for l in t.loops] for t in nm.loop_triangles]
X = [[tuple(nm.vertices[v].co) for v in t.vertices] for t in nm.loop_triangles]
np.savez(a[2], uv=np.array(U, np.float32), old=np.array(O, np.float32), xyz=np.array(X, np.float32))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('GOOSE', json.dumps({k: rep[k] for k in ('use', 'charts')}), len(U), q.min(0).round(3).tolist(), q.max(0).round(3).tolist())
