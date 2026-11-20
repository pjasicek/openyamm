"""Bake twist channels for newly fitted clips without redistributing the already calibrated skin weights."""
import math
import sys
import bpy
from mathutils import Quaternion, Vector

src, out, *clips = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=src)
rig = bpy.data.objects['Rig']
rig.animation_data_create()

def twist(q, axis):
    angle = 2 * math.atan2(Vector((q.x, q.y, q.z)).dot(axis), q.w)
    return (angle + math.pi) % (2 * math.pi) - math.pi

for act in [a for a in bpy.data.actions if a.name in clips or a.name.startswith(('Forge_', 'Lancer_'))]:
    rig.animation_data.action = act
    rig.animation_data.action_slot = act.slots[0]
    for frame in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        bpy.context.scene.frame_set(frame)
        for side in 'LR':
            fore, hand, upper = [rig.data.bones[f'B_{side}_{part}'] for part in ('Forearm', 'Hand', 'UpperArm')]
            axis = (fore.matrix_local.inverted() @ hand.head_local).normalized()
            relative = (rig.pose.bones[fore.name].matrix.inverted() @ rig.pose.bones[hand.name].matrix).to_quaternion()
            rest = (fore.matrix_local.inverted() @ hand.matrix_local).to_quaternion()
            helper = rig.pose.bones[f'B_{side}_ForearmTwist']
            helper.rotation_mode = 'QUATERNION'
            helper.rotation_quaternion = Quaternion(axis, .5 * twist(relative @ rest.inverted(), axis))
            helper.keyframe_insert('rotation_quaternion', frame=frame)
            axis = (upper.matrix_local.inverted() @ fore.head_local).normalized()
            helper = rig.pose.bones[f'B_{side}_UpperArmTwist']
            helper.rotation_mode = 'QUATERNION'
            helper.rotation_quaternion = Quaternion(axis, -.5 * twist(rig.pose.bones[upper.name].matrix_basis.to_quaternion(), axis))
            helper.keyframe_insert('rotation_quaternion', frame=frame)
    print('TWIST_BAKED', act.name, flush=True)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=out)
