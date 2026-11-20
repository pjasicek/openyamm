"""Play built clips faster: resample each named action at 60 Hz with its length divided by the factor (every keyed bone,
rotation and location; blends, smoothing and twist bakes are carried as built, only the timing changes).
Usage: blender -b -P time_scale.py -- <in blend> <out blend> <clip>:<factor> [...]"""
import math
import os
import re
import sys

import bpy

a = sys.argv[sys.argv.index('--') + 1:]
src_blend, out_blend, items = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
sc = bpy.context.scene; sc.render.fps = 60; rig = bpy.data.objects['Rig']


def use(act):
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def fcurves(act):
    if hasattr(act, 'fcurves'):
        return list(act.fcurves)
    return [fc for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves]


for item in items:
    clip, factor = item.split(':')[0], float(item.split(':')[1])
    src = bpy.data.actions[clip]; src.name = clip + '_x1'
    keyed = {}
    for fc in fcurves(src):
        m = re.match(r'pose\.bones\["(.+)"\]\.(rotation_quaternion|location)', fc.data_path)
        if m:
            keyed.setdefault(m.group(1), set()).add(m.group(2))
    f0, f1 = int(src.frame_range[0]), int(src.frame_range[1])
    n_new = int(round((f1 - f0) / factor))
    use(src)
    samples = []
    for i in range(n_new + 1):
        f = f0 + i * (f1 - f0) / n_new; sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))
        samples.append({n: (rig.pose.bones[n].rotation_quaternion.normalized(), rig.pose.bones[n].location.copy())
                        for n in keyed})
    act = bpy.data.actions.new(clip); act.use_fake_user = True; use(act)
    for i, pose in enumerate(samples):
        for n, (q, loc) in pose.items():
            pb = rig.pose.bones[n]
            if 'rotation_quaternion' in keyed[n]:
                pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=i)
            if 'location' in keyed[n]:
                pb.location = loc; pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, n_new
    src.use_fake_user = False; bpy.data.actions.remove(src)
    print(f'SCALED {clip}: {f1 - f0} -> {n_new} frames at 60 Hz = {n_new / 60:.3f} s (x{factor})')
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_blend))
