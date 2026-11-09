"""Contact sheet of an action: N evenly spaced frames from fixed side/front cameras. Args: action N tag [views]."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
action_name, count, tag = args[0], int(args[1]), args[2]
views = args[3].split(',') if len(args) > 3 else ['left', 'front']
rig = bpy.data.objects['Peasant_Rig']
action = bpy.data.actions[action_name]
rig.animation_data.action = action
for o in bpy.data.objects:
    if o.type == 'MESH': o.hide_render = o.name != 'Peasant'
scene = bpy.context.scene
common.workbench_clay(scene, textured=len(args) > 4 and args[4] == 'tex')
if not (len(args) > 4 and args[4] == 'tex'):
    scene.display.shading.color_type = 'SINGLE'; scene.display.shading.single_color = (0.78, 0.7, 0.62)
f0, f1 = action.frame_range
for i in range(count):
    f = f0 + (f1 - f0) * i / max(1, count - (0 if action.get('hold') else 1))
    scene.frame_set(int(f), subframe=f - int(f))
    common.render_views(os.path.join(common.REVIEW, 'tmp', f'{tag}_{i:02d}'), 0.8, 1.75, views=views, resolution=(300, 300))
