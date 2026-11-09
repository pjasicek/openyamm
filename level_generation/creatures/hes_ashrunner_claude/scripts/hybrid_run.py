"""Tier A's run (the pistol tier): Mixamo Standard Run's heel kicks went 7-8 cm out through the back of the long cloak
(g6_leg_leak.py), while the humanoid set's 2Hand Shooting Run Forward (the rifle tiers' run) stays within 3 cm. The
pistol run takes that run's pelvis, legs, spine, neck and head (action <legs> from the rifle chain's retarget blend)
and the arms (clavicles down, fingers included) of the Mixamo run, time-warped onto the legs' cycle by phase: each run's
phase starts at the frame where its LEFT foot is furthest forward (pelvis frame), so the arms counter-swing the legs as
in the source. Writes action <out> (replacing it). Args: -- <in blend> <out blend> <legs blend> <legs action>
<arms action> <out action>"""
import bpy, sys, os, math
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, legs_blend, legs_act, arms_act, out_act = a
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; AW = rig.matrix_world
with bpy.data.libraries.load(os.path.abspath(legs_blend), link=False) as (s_, d_):
    d_.actions = [legs_act]
LA = d_.actions[0]; AA = bpy.data.actions[arms_act]
ARMS = [b.name for b in rig.pose.bones if any(b.name.startswith(f'B_{s}_') and t in b.name
        for s in 'LR' for t in ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger'))]


def use(act):
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


def sample(act, t):
    use(act); sc.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
    return {pb.name: (pb.matrix_basis.to_quaternion().copy(), pb.matrix_basis.to_translation().copy()) for pb in rig.pose.bones}


def phase0(act):
    """frame where the left foot is furthest forward in the pelvis frame"""
    use(act); f0, f1 = (int(x) for x in act.frame_range); best = None
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        P = AW @ rig.pose.bones['B_Pelvis'].matrix
        lf = P.inverted() @ (AW @ rig.pose.bones['B_L_Foot'].matrix).translation
        fwd = (rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0)))
        d = lf.dot(fwd)
        if best is None or d > best[1]:
            best = (f, d)
    return best[0], f0, f1


lp, l0, l1 = phase0(LA); ap, a0, a1 = phase0(AA)
nl, na = l1 - l0, a1 - a0                                       # cycle lengths in frames (first = last frame)
old = bpy.data.actions.get(out_act)
new = bpy.data.actions.new(out_act + '_tmp'); new.use_fake_user = True
use(new)
for f in range(l0, l1 + 1):
    ph = ((f - lp) / nl) % 1.0
    L = sample(LA, f); A = sample(AA, a0 + ((ap - a0) / na + ph) % 1.0 * na)
    use(new)
    for pb in rig.pose.bones:
        q, t = (A if pb.name in ARMS else L)[pb.name]
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = t
        pb.keyframe_insert('rotation_quaternion', frame=f - l0); pb.keyframe_insert('location', frame=f - l0)
new.use_frame_range = True; new.frame_start, new.frame_end = 0, l1 - l0
if old:
    bpy.data.actions.remove(old)
new.name = out_act
bpy.data.actions.remove(LA)
print('HYBRIDRUN', out_act, 'frames', l1 - l0 + 1, 'legs phase frame', lp, 'arms phase frame', ap, 'arm bones', len(ARMS))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
