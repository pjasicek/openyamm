"""Authored Death for the m418 troglodyte (replaces the retargeted one): the native rears up and falls onto its back
(m418da0-de0). A human death clip falls 90 degrees from upright, which stood this horizontal body on its tail
(Mixamo Mutant Dying via KEEP_REST), so the fall is authored on top of Standing frame 0:
- 0-0.30 s: rears back: the spine pitches the hood up (3 x 8 deg), the upper arms lift 40 deg, the head 10 deg;
- 0.30-0.85 s: rolls about the body's long axis (world Y through the pelvis) 0 -> 118 deg, eased in (falling), as the
  spine straightens, the thighs pull up 35 deg, the calves fold 40 deg and the arms curl 30 deg;
- 0.85-1.20 s: bounce 118 -> 108 -> 112 deg and the limbs relax 20 %; held to 1.50 s;
- every frame: the pelvis moves vertically so the lowest evaluated mesh point sits on the floor (z 0).
Limb and spine deltas are world rotations in the unrolled body (each bone about its own head), then the roll is
applied to the pelvis only. Args: -- <in blend> <out blend> [roll side +1|-1]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out = a[0], a[1]
SIDE = float(a[2]) if len(a) > 2 else 1.0
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
FPS = 30; N = 45


def set_act(act):
    rig.animation_data_create(); rig.animation_data.action = act
    if act is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]


set_act(bpy.data.actions['Standing']); sc.frame_set(0)
BASE = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
if 'Death' in bpy.data.actions:
    bpy.data.actions.remove(bpy.data.actions['Death'])
act = bpy.data.actions.new('Death'); act.use_fake_user = True
set_act(act)
smooth = lambda u: u * u * (3 - 2 * u)
clamp = lambda u: max(0.0, min(1.0, u))


def curve(t):
    rear = smooth(clamp(t / 0.30)) * (1 - smooth(clamp((t - 0.30) / 0.4)))
    fall = clamp((t - 0.30) / 0.55)
    roll = 118 * fall * fall
    if t > 0.85:
        u = clamp((t - 0.85) / 0.2); roll = 118 - 10 * smooth(u)
        if t > 1.05:
            roll = 108 + 4 * smooth(clamp((t - 1.05) / 0.15))
    curl = smooth(clamp((t - 0.30) / 0.55)) * (1 - 0.2 * smooth(clamp((t - 0.85) / 0.35)))
    return rear, roll, curl


def world_delta(name, R):
    """rotate bone `name` by world rotation R about its own head (pose space = world: rig at the origin)"""
    pb = rig.pose.bones[name]
    M = pb.matrix.copy(); h = M.translation.copy()
    Mn = R.to_4x4() @ M; Mn.translation = h
    pb.matrix = Mn
    bpy.context.view_layer.update()


RX = lambda deg: Matrix.Rotation(math.radians(deg), 3, 'X')
mins = []
for f in range(N + 1):
    t = f / FPS
    rear, roll, curl = curve(t)
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.matrix_basis = BASE[pb.name].copy()
    bpy.context.view_layer.update()
    for n in ('B_Spine', 'B_Spine1', 'B_Spine2'):
        world_delta(n, RX(-8 * rear + 6 * curl))
    world_delta('B_Head', RX(-10 * rear + 8 * curl))
    for s in 'LR':
        world_delta(f'B_{s}_UpperArm', RX(-40 * rear - 30 * curl))
        world_delta(f'B_{s}_Forearm', RX(-30 * curl))
        world_delta(f'B_{s}_Thigh', RX(-35 * curl))
        world_delta(f'B_{s}_Calf', RX(40 * curl))
    basis = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    pel = rig.pose.bones['B_Pelvis']
    M = pel.matrix.copy(); piv = M.translation.copy()
    R = Matrix.Rotation(math.radians(SIDE * roll), 4, 'Y')
    Mn = Matrix.Translation(piv) @ R @ Matrix.Translation(-piv) @ M
    pel.matrix = Mn
    for pb in rig.pose.bones:
        if pb.name != 'B_Pelvis':
            pb.matrix_basis = basis[pb.name]
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(deps); me = ev.to_mesh()
    zmin = min((body.matrix_world @ v.co).z for v in me.vertices); ev.to_mesh_clear()
    Mn = pel.matrix.copy(); Mn.translation.z -= zmin
    pel.matrix = Mn; bpy.context.view_layer.update()
    mins.append(zmin)
    for pb in rig.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=f)
        if pb.name == 'B_Pelvis':
            pb.keyframe_insert('location', frame=f)
act.use_frame_range = True; act.frame_start, act.frame_end = 0, N
set_act(None)
print(f'DEATH authored {N + 1} frames ({N / FPS:.2f} s), roll side {SIDE:+.0f}, floor correction cm '
      f'{100 * min(mins):.1f}..{100 * max(mins):.1f}')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
