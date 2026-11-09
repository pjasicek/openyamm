"""Clay frames of clips (all visible mesh objects, rigged ones posed). Args: -- <blend> <out dir> <frames> <views csv>
<clip> [...]; writes <out>/<clip>_<i>_<view>.png and rows.json (for sheet.py)."""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out, n, views, clips = a[1], int(a[2]), a[3].split(','), a[4:]
os.makedirs(out, exist_ok=True)
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; common.workbench_clay(sc, os.environ.get('TEX') == '1')
for o in bpy.data.objects:
    if o.name == 'Demon': o.hide_render = True
rows = []
for c in clips:
    act = bpy.data.actions[c]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1); sc.frame_set(int(f), subframe=f - int(f))
        row.append(common.render_views(os.path.join(out, f'{c}_{i}'), float(os.environ.get('CZ', '0.95')), float(os.environ.get('CH', '2.2')),
                                       views=tuple(views), resolution=tuple(int(x) for x in os.environ.get('RES', '240,320').split(','))))
    rows.append((c, row))
json.dump(rows, open(os.path.join(out, 'rows.json'), 'w'))
