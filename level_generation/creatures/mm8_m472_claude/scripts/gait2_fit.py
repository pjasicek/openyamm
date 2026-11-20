"""gait2 (2026-10-21) robe fit of the retargeted walk and run: the floor-length robe hem reaches only about 0.22 m
before and behind the pelvis and cannot stretch around a 1.9 m Mixamo stride (G1 render: the trailing slipper hung
outside the robe 30 cm up). The playbook's run rule, applied to both clips (as mm6_natm_claude/scripts/run_fit.py):
each ankle follows the SOURCE's own path relative to the pelvis, forward travel scaled about its centre so the planted
foot covers STRIDE per cycle (stance speed stays constant, so the planted phase is kept), heights above the planted
level scaled by LIFT (less heel kick and knee drive under the cloth), the foot's world rotation slerped from Standing
toward the source's by PITCH; two-bone leg IK with the knee in the source's own leg plane. The cycle is resampled to
FRAMES (30 fps); upper body, arms and head keep the source motion. Pelvis drop below Standing scales with the step
(x stride ratio squared) and is lowered further only where a leg cannot reach. Args: -- <in blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik
src, out = sys.argv[sys.argv.index('--') + 1:]
# shift: the foot path's centre moved forward (m), so the trailing heel stays under the back hem (G7 round 1: the lifted
# trailing slipper showed 10-30 cm up behind the robe)
# back: once a foot leaves the floor (2-6 cm up) it is drawn in to at most this far behind the pelvis (m); only the
# airborne swing changes, so the planted phase and the stride are kept (round 2: the trailing slipper still showed
# 5-10 cm up behind the hem right after toe-off)
FIT = {'Walk2': dict(frames=23, stride=1.27, lift=.45, pitch=.45, shift=.05, back=.2),
       'Run2': dict(frames=21, stride=2.45, lift=.4, pitch=.5, shift=.07, back=.2)}
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; sc.render.fps = 30
names = [b.name for b in rig.data.bones]


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots): rig.animation_data.action_slot = a.slots[0]


def at(f):
    sc.frame_set(int(math.floor(f)), subframe=f - math.floor(f))


set_act(bpy.data.actions['Standing']); at(0)
ST_PEL = armik.W(rig, 'B_Pelvis').translation.z
ST_FOOT = {s: armik.W(rig, f'B_{s}_Foot').to_quaternion() for s in 'LR'}
L1 = {s: (rig.data.bones[f'B_{s}_Calf'].head_local - rig.data.bones[f'B_{s}_Thigh'].head_local).length for s in 'LR'}
L2 = {s: (rig.data.bones[f'B_{s}_Foot'].head_local - rig.data.bones[f'B_{s}_Calf'].head_local).length for s in 'LR'}
report = {}
for name, cfg in FIT.items():
    act = bpy.data.actions[name]; set_act(act); F = int(act.frame_range[1])
    # source: per frame pose, pelvis, ankles, knees, foot rotations (sampled at 4x for the stride measurement)
    rows = []
    for k in range(F * 4 + 1):
        at(k / 4)
        rows.append({'A': {s: np.array(armik.W(rig, f'B_{s}_Foot').translation) for s in 'LR'},
                     'P': np.array(armik.W(rig, 'B_Pelvis').translation)})
    stance = []
    for s in 'LR':
        A = np.array([r['A'][s] for r in rows]); z = A[:, 2]; v = np.gradient(A[:, 1]) * 120
        stance.append(np.median(v[(z < z.min() + .03) & (v > .02)]))     # planted: low and moving back (measure_stride.py)
    stride_src = float(np.mean(stance)) * F / 30; a = cfg['stride'] / stride_src
    rel = {s: np.array([r['A'][s] - r['P'] for r in rows]) for s in 'LR'}
    centre = {s: (rel[s][:, 1].min() + rel[s][:, 1].max()) / 2 for s in 'LR'}
    floor = {s: min(r['A'][s][2] for r in rows) for s in 'LR'}
    N = cfg['frames']; poses = []; lowered = []
    for i in range(N + 1):
        f = i * F / N; set_act(act); at(f)
        snap = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
        P = armik.W(rig, 'B_Pelvis').translation.copy()
        A = {s: armik.W(rig, f'B_{s}_Foot').translation.copy() for s in 'LR'}
        K = {s: armik.W(rig, f'B_{s}_Calf').translation.copy() for s in 'LR'}
        H = {s: armik.W(rig, f'B_{s}_Thigh').translation.copy() for s in 'LR'}
        Q = {s: armik.W(rig, f'B_{s}_Foot').to_quaternion() for s in 'LR'}
        set_act(None)
        for pb in rig.pose.bones: pb.matrix_basis = snap[pb.name]
        bpy.context.view_layer.update()
        target = {}
        for s in 'LR':
            r = A[s] - P; t = Vector(A[s]); t.y = P.y + centre[s] - cfg['shift'] + a * (r.y - centre[s])
            t.z = floor[s] + cfg['lift'] * (A[s].z - floor[s])
            w = float(np.clip((t.z - floor[s] - .02) / .04, 0, 1)); w = w * w * (3 - 2 * w)
            target[s] = t; target['pull' + s] = w * max(0., t.y - P.y - cfg['back'])
        newz = ST_PEL - (ST_PEL - P.z) * a * a
        need = 0.0
        for s in 'LR':      # hip moves with the pelvis; lower it where the leg cannot reach
            h = H[s] + Vector((0, 0, newz - P.z)); d = (target[s] - h).length; reach = (L1[s] + L2[s]) * .995
            if d > reach:
                dz = h.z - target[s].z; horiz = math.sqrt(max(0, d * d - dz * dz)); need = max(need, dz - math.sqrt(max(0, reach * reach - horiz * horiz)))
        lowered.append(need)
        poses.append((snap, newz, target, K, H, P, Q))
    lowered = np.array(lowered); lowered = np.maximum.reduce([np.roll(lowered, k) * (.6 ** abs(k)) for k in range(-3, 4)])
    # the swing pull-in, smoothed over time (cyclic, sigma 1.2 frames): applied raw it moved a run foot 20 cm within a
    # frame as it left the floor (thigh/calf 30 deg per half frame)
    kernel = np.exp(-.5 * (np.arange(-3, 4) / 1.2) ** 2); kernel /= kernel.sum()
    for s in 'LR':
        pull = np.array([pose[2]['pull' + s] for pose in poses[:-1]])
        pull = sum(np.roll(pull, k) * w for k, w in zip(range(-3, 4), kernel))
        for i, pose in enumerate(poses): pose[2][s].y -= float(pull[i % N])
    keys = []
    for i, (snap, newz, target, K, H, P, Q) in enumerate(poses):
        for pb in rig.pose.bones: pb.matrix_basis = snap[pb.name]
        bpy.context.view_layer.update()
        M = armik.W(rig, 'B_Pelvis'); M.translation.z = newz - float(lowered[i]); armik.set_world(rig, 'B_Pelvis', M)
        for s in 'LR':
            h = armik.W(rig, f'B_{s}_Thigh').translation; t = target[s]; d = min((t - h).length, (L1[s] + L2[s]) * .9995)
            u = (t - h).normalized(); along = (L1[s] ** 2 - L2[s] ** 2 + d * d) / (2 * d); hh = math.sqrt(max(0, L1[s] ** 2 - along ** 2))
            pole = K[s] - H[s] + Vector((0, -.08, 0))      # knee forward bias: a straight source leg left the plane undefined (176 deg flip)
            pole = (pole - u * pole.dot(u)).normalized(); knee = h + u * along + pole * hh
            ankle = h + u * d
            for bone, a0, a1, child in ((f'B_{s}_Thigh', h, knee, f'B_{s}_Calf'), (f'B_{s}_Calf', knee, ankle, f'B_{s}_Foot')):
                Mb = armik.W(rig, bone); cur = armik.W(rig, child).translation - Mb.translation
                R = cur.rotation_difference(a1 - Mb.translation).to_matrix()
                armik.set_world(rig, bone, armik.rot_world(Mb, R @ Mb.to_3x3()))
            q = ST_FOOT[s].slerp(Q[s] if ST_FOOT[s].dot(Q[s]) >= 0 else -Q[s], cfg['pitch'])
            armik.set_world(rig, f'B_{s}_Foot', armik.rot_world(armik.W(rig, f'B_{s}_Foot'), q.to_matrix()))
        keys.append({pb.name: (pb.rotation_quaternion.copy(), pb.location.copy()) for pb in rig.pose.bones})
    keys[-1] = keys[0]
    old = act.name; bpy.data.actions.remove(act); act = bpy.data.actions.new(old); act.use_fake_user = True; set_act(act)
    prev = {}
    for i, row in enumerate(keys):
        for n, (q, l) in row.items():
            if n not in snap or n.startswith(('Robe', 'Cuff', 'Hair', 'Tassel')) or 'Twist' in n: continue
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0: q = -q
            prev[n] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'B_Pelvis': pb.location = l; pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, N
    report[name] = {'source_stride_m': round(stride_src, 3), 'forward_scale': round(a, 3), 'frames': N, 'seconds': N / 30,
                    'target_stride_m': cfg['stride'], 'authored_speed': round(cfg['stride'] * 30 / N, 3),
                    'extra_pelvis_lowering_cm': round(float(lowered.max()) * 100, 2), **cfg}
    print('GAIT2_FIT', name, json.dumps(report[name]), flush=True)
set_act(None)
for pb in rig.pose.bones: pb.matrix_basis.identity()
sc['gait2_fit'] = json.dumps(report)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
