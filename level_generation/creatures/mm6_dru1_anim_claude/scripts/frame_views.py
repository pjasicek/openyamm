"""Render one action at given frames from front/left/three_quarter (clay). Args: -- <blend> <action> <out prefix> frame [frame ...]"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, action, out, frames = a[0], a[1], a[2], [float(x) for x in a[3:]]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene; common.workbench_clay(scene)
act = bpy.data.actions[action]; rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
rows = []
for f in frames:
    scene.frame_set(int(f), subframe=f - int(f))
    ps = common.render_views(f'{out}_{action}_{f:g}', 0.85, 2.0, views=('front', 'left', 'three_quarter'), resolution=(400, 500))
    rows.append([[p, f'{action} {f:g} {v}'] for p, v in zip(ps, ('front', 'left', '3/4'))])
d = os.path.dirname(out)
json.dump(rows, open(os.path.join(d, 'frames.json'), 'w'))
