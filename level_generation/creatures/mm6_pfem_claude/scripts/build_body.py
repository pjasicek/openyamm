"""Stage A: MPFB female base body with Mixamo rig. Writes work/body_v1.blend and clay renders."""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
common.enable_mpfb()
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
from bl_ext.blender_org.mpfb.services.targetservice import TargetService

MACROS = {'gender': 0.0, 'age': 0.5, 'muscle': 0.45, 'weight': 0.45, 'proportions': 0.6, 'height': 0.45,
          'cupsize': 0.45, 'firmness': 0.5, 'race': {'asian': 0.0, 'caucasian': 1.0, 'african': 0.0}}

common.clear_scene()
human = HumanService.create_human(macro_detail_dict=MACROS, feet_on_ground=True, scale=0.1)
rig = HumanService.add_builtin_rig(human, 'mixamo')
bpy.context.view_layer.update()
lo, hi = common.world_bounds([human])
H = hi.z - lo.z
bones = {b.name: (rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local) for b in rig.data.bones}
def bz(name, tail=False):
    return bones['mixamorig:' + name][1 if tail else 0]
report = {
    'height_m': H, 'bounds': [list(lo), list(hi)],
    'head_bone_z_over_H': (bz('Head').z - lo.z) / H,
    'shoulder_width_over_H': (bz('LeftArm') - bz('RightArm')).length / H,
    'hips_z_over_H': (bz('Hips').z - lo.z) / H,
    'spine1_z_over_H': (bz('Spine1').z - lo.z) / H,
    'arm_angle_deg': None,
    'shapekeys': [k.name for k in human.data.shape_keys.key_blocks] if human.data.shape_keys else [],
}
import math
la = bz('LeftArm'); lf = bz('LeftForeArm')
d = lf - la
report['arm_angle_deg'] = math.degrees(math.atan2(-d.z, abs(d.x)))
for name in ('LeftHand', 'LeftFoot', 'LeftToeBase', 'Neck', 'Head'):
    report[name] = list(bz(name))
print('REPORT', json.dumps(report, indent=1))
os.makedirs(common.WORK, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'body_v1.blend'))
scene = bpy.context.scene
common.workbench_clay(scene)
common.render_views(os.path.join(common.REVIEW, 'body_v1'), (lo.z + hi.z) / 2, H * 1.08)
