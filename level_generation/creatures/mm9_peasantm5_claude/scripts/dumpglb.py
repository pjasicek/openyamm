import bpy, sys, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if arm and arm.animation_data: arm.animation_data.action = None
if arm:
    for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
cos, tris, n = [], [], 0
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name.startswith('Icosphere'): continue
    me = o.evaluated_get(dg).to_mesh()
    cos += [o.matrix_world @ v.co for v in me.vertices]
    for p in me.polygons:
        vs = list(p.vertices)
        for k in range(1, len(vs) - 1): tris.append([n + vs[0], n + vs[k], n + vs[k + 1]])
    n += len(me.vertices)
np.savez(argv[1], co=np.array(cos, np.float32), tris=np.array(tris, np.int32))
print('DUMP', n)
