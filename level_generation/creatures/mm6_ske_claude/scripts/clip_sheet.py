"""Render N evenly spaced frames per action (one view) with the right-hand grip applied to bones the action does not
key; frames go to <out_dir>/<action>_<i>.png and labels to <out_dir>/frames.json (compose_sheet.py makes the sheet).
Args: -- <blend> <out_dir> <view: front|left|three_quarter|back|right> <frames per action> action [action ...]"""
import bpy, sys, os, json
from mathutils import Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, view, n = a[0], a[1], a[2], int(a[3]); acts = a[4:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Skeleton_Rig']
grip = json.loads(bpy.context.scene.get('ske_grip', '{}'))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'


def keyed(act):
    paths = set()
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for bag in strip.channelbags:
                paths.update(fc.data_path for fc in bag.fcurves)
    if hasattr(act, 'fcurves'):
        paths.update(fc.data_path for fc in act.fcurves)
    return paths


rows = []
for act_name in acts:
    act = bpy.data.actions[act_name]
    rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    paths = keyed(act)
    f0, f1 = act.frame_range
    row = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(n - 1, 1)
        scene.frame_set(int(f), subframe=f - int(f))
        for name, q in grip.items():
            if f'pose.bones["{name}"].rotation_quaternion' not in paths:
                rig.pose.bones[name].rotation_quaternion = Quaternion(q)
        bpy.context.view_layer.update()
        p = common.render_views(os.path.join(out, f'{act_name}_{i}'), 0.9, 2.1, views=(view,), resolution=(260, 420))[0]
        row.append([p, f'{act_name} {f:.1f}'])
    rows.append(row)
json.dump(rows, open(os.path.join(out, 'frames.json'), 'w'))
