"""Textured renders of an exported GLB at clip frames. Args: -- <glb> <out prefix> clip:frame [...]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name or o.name.startswith('Ico')):
        o.hide_render = True
scene = bpy.context.scene; common.workbench_clay(scene, textured=True)
for pk in a[2:]:
    clip, fr = pk.split(':')
    act = next(x for x in bpy.data.actions if x.name.startswith(clip))
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(fr))
    common.render_views(f'{a[1]}_{clip}{fr}', 0.95, 2.0, views=('front', 'right', 'three_quarter'), resolution=(420, 520))
    h = arm.matrix_world @ arm.pose.bones['B_R_Hand'].head
    common.render_views(f'{a[1]}_{clip}{fr}_hand', h.z, 0.45, views=('front', 'right'), resolution=(400, 400), target=(h.x, h.y))
