"""Stress poses on the rig (world-axis rotations about each joint), rendered front/side/three-quarter.
Args: -- <rig blend> <tag>"""
import bpy, sys, os, math
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Skeleton_Rig']


def turn(bone, axis, deg):
    """Rotate a pose bone about a world axis through its head (rest-relative, applied in order)."""
    pb = rig.pose.bones['mixamorig:' + bone]
    bpy.context.view_layer.update()
    m = rig.matrix_world @ pb.matrix
    h = m.translation.copy()
    r = Matrix.Rotation(math.radians(deg), 4, Vector(axis))
    w = Matrix.Translation(h) @ r @ Matrix.Translation(-h) @ m
    pb.matrix = rig.matrix_world.inverted() @ w
    bpy.context.view_layer.update()


POSES = {
    'arms': [('RightArm', (0, 1, 0), 50), ('RightArm', (1, 0, 0), 70), ('RightForeArm', (1, 0, 0), 80),
             ('LeftArm', (0, 1, 0), -60), ('LeftForeArm', (1, 0, 0), 60), ('Spine1', (0, 0, 1), 20),
             ('Head', (1, 0, 0), -20), ('Neck', (0, 0, 1), 25)],
    'crouch': [('RightUpLeg', (1, 0, 0), 70), ('RightLeg', (1, 0, 0), -100), ('LeftUpLeg', (1, 0, 0), 30),
               ('LeftLeg', (1, 0, 0), -40), ('LeftFoot', (1, 0, 0), 20), ('Spine', (1, 0, 0), 20),
               ('Spine2', (0, 1, 0), 15)],
}
fist = []
for s, sg in (('Right', -1), ('Left', 1)):
    for f in ('Index', 'Middle', 'Ring', 'Pinky'):
        for i in (1, 2, 3):
            fist.append((f'{s}Hand{f}{i}', (0, sg * 1, 0), 0))
scene = bpy.context.scene; common.workbench_clay(scene)
for name, ops in POSES.items():
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix()
    for b, ax, d in ops:
        turn(b, ax, d)
    common.render_views(os.path.join(common.REVIEW, f'{tag}_{name}'), 0.85, 1.8,
                        views=('front', 'left', 'three_quarter'), resolution=(500, 750))
