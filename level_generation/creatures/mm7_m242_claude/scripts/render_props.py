"""Textured renders of work/props.blend (SwordMesh broad side and edge, ShieldMesh front, back and side) to
review/props_<view>.png. Args: none"""
import bpy, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'props.blend'))
sc = bpy.context.scene; common.workbench_clay(sc, textured=True)
sw, sh = bpy.data.objects['SwordMesh'], bpy.data.objects['ShieldMesh']
sw.rotation_mode = sh.rotation_mode = 'XYZ'                                      # imported glTF objects use quaternions
sh.location = (0.9, 0, 0.3); sh.rotation_euler = (math.radians(90), 0, 0)      # face toward -Y (front camera)
sw.rotation_euler = (math.radians(90), 0, 0)                                      # tip up, flat facing the camera
for name, rz in (('front', 0), ('back', 180), ('side', 90)):
    sw.rotation_euler[2] = math.radians(rz); sh.rotation_euler[2] = math.radians(rz)
    common.render_views(os.path.join(common.REVIEW, f'props_{name}'), 0.3, 1.4, views=('front',), resolution=(900, 900), target=(0.45, 0))
