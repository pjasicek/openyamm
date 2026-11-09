"""Stress pose render (no action): right arm overhead (native attack key b), left arm forward, long stride.
Args: blend tag."""
import bpy, sys, os, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, a[0]))
arm = bpy.data.objects['Thief_Rig']
arm.animation_data_create(); arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
bpy.context.view_layer.update()


def turn(bone, axis, deg):
    pb = arm.pose.bones[bone]
    M = arm.matrix_world @ pb.matrix; h = M.translation.copy()
    R = Matrix.Rotation(math.radians(deg), 4, Vector(axis))
    pb.matrix = arm.matrix_world.inverted() @ (Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ M)
    bpy.context.view_layer.update()


turn('RightArm', (0, 1, 0), 120)       # raise sideways/up (character right = -X)
turn('RightArm', (1, 0, 0), 25)
turn('RightForeArm', (1, 0, 0), 30)
turn('LeftArm', (1, 0, 0), 55)         # forward
turn('LeftForeArm', (1, 0, 0), 40)
turn('LeftUpLeg', (1, 0, 0), 35); turn('LeftLeg', (1, 0, 0), -20)
turn('RightUpLeg', (1, 0, 0), -30); turn('RightLeg', (1, 0, 0), -25)
sc = bpy.context.scene
common.workbench_clay(sc)
sc.display.shading.color_type = 'SINGLE'
common.render_views(os.path.join(common.REVIEW, a[1]), 0.85, 1.9, views=('front', 'three_quarter', 'left', 'back'),
                    resolution=(600, 900))
