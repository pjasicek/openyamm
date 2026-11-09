"""Report the converted MM9 dragonfly: bones (world heads/tails in bind), mesh pieces, bounds, clip ranges."""
import bpy, sys, json
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb = argv[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
out = {'arm_matrix': [list(r) for r in arm.matrix_world]}
out['bones'] = {b.name: {'parent': b.parent.name if b.parent else None,
                         'head': [round(v, 4) for v in arm.matrix_world @ b.head_local],
                         'tail': [round(v, 4) for v in arm.matrix_world @ b.tail_local]} for b in arm.data.bones}
dg = bpy.context.evaluated_depsgraph_get()
out['meshes'] = {}
for o in sc.objects:
    if o.type != 'MESH':
        continue
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    vs = [o.matrix_world @ v.co for v in me.vertices]
    mn = [min(v[i] for v in vs) for i in range(3)]
    mx = [max(v[i] for v in vs) for i in range(3)]
    groups = {}
    for v in o.data.vertices:
        for g in v.groups:
            if g.weight > 0:
                n = o.vertex_groups[g.group].name
                groups[n] = groups.get(n, 0) + 1
    out['meshes'][o.name] = {'verts': len(me.vertices), 'polys': len(me.polygons), 'min': [round(x, 4) for x in mn],
                             'max': [round(x, 4) for x in mx], 'groups': groups,
                             'materials': [m.name for m in o.data.materials if m]}
    ev.to_mesh_clear()
out['actions'] = {a.name: [a.frame_range[0], a.frame_range[1]] for a in bpy.data.actions}
out['fps'] = sc.render.fps
print('INSPECT ' + json.dumps(out))
