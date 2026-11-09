"""One-shot clips clip_timing.py does not handle (Forad 2026-10-30: Talk, Bow, AttackMelee from Mixamo, planted):
ease in from and out to Standing frame 0 over BLEND seconds (smoothstep, every bone; the engine crossfades only
0.06-0.12 s), quaternions sign-continuous. AttackMelee: impact = the key where the punching hand (the one that
travels farthest forward of the chest) is most forward; printed as IMPACT for actors.yml events.
Args: -- <in blend> <out blend>"""
import bpy, sys, os
from mathutils import Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
sc = bpy.context.scene; sc.render.fps = 30
rig = bpy.data.objects['Rig']
BLEND = {'Talk': (0.3, 0.3), 'Bow': (0.3, 0.3), 'AttackMelee': (0.15, 0.25)}
names = [b.name for b in rig.data.bones]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if getattr(a, 'slots', None) is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


set_act(bpy.data.actions['Standing']); sc.frame_set(0)
st = {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}
for nm, (bi, bo) in BLEND.items():
    if nm not in bpy.data.actions:
        continue
    act = bpy.data.actions[nm]; set_act(act)
    f0, f1 = (int(x) for x in act.frame_range)
    poses = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        poses.append({n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names})
    if nm == 'AttackMelee':
        best = (-1, 0, '')
        for k in range(len(poses)):
            sc.frame_set(f0 + k)
            chest = rig.matrix_world @ rig.pose.bones['B_Spine2'].head
            for sd in 'LR':
                hnd = rig.matrix_world @ rig.pose.bones[f'B_{sd}_Hand'].head
                fwd = -(hnd - chest).y                      # facing -Y
                if fwd > best[0]:
                    best = (fwd, k, sd)
        print('IMPACT AttackMelee', round(best[1] / 30.0, 3), 's hand', best[2], 'reach m', round(best[0], 3))
    if nm == 'Bow' and float(os.environ.get('BOW_GAIN', '1.8')) != 1.0:
        # Mixamo's Quick Formal Bow bends mostly the upper back (~25 deg); MM9's bow is a deeper courtly bow: the
        # spine chain's flexion away from the clip's first pose is scaled (the arms hang and follow in world space)
        g = float(os.environ.get('BOW_GAIN', '1.8'))
        for P in poses:
            for b in ('B_Spine', 'B_Spine1', 'B_Spine2'):
                q0 = poses[0][b][0]; q = P[b][0]
                d = q0.inverted() @ q
                ax, ang = d.to_axis_angle()
                from mathutils import Quaternion as _Q
                P[b] = (q0 @ _Q(ax, ang * g), P[b][1])
        print('EXTRA Bow spine flexion gain', g)
    n = len(poses); ni, no = int(bi * 30), int(bo * 30)
    act_new = bpy.data.actions.new(nm + '_x'); act_new.use_fake_user = True
    set_act(act_new)
    for k, P in enumerate(poses):
        w = 0.0
        if k < ni:
            w = 1 - k / ni
        if k > n - 1 - no:
            w = max(w, (k - (n - 1 - no)) / no)
        w = w * w * (3 - 2 * w)
        for b in names:
            q, l = P[b]; qs, ls = st[b]
            if q.dot(qs) < 0:
                qs = -qs
            pb = rig.pose.bones[b]; pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = q.slerp(qs, w); pb.location = l.lerp(ls, w)
            pb.keyframe_insert('rotation_quaternion', frame=f0 + k); pb.keyframe_insert('location', frame=f0 + k)
    bpy.data.actions.remove(act)
    act_new.name = nm
    print('EXTRA', nm, 'frames', n, 'blend in/out s', bi, bo)
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
