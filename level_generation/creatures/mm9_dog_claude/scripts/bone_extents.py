"""Per-bone vertex extents of a converted MM9 GLB in the bind pose (rigid skin: dominant bone per vertex).
Args: <glb>"""
import bpy, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
out = {}
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name.startswith('Icosphere'):
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        n = o.vertex_groups[g.group].name
        p = o.matrix_world @ v.co
        e = out.setdefault(n, [list(p), list(p), 0])
        e[0] = [min(a, b) for a, b in zip(e[0], p)]
        e[1] = [max(a, b) for a, b in zip(e[1], p)]
        e[2] += 1
for n, (a, b, c) in sorted(out.items(), key=lambda kv: kv[1][0][2]):
    print('EXT %-12s n=%3d min %s max %s' % (n, c, [round(x, 4) for x in a], [round(x, 4) for x in b]))
