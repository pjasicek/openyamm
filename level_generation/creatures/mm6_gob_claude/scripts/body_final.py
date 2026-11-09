"""Stage A final: MPFB body with selected macros, baked shape, arms/legs re-posed into the reference A-pose,
pose applied as rest. Output work/body_final.blend (Human mesh + Human.rig)."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
cfg = json.loads(args[0]) if args else {}
MACROS = {"gender": 1.0, "age": 0.5, "muscle": 0.75, "weight": 0.3, "proportions": 0.4, "height": 0.4,
          "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.0, "caucasian": 1.0, "african": 0.0}}
ARM_DOWN = cfg.get('arm_down', 7.0)
LEG_IN = cfg.get('leg_in', 3.0)
FOREARM_IN = cfg.get('forearm_in', 4.0)
tag = cfg.get('tag', 'final')
common.enable_mpfb()
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
common.clear_scene()
human = HumanService.create_human(macro_detail_dict=MACROS, feet_on_ground=True, scale=0.1)
rig = HumanService.add_builtin_rig(human, 'mixamo')
bpy.context.view_layer.update()
# Bake macro shape keys into the base mesh.
bpy.context.view_layer.objects.active = human
human.shape_key_add(name='baked', from_mix=True)
keys = human.data.shape_keys.key_blocks
baked = [tuple(k.co) for k in keys['baked'].data]
human.shape_key_clear()
for v, co in zip(human.data.vertices, baked):
    v.co = co

def rotate_world(pb, axis, degrees):
    head = pb.head.copy()
    R = Matrix.Translation(head) @ Matrix.Rotation(math.radians(degrees), 4, axis) @ Matrix.Translation(-head)
    pb.matrix = R @ pb.matrix
    bpy.context.view_layer.update()

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')
P = rig.pose.bones
rotate_world(P['mixamorig:LeftArm'], 'Y', ARM_DOWN)
rotate_world(P['mixamorig:RightArm'], 'Y', -ARM_DOWN)
rotate_world(P['mixamorig:LeftForeArm'], 'Y', FOREARM_IN)
rotate_world(P['mixamorig:RightForeArm'], 'Y', -FOREARM_IN)
rotate_world(P['mixamorig:LeftUpLeg'], 'Y', LEG_IN)
rotate_world(P['mixamorig:RightUpLeg'], 'Y', -LEG_IN)
# Keep feet flat after adduction.
rotate_world(P['mixamorig:LeftFoot'], 'Y', -LEG_IN)
rotate_world(P['mixamorig:RightFoot'], 'Y', LEG_IN)
bpy.ops.object.mode_set(mode='OBJECT')
# Apply deformation to the mesh, then make the pose the new rest.
mod = next(m for m in human.modifiers if m.type == 'ARMATURE')
mask = [m for m in human.modifiers if m.type == 'MASK']
for m in mask: m.show_viewport = False
bpy.context.view_layer.objects.active = human
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode='OBJECT')
arm = human.modifiers.new('Armature', 'ARMATURE'); arm.object = rig
for m in mask:
    m.show_viewport = True
    bpy.ops.object.modifier_move_to_index(modifier=m.name, index=len(human.modifiers) - 1)
# Align torso to the Meshy detail source (Y) - measured offset.
rig.location.y += cfg.get('dy', 0.0)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, f'body_{tag}.blend'))
print('SAVED', tag)
