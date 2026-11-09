"""Procedural tail motion for the m418 troglodyte: the chain B_Tail0.. (built by build_rig.py from
fit_joints.py's tail points, bone-heat weights) has no source counterpart, so every action is keyed on top of the
pelvis motion (local rotations; bones rolled with local Z up):
- a side-to-side sway (about each bone's local Z) travelling down the chain (phase lag 0.6 rad per bone), whole cycles
  per clip so loops close (Standing 1, Walking/Running 1 per cycle = the stride rhythm, Fidget 2), amplitude growing to
  the tip;
- a pitch lift in the attack (the tail rises as the body leans into the blow) and a droop in the death (the tail
  falls limp as the body lies), with the sway fading out.
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
NB = len([b for b in rig.data.bones if b.name.startswith('B_Tail')])
print('TAIL bones', NB)


def set_act(a):
    rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


SWAY = {'Standing': (1, 6.0), 'Walking': (1, 12.0), 'Running': (1, 14.0), 'Fidget': (2, 10.0), 'Hit': (1, 14.0),
        'Attack': (1, 12.0), 'Death': (1, 10.0)}
for act in [x for x in bpy.data.actions if x.name in SWAY]:
    cyc, amp = SWAY.get(act.name, (1, 6.0))
    set_act(act); f0, f1 = (int(x) for x in act.frame_range); n = max(f1 - f0, 1)
    for f in range(f0, f1 + 1):
        u = (f - f0) / n
        fade = 1.0
        droop = 0.0
        if act.name == 'Death':
            fade = max(0.0, 1.0 - 1.5 * u)
        if act.name == 'Attack':
            droop = 12.0 * math.sin(math.pi * u)                  # the tail lifts (local +X pitch) as the body leans into the blow
        for k in range(NB):
            pb = rig.pose.bones[f'B_Tail{k}']; pb.rotation_mode = 'QUATERNION'
            ph = 2 * math.pi * (cyc * u) - 0.6 * k
            yaw = math.radians(amp * fade * (0.35 + 0.65 * k / max(NB - 1, 1)) * math.sin(ph))
            pitch = math.radians(droop / NB)
            pb.rotation_quaternion = Quaternion((1, 0, 0), pitch) @ Quaternion((0, 0, 1), yaw)
            pb.location = (0, 0, 0)
            pb.keyframe_insert('rotation_quaternion', frame=f)
set_act(None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
