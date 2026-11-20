"""Clay renders of N evenly spaced frames per action, one row per action and view, for sheet.py.
Args: -- <blend> <out dir> <frames per action> <views comma list> action [...]   (env TEXTURED=1: texture colours)"""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, n, views, acts = a[0], a[1], int(a[2]), a[3].split(','), a[4:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
scene = bpy.context.scene; common.workbench_clay(scene, textured=bool(os.environ.get('TEXTURED')))
H = float(os.environ.get('HEIGHT', '1.95')); ZC = float(os.environ.get('ZC', '0.85'))
rows = []
for name in acts:
    act = bpy.data.actions[name]
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    for view in views:
        row = []
        for i in range(n):
            f = f0 + (f1 - f0) * i / max(n - 1, 1)
            scene.frame_set(int(f), subframe=f - int(f))
            pel = rig.matrix_world @ rig.pose.bones['B_Pelvis'].head
            p = common.render_views(os.path.join(out, f'{name}_{view}_{i}'), ZC, H, views=(view,), resolution=(300, 420),
                                    target=(pel.x, pel.y))[0]
            row.append(p)
        rows.append({'label': f'{name} [{view}] frames {f0:.0f}-{f1:.0f}', 'frames': row})
json.dump(rows, open(os.path.join(out, 'frames.json'), 'w'), indent=1)
print('RENDERED', len(rows), 'rows')
