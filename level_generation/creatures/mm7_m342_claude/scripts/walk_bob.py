"""Even out the Walking clip's vertical bob (batch A review 2026-10-20: "uneven head bob ... at the end"). The retarget
sets the pelvis height per frame from the lowest foot point, so it zigzags where that point switches between heel and
toe (m222: 89.9, 90.4, 90.9, 89.7, 89.9 cm, then +2.7 cm in one frame) and the two steps of the cycle bob
differently. MM8 reductions fixed the same Mixamo walk on the GLB (mm8_m632_reduce_claude/scripts/smooth_walk_bob.py);
this is that rule in the chain, after clip_timing.py:
- new pelvis height = the two half cycles averaged (both steps bob the same), one periodic Gaussian pass (SIGMA
  frames), lowered by smooth local dips wherever both ankles would be out of reach (99.5 % of the leg length);
- both legs re-solved by two-bone IK in their own knee plane so every ankle keeps its world path and every foot its
  world rotation (no slide, lift or sink). Only B_Pelvis location and the thigh, calf and foot rotations of Walking change.
Args: -- <in blend> <out blend> (env SIGMA, default 1.5)"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
src, out = sys.argv[sys.argv.index('--') + 1:][:2]
SIGMA = float(os.environ.get('SIGMA', '1.5'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
names = [b.name for b in rig.data.bones]
LEGS = [f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf', 'Foot')]
act = bpy.data.actions['Walking']
rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); n = f1 - f0      # key f1 repeats key f0 (loop)
pel, ank, frot, hip, L = [], {s: [] for s in 'LR'}, {s: [] for s in 'LR'}, {s: [] for s in 'LR'}, {}
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    pel.append(armik.W(rig, 'B_Pelvis').translation.z)
    for s in 'LR':
        ank[s].append(armik.W(rig, f'B_{s}_Foot').translation.copy()); frot[s].append(armik.W(rig, f'B_{s}_Foot').to_3x3().normalized())
        hip[s].append(armik.W(rig, f'B_{s}_Thigh').translation.copy())
        L[s] = ((armik.W(rig, f'B_{s}_Calf').translation - hip[s][-1]).length, (ank[s][-1] - armik.W(rig, f'B_{s}_Calf').translation).length)
pel = np.array(pel)
assert abs(pel[0] - pel[-1]) < 1e-4, 'Walking is not a closed loop'
z = pel[:n]
per = lambda zz, t: np.interp(t % n, np.arange(n + 1), np.append(zz, zz[0]))
z = 0.5 * (z + per(z, np.arange(n) + n / 2))                                  # both steps bob the same
k = np.exp(-0.5 * (np.arange(-4, 5) / SIGMA) ** 2); k /= k.sum()
smooth = lambda zz: np.array([np.dot(k, zz[(i + np.arange(-4, 5)) % n]) for i in range(n)])
z = smooth(z)
lim = np.full(n, np.inf)
for s in 'LR':
    R = 0.995 * sum(L[s])
    for i in range(n):
        d = ank[s][i] - hip[s][i]; hor = math.hypot(d.x, d.y)
        lim[i] = min(lim[i], pel[i] + d.z + math.sqrt(max(R * R - hor * hor, 0.0)))
for _ in range(100):
    over = np.maximum(z - lim, 0)
    if over.max() < 1e-5:
        break
    z = z - smooth(np.array([over[(i + np.arange(-2, 3)) % n].max() for i in range(n)])) * 1.2
znew = np.append(z, z[0])
step = lambda zz: np.abs(np.diff(zz)).max(); acc = lambda zz: np.abs(np.diff(zz, 2)).max()
print(f'WALKBOB pelvis {100 * pel.min():.1f}..{100 * pel.max():.1f} -> {100 * znew.min():.1f}..{100 * znew.max():.1f} cm; '
      f'largest frame step {100 * step(pel):.2f} -> {100 * step(znew):.2f} cm, second difference {100 * acc(pel):.2f} -> {100 * acc(znew):.2f} cm')


def leg_ik(s, T, Mf):
    th, ca, ft = f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot'
    Hh = armik.W(rig, th).translation; Kk = armik.W(rig, ca).translation; Aa = armik.W(rig, ft).translation
    l1, l2 = (Kk - Hh).length, (Aa - Kk).length
    d = T - Hh; dist = min(d.length, (l1 + l2) * 0.999); u = d.normalized()
    p = (Kk - Hh) - u * (Kk - Hh).dot(u); v = p.normalized()                    # the current knee's bend side
    c = max(-1, min(1, (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)))
    K = Hh + l1 * (u * c + v * math.sqrt(1 - c * c))
    q = (Kk - Hh).normalized().rotation_difference((K - Hh).normalized())
    armik.set_world(rig, th, armik.rot_world(armik.W(rig, th), q.to_matrix() @ armik.W(rig, th).to_3x3().normalized()))
    Mc = armik.W(rig, ca)
    q2 = (armik.W(rig, ft).translation - Mc.translation).normalized().rotation_difference((Hh + u * dist - Mc.translation).normalized())
    armik.set_world(rig, ca, armik.rot_world(Mc, q2.to_matrix() @ Mc.to_3x3().normalized()))
    armik.set_world(rig, ft, armik.rot_world(armik.W(rig, ft), Mf))


keys, err = [], 0.0
for i, f in enumerate(range(f0, f1 + 1)):
    rig.animation_data.action = act; sc.frame_set(f)
    snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis = snap[pb.name]
    bpy.context.view_layer.update()
    M = armik.W(rig, 'B_Pelvis'); M.translation.z = float(znew[i]); armik.set_world(rig, 'B_Pelvis', M)
    for s in 'LR':
        leg_ik(s, ank[s][i], frot[s][i])
    bpy.context.view_layer.update()
    err = max(err, max((armik.W(rig, f'B_{s}_Foot').translation - ank[s][i]).length for s in 'LR'))
    keys.append({b: rig.pose.bones[b].rotation_quaternion.copy() for b in LEGS} | {'loc': rig.pose.bones['B_Pelvis'].location.copy()})
rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
prev = {}
for i, f in enumerate(range(f0, f1 + 1)):
    pb = rig.pose.bones['B_Pelvis']; pb.location = keys[i]['loc']; pb.keyframe_insert('location', frame=f)
    for b in LEGS:
        q = keys[i][b]
        if b in prev and q.dot(prev[b]) < 0:
            q = -q
        prev[b] = q; pb = rig.pose.bones[b]; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
rig.animation_data.action = None
print(f'WALKBOB legs re-solved: largest ankle path error {1000 * err:.2f} mm')
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
