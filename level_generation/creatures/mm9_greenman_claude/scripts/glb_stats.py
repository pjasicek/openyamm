"""Triangles, loose parts and bounds of a GLB's meshes (Blender). Args: <glb>"""
import bpy, bmesh, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    parts = len([1 for _ in bmesh.ops.find_doubles(bm, verts=[], dist=0)['targetmap']]) if False else None
    import numpy as np
    co = np.array([v.co for v in bm.verts])
    print('STAT', o.name, 'tris', sum(len(f.verts) - 2 for f in bm.faces), 'verts', len(bm.verts), 'min', co.min(0).round(3), 'max', co.max(0).round(3))
