"""Pass 7: Meshy GLB -> npz (co in Blender axes after the import transform, tri, comp = connected piece id sorted by size, uv when the
GLB has one). Vertices welded at 1e-6 unless KEEP_UV=1 (then the GLB's own vertex split is kept). Args: <glb> <out npz>"""
import bpy, bmesh, sys, os
import numpy as np
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
obs = [x for x in bpy.data.objects if x.type == 'MESH']
for o in obs:
    bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM'); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
o = obs[0]; me = o.data
keep_uv = os.environ.get('KEEP_UV') == '1'
bm = bmesh.new(); bm.from_mesh(me)
if not keep_uv: bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
P = np.array([v.co[:] for v in me.vertices]); T = np.array([p.vertices[:] for p in me.polygons])
n = len(P); par = np.arange(n)
def f(a):
    while par[a] != a: par[a] = par[par[a]]; a = par[a]
    return a
for t in T:
    r = f(t[0]); par[f(t[1])] = r; par[f(t[2])] = r
r = np.array([f(i) for i in range(n)]); u, inv, cnt = np.unique(r, return_inverse=True, return_counts=True)
rank = np.empty(len(u), int); rank[np.argsort(-cnt)] = np.arange(len(u)); comp = rank[inv]
extra = {}
if me.uv_layers:
    uv = np.zeros((n, 2)); L = me.uv_layers[0].data
    for p in me.polygons:
        for li, vi in zip(p.loop_indices, p.vertices): uv[vi] = L[li].uv[:]
    extra['uv'] = uv
np.savez(OUT, co=P, tri=T, comp=comp, **extra)
print('DUMP', OUT, n, len(T), 'pieces', len(u), 'sizes', sorted(cnt)[::-1][:10])
