"""Zoomed clay renders of one action at given frames: camera view, centre z and ortho height configurable.
Args: -- <blend> <action> <out dir> <view> <centre z> <height> frame [frame ...]"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, action, out, view, cz, h = a[0], a[1], a[2], a[3], float(a[4]), float(a[5])
frames = [float(x) for x in a[6:]]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene; common.workbench_clay(scene)
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
row = []
for f in frames:
    scene.frame_set(int(f), subframe=f - int(f))
    p = common.render_views(os.path.join(out, f'{action}_{f:g}'), cz, h, views=(view,), resolution=(400, 400))[0]
    row.append([p, f'{action} {f:g} {view}'])
json.dump([row], open(os.path.join(out, 'frames.json'), 'w'))
