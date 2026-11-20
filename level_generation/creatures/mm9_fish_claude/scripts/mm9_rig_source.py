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
print('SOURCE', OUT, 'zmin %.4f zmax %.4f' % (min(zs), max(zs)), [o.name for o in bpy.data.objects])
bpy.ops.wm.save_as_mainfile(filepath=OUT)
