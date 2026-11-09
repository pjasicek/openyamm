"""MM9 skeleton + mesh + clips, re-oriented for OpenYAMM, saved as a blend (armature 'MM9_Rig').

Args: <mm9 glb> <out blend> <flip 0|1> <lift metres>
flip 1: the armature is turned 180 deg about the forward axis (Blender Y; the creature faces -Y), which grows the
ceiling-hanging Lobber upright from its root bulb. lift: raises it so the lowest bind point is on the floor (z = 0).
Both are applied to the armature and its meshes (rest pose), so every MM9 clip (bone-local channels) follows.
"""
import bpy, sys, math
from mathutils import Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, FLIP, LIFT = argv[0], argv[1], argv[2] == '1', float(argv[3])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name.startswith('Icosphere'):
        bpy.data.objects.remove(o)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.name = 'MM9_Rig'
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
m = Matrix.Translation((0, 0, LIFT)) @ (Matrix.Rotation(math.pi, 4, 'Y') if FLIP else Matrix())
arm.matrix_world = m @ arm.matrix_world
bpy.context.view_layer.update()
for o in bpy.data.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
zs = []
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.evaluated_get(dg).to_mesh()
        zs += [(o.matrix_world @ v.co).z for v in me.vertices]
        o.evaluated_get(dg).to_mesh_clear()
# Constant clip offsets (sheep): every SHEEP.abc clip keeps Xjawpiv translated (0, 0.0511, 0.0079) from the bind (the
# lower jaw pushed 5 cm up into the skull), the ears (Xearpiv/01) 1.4 cm out along the ear and Xheadpiv 6 mm; the
# setup clip has none. The offsets are the same in every key of every clip, i.e. a mismatch between MM9's setup pose
# and its animation set. Our mesh is fitted to the setup (bind) pose, so the offset is removed from the location keys
# (rotations untouched): the jaw opens about its bind position as in MM9, the ears stay on the head.
import os, json
offsets = {}
if os.environ.get('ZERO_CONST_OFFSETS', '1') == '1':
    from collections import defaultdict
    vals = defaultdict(list)
    curves = defaultdict(list)
    for act in bpy.data.actions:
        if 'setup' in act.name.lower():
            continue
        fcs = list(getattr(act, 'fcurves', []) or [])
        if not fcs and hasattr(act, 'layers'):
            fcs = [fc for layer in act.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
        for fc in fcs:
            if fc.data_path.endswith('.location'):
                key = (fc.data_path.split('"')[1], fc.array_index)
                vals[key] += [kp.co.y for kp in fc.keyframe_points]
                curves[key].append(fc)
    for (bone, axis), v in vals.items():
        v = list(v)
        if v and max(v) - min(v) < 1e-5 and abs(v[0]) > 0.005:
            offsets.setdefault(bone, [0.0, 0.0, 0.0])[axis] = v[0]
            for fc in curves[(bone, axis)]:
                for kp in fc.keyframe_points:
                    kp.co.y -= v[0]; kp.handle_left.y -= v[0]; kp.handle_right.y -= v[0]
    arm['const_offsets_removed'] = json.dumps(offsets)
print('OFFSETS', json.dumps(offsets))
print('SOURCE', OUT, 'zmin %.4f zmax %.4f' % (min(zs), max(zs)), [o.name for o in bpy.data.objects])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
