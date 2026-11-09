"""Render N evenly spaced frames per action of the Rig (one view) to <out_dir>/<action>_<i>.png + frames.json.
Args: -- <blend> <out_dir> <view> <frames per action> action [action ...]"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, view, n = a[0], a[1], a[2], int(a[3]); acts = a[4:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene; common.workbench_clay(scene)
from sword import add_sword
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
sword=add_sword(rig)
rows = []
for name in acts:
    act = bpy.data.actions[name]
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1)
        scene.frame_set(int(f), subframe=f - int(f))
        p = common.render_views(os.path.join(out, f'{name}_{i}'), 0.9, 2.7, views=(view,), resolution=(260, 420))[0]
        row.append([p, f'{name} {f:.1f}'])
    rows.append(row)
json.dump(rows, open(os.path.join(out, 'frames.json'), 'w'))
