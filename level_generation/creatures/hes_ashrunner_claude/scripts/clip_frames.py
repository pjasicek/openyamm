"""Clay frames of every listed clip of a rig file (N evenly spaced frames, several views; the rifle and every other
object included) -> <out dir>/<clip>_<i>_<view>.png and rows.json for compose_frames.py.
Args: -- <blend> <out dir> <frames> <views> clip [...]   (env CZ, CH: camera centre height and frame height)"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out, n, views, clips = a[1], int(a[2]), a[3].split(','), a[4:]
os.makedirs(out, exist_ok=True)
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; common.workbench_clay(sc, textured=bool(os.environ.get('TEXTURED')))
rows = []
for c in clips:
    act = bpy.data.actions[c]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1); sc.frame_set(int(f), subframe=f - int(f))
        row.append(common.render_views(os.path.join(out, f'{c}_{i}'), float(os.environ.get('CZ', '0.95')),
                                       float(os.environ.get('CH', '2.3')), views=tuple(views), resolution=(220, 300)))
    rows.append((c, row))
json.dump(rows, open(os.path.join(out, 'rows.json'), 'w'))
