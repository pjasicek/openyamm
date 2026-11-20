"""Rig stress poses rendered in clay. Args: tag."""
import bpy, sys, os, math
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, posing as P
tag = sys.argv[sys.argv.index('--') + 1]
rig = bpy.data.objects['Peasant_Rig']
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name != 'Peasant'
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'SINGLE'; scene.display.shading.single_color = (0.78, 0.7, 0.62)

def shoulder(side): return P.bone_world(rig, f'{side}Arm')

def clasp():
    for side, sx in (('Right', -1), ('Left', 1)):
        s = shoulder(side)
        P.two_bone_ik(rig, f'mixamorig:{side}Arm', f'mixamorig:{side}ForeArm', Vector((0.045 * sx, -0.2, 0.93)),
                      s + Vector((0.35 * sx, 0.25, -0.3)))
        P.aim_bone(rig, f'mixamorig:{side}Hand', Vector((-0.03 * sx, -0.215, 0.84)))
        P.curl_hand(rig, side, 22, thumb=10)

def grip():
    P.curl_hand(rig, 'Right', 80, thumb=35)

def reach():
    s = shoulder('Right')
    P.two_bone_ik(rig, 'mixamorig:RightArm', 'mixamorig:RightForeArm', Vector((0.22, -0.42, 1.25)), s + Vector((0, 0.1, -0.4)))
    P.curl_hand(rig, 'Right', 80, thumb=35)

def bend():
    for b in ('Spine', 'Spine1', 'Spine2'):
        P.rotate_world(rig, b, 'X', 13)
    P.rotate_world(rig, 'Neck', 'X', 10)

def kneel():
    hips = P.pb(rig, 'Hips')
    hips.matrix = Matrix.Translation((0, 0.05, -0.42)) @ hips.matrix
    bpy.context.view_layer.update()
    for side in ('Left', 'Right'):
        P.rotate_world(rig, f'{side}UpLeg', 'X', -80)
        P.rotate_world(rig, f'{side}Leg', 'X', 125)
        P.rotate_world(rig, f'{side}Foot', 'X', -40)
    for b in ('Spine', 'Spine1'):
        P.rotate_world(rig, b, 'X', 10)

poses = {'clasp': clasp, 'grip': grip, 'reach': reach, 'bend': bend, 'kneel': kneel}
for name, fn in poses.items():
    P.reset(rig); fn()
    common.render_views(os.path.join(common.REVIEW, f'{tag}_{name}'), 0.8, 1.7, views=('front', 'left'), resolution=(500, 500))
    if name in ('grip', 'clasp', 'reach'):
        h = P.bone_world(rig, 'RightHand')
        common.render_views(os.path.join(common.REVIEW, f'{tag}_{name}_hand'), h.z, 0.25, views=('front', 'right', 'three_quarter'),
                            resolution=(400, 400), target=(h.x, h.y))
