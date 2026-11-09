"""Edges traversed twice in the same direction (inconsistent winding) and duplicate-position faces. Args: <glb|blend> [object]"""
import bpy, bmesh, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
if argv[0].endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=argv[0])
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=argv[0])
for o in bpy.data.objects:
    if o.type != 'MESH' or (len(argv) > 1 and o.name != argv[1]):
        continue
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    d = {}
    bad = 0
    for f in bm.faces:
        vs = [v.index for v in f.verts]
        for k in range(len(vs)):
            e = (vs[k], vs[(k + 1) % len(vs)])
            if e in d:
                bad += 1
            d[e] = 1
    nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    bound = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    print('WIND', o.name, json.dumps({'faces': len(bm.faces), 'same_dir_edges': bad, 'nonmanifold': nonman, 'boundary': bound}))
