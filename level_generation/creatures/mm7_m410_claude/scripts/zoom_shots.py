"""Close clay renders (orthographic, centred on the chest or the bone CENTER) for listed frames of one action and views.
Args: -- <blend> <action> <out prefix> <frames a,b,c> [views comma list, default rside60,right,three_quarter]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, action, outp, frames = a[0], a[1], a[2], [int(x) for x in a[3].split(',')]
views = a[4].split(',') if len(a) > 4 else ['rside60', 'right', 'three_quarter']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene; common.workbench_clay(scene)
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
for f in frames:
    scene.frame_set(f)
    C = (rig.matrix_world @ rig.pose.bones[os.environ.get('CENTER', 'B_Spine2')].matrix).translation
    for v in views:
        common.render_views(f'{outp}_f{f}', C.z, 0.95, views=(v,), resolution=(640, 640), distance=9, target=(C.x, C.y))
print('ZOOM', outp)
