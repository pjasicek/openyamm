"""Render specific frames of an action from given views. Args: action tag frames(comma) views(comma) [cz height]."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
action, tag, frames, views = args[0], args[1], [float(f) for f in args[2].split(',')], args[3].split(',')
cz = float(args[4]) if len(args) > 4 else 0.8; hh = float(args[5]) if len(args) > 5 else 1.75
textured = len(args) > 6 and args[6] == 'tex'
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = bpy.data.actions[action]
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name != 'Peasant'
scene = bpy.context.scene
common.workbench_clay(scene, textured=textured)
if not textured:
    scene.display.shading.color_type = 'SINGLE'; scene.display.shading.single_color = (0.78, 0.7, 0.62)
for i, f in enumerate(frames):
    scene.frame_set(int(f), subframe=f - int(f))
    common.render_views(os.path.join(common.REVIEW, 'tmp', f'{tag}_{i:02d}'), cz, hh, views=views, resolution=(300, 300))
