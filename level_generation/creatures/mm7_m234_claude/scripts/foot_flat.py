"""Planted feet flat on the floor for the gargoyle's long clawed feet (user review 2026-10-20: "the feet should stand
FLAT on the floor; now they are angled, toes/claws tilted up, the sole rocking on the heel, one foot curled in the air").
Cause: the world-rotation retarget gives B_<s>_Foot the human source's foot direction, but our Foot segment is the long
digitigrade foot (hock -> ball), so the idle turned it ~40 deg off its rest and stood it on the heel pad; the source toe
channels curled the claws. foot_level.py could not catch it (its heel/toe references fell on the outer toe claw).
Per listed action, frame and foot (after clip_timing.py, so the stance blends and the attack steps are included):
- groundedness g = 1 while the hock is within LIFT0 of its rest height, fading to 0 at LIFT1 (a stepping foot keeps
  its lift);
- leg IK (two bones, the knee kept in its current bend plane) moves the hock to its rest height, weighted by g; when a
  planted leg cannot reach, the pelvis is lowered by the deficit for that frame;
- the foot's world orientation = its rest orientation turned about the vertical by the knee's heading change, in every
  frame (lifted feet stay level too);
- the toes (B_<s>_Toe0) take their rest relation to the foot (no curl) in every frame.
Action names may carry ':until=<frame>' (death: only until the fall). Prints the per-clip IK and pelvis changes.
Args: -- <in blend> <out blend> <Action>[:until=N] ..."""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, items = a[0], a[1], a[2:]
LIFT0, LIFT1 = float(os.environ.get('LIFT0', '0.015')), float(os.environ.get('LIFT1', '0.05'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']; MW = rig.matrix_world
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
P = rig.pose.bones
REST = {}
for s in 'LR':
    REST[s] = {'foot': (MW @ P[f'B_{s}_Foot'].matrix).copy(), 'hock_z': (MW @ P[f'B_{s}_Foot'].head).z,
               'heading': None}
PEL_RINV = rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()


def knee_heading(s):
    H, K, A = (MW @ P[f'B_{s}_Thigh'].head), (MW @ P[f'B_{s}_Calf'].head), (MW @ P[f'B_{s}_Foot'].head)
    d = K - (H + A) / 2; d.z = 0
    return math.atan2(d.y, d.x) if d.length > 1e-4 else 0.0


for s in 'LR':
    REST[s]['heading'] = knee_heading(s)


def set_act(x):
    rig.animation_data_create(); rig.animation_data.action = x
    if x is not None and getattr(x, 'slots', None) is not None and len(x.slots):
        rig.animation_data.action_slot = x.slots[0]


def rotate_about(pb, R, pivot):
    M = MW @ pb.matrix
    pb.matrix = MW.inverted() @ (Matrix.Translation(pivot) @ R.to_4x4() @ Matrix.Translation(-pivot) @ M)
    bpy.context.view_layer.update()


def aim(pb, frm, to, pivot):
    if frm.length < 1e-6 or to.length < 1e-6:
        return
    rotate_about(pb, frm.normalized().rotation_difference(to.normalized()).to_matrix(), pivot)


def leg_ik(s, target):
    th, ca = P[f'B_{s}_Thigh'], P[f'B_{s}_Calf']
    H, K, A = (MW @ th.head), (MW @ ca.head), (MW @ P[f'B_{s}_Foot'].head)
    la, lb = (K - H).length, (A - K).length
    d = (target - H).length
    d = min(max(d, abs(la - lb) + 1e-4), la + lb - 1e-4)
    u = (target - H).normalized()
    perp = (K - H) - u * (K - H).dot(u)
    if perp.length < 1e-6:
        perp = Vector((0, -1, 0)) - u * u.y * -1
    perp.normalize()
    x = (la * la - lb * lb + d * d) / (2 * d)
    K2 = H + u * x + perp * math.sqrt(max(la * la - x * x, 0.0))
    aim(th, K - H, K2 - H, H)
    K = MW @ ca.head; A = MW @ P[f'B_{s}_Foot'].head
    aim(ca, A - K, target - K, K)


for item in items:
    parts = item.split(':'); name = parts[0]
    until = int(parts[1].split('=')[1]) if len(parts) > 1 and parts[1].startswith('until=') else None
    act = bpy.data.actions[name]; set_act(act)
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    max_ik, max_pel, planted = 0.0, 0.0, 0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        k_until = 1.0 if until is None else max(0.0, min(1.0, (until + 6 - f) / 6.0))
        g = {}
        for s in 'LR':
            hz = (MW @ P[f'B_{s}_Foot'].head).z - REST[s]['hock_z']
            g[s] = k_until * max(0.0, min(1.0, (LIFT1 - hz) / (LIFT1 - LIFT0)))
        # pelvis: lower it when a planted leg cannot reach its rest hock height
        deficit = 0.0
        for s in 'LR':
            if g[s] <= 0:
                continue
            H = MW @ P[f'B_{s}_Thigh'].head; A = MW @ P[f'B_{s}_Foot'].head
            T = Vector((A.x, A.y, A.z + (REST[s]['hock_z'] - A.z) * g[s]))
            la = (MW @ P[f'B_{s}_Calf'].head - H).length; lb = (A - (MW @ P[f'B_{s}_Calf'].head)).length
            dz = (T - H).length - (la + lb - 0.004)
            if dz > 0:
                deficit = max(deficit, dz * g[s])
        if deficit > 0:
            pb = P['B_Pelvis']; pb.location = pb.location + PEL_RINV @ Vector((0, 0, -deficit))
            bpy.context.view_layer.update(); max_pel = max(max_pel, deficit)
        for s in 'LR':
            foot = P[f'B_{s}_Foot']
            if g[s] > 0:
                A = MW @ foot.head
                T = Vector((A.x, A.y, A.z + (REST[s]['hock_z'] - A.z) * g[s]))
                max_ik = max(max_ik, (T - A).length)
                leg_ik(s, T)
                planted += 1
            if k_until > 0:
                # foot: rest orientation turned by the knee heading change, in the air too (a stepping foot stays
                # level instead of tilting 40 deg and landing flat), faded out after the death's 'until'
                yaw = knee_heading(s) - REST[s]['heading']
                want = (Matrix.Rotation(yaw, 4, 'Z') @ REST[s]['foot']).to_quaternion()
                M = MW @ foot.matrix; cur = M.to_quaternion()
                q = cur.slerp(want, k_until)
                Mn = q.to_matrix().to_4x4(); Mn.translation = M.translation
                foot.matrix = MW.inverted() @ Mn
                bpy.context.view_layer.update()
            toe = P[f'B_{s}_Toe0']; toe.rotation_mode = 'QUATERNION'; toe.rotation_quaternion = Quaternion()
        bpy.context.view_layer.update()
        for s in 'LR':
            for b in ('Thigh', 'Calf', 'Foot', 'Toe0'):
                pb = P[f'B_{s}_{b}']; pb.rotation_mode = 'QUATERNION'; pb.keyframe_insert('rotation_quaternion', frame=f)
        P['B_Pelvis'].keyframe_insert('location', frame=f)
    set_act(None)
    print('FOOTFLAT', name, 'frames', f1 - f0 + 1, 'planted foot-frames', planted, 'max hock move cm', round(max_ik * 100, 1),
          'max pelvis drop cm', round(max_pel * 100, 1))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
