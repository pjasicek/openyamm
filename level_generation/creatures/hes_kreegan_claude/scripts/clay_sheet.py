"""Clay contact sheet of every listed clip (N evenly spaced frames, one view) of the rig file, no prop stand-ins.
Args: -- <blend> <out png> <view> <frames per clip> <clip> [...]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out, view, n, clips = a[1], a[2], int(a[3]), a[4:]
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; common.workbench_clay(sc)
tmp = os.path.join(os.path.dirname(os.path.abspath(out)), '_clay'); os.makedirs(tmp, exist_ok=True)
rows = []
for c in clips:
    act = bpy.data.actions[c]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1); sc.frame_set(int(f), subframe=f - int(f))
        row.append(common.render_views(os.path.join(tmp, f'{c}_{i}'), float(os.environ.get('CZ', '0.95')), float(os.environ.get('CH', '2.2')),
                                       views=(view,), resolution=(240, 300))[0])
    rows.append((c, row))
import json; json.dump(rows, open(os.path.join(tmp, 'rows.json'), 'w'))
