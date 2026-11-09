"""Dump MM9 mesh pieces in the bind pose (Blender world, Z up, creature faces -Y): positions, triangles, UVs, bone.
Args: <glb> <out npz>"""
import bpy, sys, numpy as np
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
    me = o.data
    P = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
    T = np.array([tuple(p.vertices) for p in me.polygons])
    uv = np.zeros((len(me.loops), 2))
    if me.uv_layers:
        for i, l in enumerate(me.uv_layers[0].data):
            uv[i] = tuple(l.uv)
    L = np.array([[p.loop_indices[0], p.loop_indices[1], p.loop_indices[2]] for p in me.polygons])
    bone = np.array([o.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name for v in me.vertices])
    key = o.name.split('.')[0]
    out[key + '_P'] = P; out[key + '_T'] = T; out[key + '_UV'] = uv[L]; out[key + '_bone'] = bone
    print('PIECE', key, len(P), len(T), sorted(set(bone)))
np.savez(argv[1], **out)
