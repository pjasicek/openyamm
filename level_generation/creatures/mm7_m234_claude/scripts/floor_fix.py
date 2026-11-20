"""Ground the standing clips: the hunched Mixamo idle on the gargoyle's digitigrade legs leaves the soles ~8 cm above the
floor, and the attack and fidget are planted on that Standing. For each listed action the lowest FOOT vertex (weight on
B_*_Foot / B_*_Toe0 > 0.5) is measured per frame and the clip's B_Pelvis keys are lowered by the clip's median of it
(a constant shift: the feet stay planted). Clips floored per frame elsewhere (Hit, Death) are not listed.
Args: -- <in blend> <out blend> <action> [...]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
gi = {g.index: g.name for g in body.vertex_groups}
feet = [v.index for v in me.vertices if sum(e.weight for e in v.groups if any(k in gi[e.group] for k in ('_Foot', '_Toe0'))) > 0.5]
Rinv = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()


def set_act(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and getattr(x, 'slots', None) is not None and len(x.slots):
        rig.animation_data.action_slot = x.slots[0]


for name in acts:
    act = bpy.data.actions[name]; set_act(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    lows = []
    for f in range(f0, f1 + 1):
        scene.frame_set(f); deps = bpy.context.evaluated_depsgraph_get()
        ev = body.evaluated_get(deps); m = ev.to_mesh()
        lows.append(min((body.matrix_world @ m.vertices[i].co).z for i in feet)); ev.to_mesh_clear()
    d = float(np.median(lows))
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        pb = rig.pose.bones['B_Pelvis']
        pb.location = pb.location + Rinv @ Vector((0, 0, -d))
        pb.keyframe_insert('location', frame=f)
    set_act(None)
    print('FLOORFIX', name, 'sole height median cm', round(d * 100, 1), 'range', round(min(lows) * 100, 1), round(max(lows) * 100, 1))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
