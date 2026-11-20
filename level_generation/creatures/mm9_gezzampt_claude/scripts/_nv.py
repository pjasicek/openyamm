import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=a[0])
o = next(x for x in bpy.data.objects if x.type == 'MESH')
Mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mw
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x)
bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=2e-4)
before = [f.normal.copy() for f in bm.faces]
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
print('NV flipped', sum(1 for f, n in zip(bm.faces, before) if f.normal.dot(n) < 0), 'of', len(before), 'bd', sum(1 for e in bm.edges if e.is_boundary))
bm.to_mesh(o.data); bm.free()
for p in o.data.polygons: p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=a[1])
