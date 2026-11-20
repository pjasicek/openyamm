"""Step 1: Meshy Smart Topology -> raw MM9 space (Blender frame: faces -Y, z up; MM9's bind is centred on the pelvis,
soles at z -0.819), exact mirror symmetry (the figure's LEFT half, +x in the master frame, kept and mirrored; Blender's
bisect + mirror with merge), symmetric decimate to a budget. Writes co/tri/comp (connected parts, largest first).
Args: <meshy glb> <out npz> <target faces> [keep side +1|-1]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, TARGET = a[0], a[1], int(a[2])
SIDE = float(a[3]) if len(a) > 3 else 1.0
SOLE, TOP = -0.8192, 1.0992          # MM9 sole and horn tip (raw ABC, Blender frame)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
ob.data.transform(ob.matrix_world); ob.matrix_world = Matrix()
P = np.array([v.co for v in ob.data.vertices])
s = (TOP - SOLE) / np.ptp(P[:, 2])
cx = 0.5 * (P[:, 0].min() + P[:, 0].max())
ob.data.transform(Matrix.Translation((-cx * s, 0, SOLE - P[:, 2].min() * s)) @ Matrix.Scale(s, 4))
P = np.array([v.co for v in ob.data.vertices]); print('BOUNDS', P.min(0).round(3), P.max(0).round(3), 'scale', s)
# drop UVs/normals, weld
bm = bmesh.new(); bm.from_mesh(ob.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
r = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=(0, 0, 0), plane_no=(SIDE, 0, 0), clear_inner=True)
bm.to_mesh(ob.data); bm.free()
for u in list(ob.data.uv_layers): ob.data.uv_layers.remove(u)
m = ob.modifiers.new('mir', 'MIRROR'); m.use_axis[0] = True; m.use_mirror_merge = True; m.merge_threshold = 1e-4
bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier='mir')
bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free()
nf = len(ob.data.polygons); print('FACES after mirror', nf)
if nf > TARGET:
    d = ob.modifiers.new('dec', 'DECIMATE'); d.ratio = TARGET / nf; d.use_symmetry = True; d.symmetry_axis = 'X'
    bpy.ops.object.modifier_apply(modifier='dec')
bm = bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(ob.data); bm.free()
me = ob.data
co = np.array([v.co for v in me.vertices]); tri = np.array([p.vertices[:] for p in me.polygons])
# components
n = len(co); par = np.arange(n)
def f(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for t in tri:
    r0 = f(t[0]); par[f(t[1])] = r0; par[f(t[2])] = r0
root = np.array([f(i) for i in range(n)])
u, cnt = np.unique(root, return_counts=True); order = u[np.argsort(-cnt)]
comp = np.searchsorted(order, root, sorter=np.argsort(order)); comp = np.argsort(np.argsort(-cnt))[np.searchsorted(u, root)]
for k in range(len(order)):
    q = co[comp == k]; print('PART', k, len(q), q.mean(0).round(3).tolist(), q.min(0).round(3).tolist(), q.max(0).round(3).tolist())
mx = np.abs(co[:, 0]).max(); d = np.array([(co - co[i] * [-1, 1, 1]).__abs__().sum(1).min() for i in range(0, n, 50)])
print('FACES', len(tri), 'VERTS', n, 'mirror residual (sampled)', d.max())
np.savez(OUT, co=co, tri=tri, comp=comp)
