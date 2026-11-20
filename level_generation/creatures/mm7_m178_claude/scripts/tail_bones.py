"""Procedural tail motion for the m178 devil: the chain B_Tail0..B_Tail7 (build_rig.py from fit_joints.py's tail
points; bone heat) has no source counterpart, so every action is keyed on top of the retargeted body:
- carriage: the Smart Topology tail runs straight back at hip height for 1.25 m; the native sprites carry it rising
  behind the body in an arc (m178sa2, walk and attack side views). Each bone lifts by CARRY[k] degrees (local +X,
  bones rolled with local Z up), 26 degrees in all (the mesh's own end curl adds ~35);
- tilt compensation: the tail root would follow every forward pitch of the pelvis (a hunched walk, the forward death
  fall) and swing up past vertical; B_Tail0 takes back TILT_KEEP of the pelvis's tilt from its Standing frame-0 up
  vector (yaw is kept: the tail follows the body's heading);
- a side-to-side sway (about each bone's local Z) travelling down the chain (phase lag 0.6 rad per bone), whole
  cycles per clip so loops close, amplitude growing to the tip; a lift in the attack's wind-up; in the death the
  carriage and sway fade out, the end curl flattens and the tail lies down (the tilt compensation keeps it off the vertical).
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
NB = len([b for b in rig.data.bones if b.name.startswith('B_Tail')])
CARRY = [12.0, 3.0, 3.0, 3.0, 3.0, 2.0, 0.0, 0.0][:NB]   # the mesh's own end curl adds ~35 deg
TILT_KEEP = {'Death': 0.85}
print('TAIL bones', NB, 'carriage deg', sum(CARRY))


def set_act(a):
    rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


st = bpy.data.actions['Standing']; set_act(st); sc.frame_set(0)
UP = Vector((0, 0, 1))
pel_rest = (rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).to_3x3().normalized()
up_rest_local = pel_rest.inverted() @ UP                           # the pelvis's world up at Standing frame 0, in its frame
# per-bone amplitudes (8 bones add up: Walking reaches ~20 deg at the tip; 10 deg per bone swung the curl sideways
# into a vertical-looking hook in three-quarter views)
SWAY = {'Standing': (1, 2.5), 'Walking': (1, 4.5), 'Running': (1, 5.5), 'Fidget': (2, 3.5), 'Hit': (1, 5.0),
        'Attack': (1, 3.5), 'Death': (1, 3.5)}
for act in [x for x in bpy.data.actions if x.name in SWAY]:
    cyc, amp = SWAY[act.name]
    keep = TILT_KEEP.get(act.name, 0.6)
    set_act(act); f0, f1 = (int(x) for x in act.frame_range); n = max(f1 - f0, 1)
    tilts = []
    for f in range(f0, f1 + 1):
        u = (f - f0) / n
        fade = carry = 1.0; lift = 0.0; side = 0.0
        if act.name == 'Death':
            # the corpse's tail lies down: carriage off, then the end curl flattened (-36 deg over the last bones)
            fade = max(0.0, 1.0 - 1.5 * u); carry = max(-1.0, 1.0 - 2.4 * u)
        if act.name == 'Attack':
            side = float(os.environ.get('TAIL_SIDE', '0')) * math.sin(math.pi * min(1.0, 1.6 * u))   # tried +-18: the off hand's 4.2-4.7 cm touch of the tail root stays
            lift = 24.0 * math.sin(math.pi * min(1.0, 1.6 * u))         # rises with the wind-up and over the follow-through (the off hand swings back under it), settles
        sc.frame_set(f)
        for k in range(NB):
            pb = rig.pose.bones[f'B_Tail{k}']; pb.rotation_mode = 'QUATERNION'; pb.location = (0, 0, 0)
            pb.rotation_quaternion = Quaternion()
        bpy.context.view_layer.update()
        # tilt compensation on the root: rotate it back by `keep` of the pelvis's tilt (world up of the rest pelvis now)
        P = (rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).to_3x3().normalized()
        tilt = UP.rotation_difference(P @ up_rest_local)                  # world rotation taking up to the tilted up
        tilts.append(math.degrees(tilt.angle))
        back = Quaternion(tilt.axis, -tilt.angle * keep) if tilt.angle > 1e-6 else Quaternion()
        b0 = rig.pose.bones['B_Tail0']
        W0 = (rig.matrix_world @ b0.matrix).to_3x3().normalized()
        Wt = back.to_matrix() @ W0
        PL = (rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).to_3x3().normalized()
        rest_rel = (rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ rig.data.bones['B_Tail0'].matrix_local.to_3x3())
        comp = (rest_rel.inverted() @ PL.inverted() @ Wt).to_quaternion()
        for k in range(NB):
            pb = rig.pose.bones[f'B_Tail{k}']
            ph = 2 * math.pi * (cyc * u) - 0.6 * k
            yaw = math.radians(amp * fade * (0.35 + 0.65 * k / max(NB - 1, 1)) * math.sin(ph) + (side if k == 0 else 0.0))
            flat = (-24.0 if k >= NB - 4 else 0.0) * max(0.0, -carry)       # death: undo the mesh end curl (~95 deg)
            pitch = math.radians(CARRY[k] * max(carry, 0.0) + flat + (lift * 0.5 if k == 0 else lift * 0.5 / (NB - 1)))   # the lift mostly at the root
            q = Quaternion((1, 0, 0), pitch) @ Quaternion((0, 0, 1), yaw)
            pb.rotation_quaternion = (comp @ q) if k == 0 else q
            pb.keyframe_insert('rotation_quaternion', frame=f)
    print(f'TAIL {act.name}: pelvis tilt {min(tilts):.0f}..{max(tilts):.0f} deg, {keep:.2f} of it taken back at the root')
set_act(None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
