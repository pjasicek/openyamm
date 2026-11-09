"""Meshy body -> work/body_clean.blend + work/body_clean.npz: main shell only, Y-forward kept (figure faces -Y in Blender, as MM9 raw), scaled so the
hip-to-sole height matches MM9 bind (`SCALE` env), feet on z=0, centred on x. Args: <glb> <blend> <npz>"""
import bpy, sys, os, bmesh
import numpy as np
glb, blend, npz = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
for o in list(bpy.context.scene.objects):
    if o is not ob: bpy.data.objects.remove(o)
ob.parent = None
M = ob.matrix_world.copy()
me = ob.data; me.transform(M); ob.matrix_world.identity()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); comps = []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); c = []
    while st:
        x = st.pop(); c.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen: seen.add(y.index); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
kill = [v for c in comps[1:] for v in c]
bmesh.ops.delete(bm, geom=kill, context='VERTS')
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.to_mesh(me); bm.free()
scale = float(os.environ.get('SCALE', '1.84'))
P = np.array([tuple(v.co) for v in me.vertices])
s = scale / np.ptp(P[:, 2])
P = P * s
P[:, 2] -= P[:, 2].min()
P[:, 0] -= (P[:, 0].min() + P[:, 0].max()) / 2
me.vertices.foreach_set('co', P.ravel())
me.update(); ob.name = 'Body'; me.name = 'Body'
for m in list(me.materials): pass
me.materials.clear()
bpy.ops.wm.save_as_mainfile(filepath=blend)
T = np.zeros(len(me.polygons) * 3, np.int32); me.polygons.foreach_get('vertices', T)
np.savez(npz, co=P, tri=T.reshape(-1, 3))
print('CLEAN', len(P), len(T) // 3, s, P.min(0), P.max(0))
