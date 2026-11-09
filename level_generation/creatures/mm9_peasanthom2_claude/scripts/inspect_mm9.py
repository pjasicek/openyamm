"""Per-bone vertex counts and centroids of the MM9 mesh, and joint positions. Args: glb"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
for b in arm.data.bones:
    h = arm.matrix_world @ b.head_local
    print('J %-20s %6.3f %6.3f %6.3f parent=%s' % (b.name, h.x, h.y, h.z, b.parent.name if b.parent else None))
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        continue
    print('MESH', o.name, len(o.data.vertices), [m.name for m in o.data.materials])
    acc = {}
    for v in o.data.vertices:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda g: g.weight)
        acc.setdefault(o.vertex_groups[g.group].name, []).append(o.matrix_world @ v.co)
    for k, pts in acc.items():
        p = np.array(pts)
        print('  %-20s %4d c=%s min=%s max=%s' % (k, len(p), np.round(p.mean(0), 3), np.round(p.min(0), 3), np.round(p.max(0), 3)))
