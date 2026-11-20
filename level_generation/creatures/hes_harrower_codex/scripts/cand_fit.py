"""Candidate attack clips from the library, full body and source arms (2026-10-24 attack review).
The bound Attack/Attack2 kept only 20 % of the mocap upper body over Standing and replaced both arms with authored wrist
paths, which read as weak. Here the retargeted clip drives every body bone; only these change:
- a window [f0, f1] of the source at its own 30 fps (no retime);
- heading: the source root's (the library characters face their target along the root; Mixamo's fighting stance is
  turned 30-40 deg off it on purpose); an optional constant yaw_deg about the source pelvis at f0, which is moved onto
  Standing's pelvis (aligning f0's chest to Standing turned mid-spin windows away from the target);
- travel: the pelvis's horizontal path and every foot's displacement from its own position at f0 are scaled by k, the
  legs then solved by two-bone IK (planted feet stay planted, steps shrink), the source foot rotation kept;
- ground: the pelvis moves vertically so the lowest claw-foot vertex sits on the floor (ground 'snap', the set's deep
  in-place guard sank our long feet up to 28 cm; Gaussian-smoothed, never below a frame's own need) or only comes out
  of it (ground 'lift', for clips whose feet keep the source heights through the IK);
- the ends ease from and back to Standing frame 0 (smoothstep over blend_in / blend_out seconds, local slerp);
- the solved crescent grip (grip_pose_<S>.json finger channels) on every frame; the hand keeps the source rotation, so
  the handle lies along the source weapon axis;
- helper bones as the bound clips: forearm twist 0.6 of the hand roll, upper-arm counter-twist 0.5, pauldrons follow
  the upper arm at `pauldron` (0.8 in final_fit.py);
- clearance for our wider body (shoulder spikes, chest plate, belt, knee and shin plates) and longer blades, each
  measured by the gates first: `abduct_deg` turns both upper arms out about the chest's forward axis; the wrist swing is
  scaled down to `wrist_max` deg (arm gate 60) and its twist kept within +-`twist_max` deg; the bend of each spine bone (swing off its axis) to `spine_bend_max`
  deg (the spine plates met in deep arches); where the shins or knees of the two legs come closer than `leg_gap` m
  (spins cross the legs), the higher foot steps out by the deficit (IK, Gaussian-smoothed).
Writes Harrower_<name> keyed on every frame. Args: -- <in blend> <out blend> <config json>"""
from pathlib import Path
import sys, json, math
import bpy
import numpy as np
from mathutils import Vector, Matrix, Quaternion
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts')); import armik
src_blend, out_blend, cfg_path = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=str(Path(src_blend).resolve()))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; sc.render.fps = 30; sc.render.fps_base = 1
CFG = json.loads(Path(cfg_path).read_text())
G = {s: json.loads((P / f'work/grip_pose_{s}.json').read_text()) for s in 'LR'}
CORE = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_Head'] + [f'B_{s}_{b}' for s in 'LR' for b in (
    'Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Thigh', 'Calf', 'Foot')]
FEET = {s: (f'B_{s}_Thigh', f'B_{s}_Calf', f'B_{s}_Foot') for s in 'LR'}
CHEST_FWD = rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))


def set_action(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


def snap():
    return {b.name: b.matrix_basis.copy() for b in rig.pose.bones}


def restore(s):
    set_action(None)
    for n, m in s.items():
        rig.pose.bones[n].matrix_basis = m
    bpy.context.view_layer.update()


def chest_yaw():
    f = armik.W(rig, 'B_Spine2').to_3x3() @ CHEST_FWD
    return math.atan2(f.y, f.x)


def two_bone(s, target, foot_rot):
    """thigh and calf so the ankle reaches target, knee in its current plane; then the foot's world rotation"""
    th, ca, ft = FEET[s]
    H, K, A = armik.W(rig, th).translation, armik.W(rig, ca).translation, armik.W(rig, ft).translation
    L1, L2 = (K - H).length, (A - K).length; d = target - H; dist = min(d.length, (L1 + L2) * 0.999)
    u = d.normalized(); pole = (K - H) - u * (K - H).dot(u)
    pole = pole.normalized() if pole.length > 1e-6 else Vector((0, -1, 0))
    c = max(-1.0, min(1.0, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)))
    Kn = H + L1 * (u * c + pole * math.sqrt(max(0.0, 1 - c * c)))
    M = armik.W(rig, th); armik.set_world(rig, th, armik.rot_world(M, (K - H).normalized().rotation_difference((Kn - H).normalized()).to_matrix() @ M.to_3x3().normalized()))
    M = armik.W(rig, ca); A2 = armik.W(rig, ft).translation
    q = (A2 - M.translation).normalized().rotation_difference((H + u * dist - M.translation).normalized())
    armik.set_world(rig, ca, armik.rot_world(M, q.to_matrix() @ M.to_3x3().normalized()))
    armik.set_world(rig, ft, armik.rot_world(armik.W(rig, ft), foot_rot))


def helpers():
    """twist helpers and pauldrons from the current pose (fit_motion.py, final_fit.py)"""
    REST = lambda n: rig.data.bones[n].matrix_local.to_3x3()
    for sd in 'LR':
        fb = rig.data.bones[f'B_{sd}_Forearm']; hb = rig.data.bones[f'B_{sd}_Hand']
        axis = (fb.matrix_local.inverted() @ hb.head_local).normalized()
        rel = (rig.pose.bones[fb.name].matrix.inverted() @ rig.pose.bones[hb.name].matrix).to_quaternion()
        rest = (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion()
        _, tw = armik.split_swing_twist(rel @ rest.inverted(), axis)
        pb = rig.pose.bones[f'B_{sd}_ForearmTwist']; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(axis, .6 * tw)
        ub = rig.data.bones[f'B_{sd}_UpperArm']; axis = (ub.matrix_local.inverted() @ fb.head_local).normalized()
        _, tw = armik.split_swing_twist(rig.pose.bones[ub.name].matrix_basis.to_quaternion(), axis)
        pb = rig.pose.bones[f'B_{sd}_UpperArmTwist']; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(axis, -.5 * tw)
        bpy.context.view_layer.update()
        ua = rig.pose.bones[f'B_{sd}_UpperArm']; cl = rig.pose.bones[f'B_{sd}_Clavicle']; name = f'B_{sd}_Pauldron'
        q = (REST(cl.name).inverted() @ REST(ua.name).col[1]).rotation_difference(cl.matrix.to_3x3().inverted() @ ua.matrix.to_3x3().col[1])
        q = Quaternion(q.axis, q.angle * PAULDRON) if q.angle > 1e-6 else Quaternion(); Rb = REST(cl.name).inverted() @ REST(name)
        pb = rig.pose.bones[name]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (Rb.inverted() @ q.to_matrix() @ Rb).to_quaternion()
    bpy.context.view_layer.update()


body = bpy.data.objects['Body']; VG = [g.name for g in body.vertex_groups]
FOOTV = np.array([sum(e.weight for e in v.groups if VG[e.group].endswith(('_Foot', '_Toe0'))) > 0.5 for v in body.data.vertices])


def lowest_foot():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    co = co.reshape(-1, 3)[FOOTV] @ np.array(body.matrix_world.to_3x3()).T
    return float(co[:, 2].min() + body.matrix_world.translation.z)


def seg_seg(p1, q1, p2, q2):
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2; a, e, f = d1.dot(d1), d2.dot(d2), d2.dot(r); c_ = d1.dot(r); b = d1.dot(d2)
    den = a * e - b * b; s_ = max(0.0, min(1.0, (b * f - c_ * e) / den)) if den > 1e-9 else 0.0
    t_ = max(0.0, min(1.0, (b * s_ + f) / e)); s_ = max(0.0, min(1.0, (b * t_ - c_) / a))
    x, y = p1 + d1 * s_, p2 + d2 * t_
    return (x - y).length, x, y


def leg_points():
    J = lambda n: armik.W(rig, n).translation.copy()
    return {s: [J(f'B_{s}_Thigh'), J(f'B_{s}_Calf'), J(f'B_{s}_Foot'), J(f'B_{s}_Toe0')] for s in 'LR'}


def legs_gap():
    L = leg_points(); best = (9.0, None, None)
    for i in (0, 1, 2):
        for j in (0, 1, 2):
            if i == 0 and j == 0: continue                 # thighs meet at the hips by design
            d, x, y = seg_seg(L['L'][i], L['L'][i + 1], L['R'][j], L['R'][j + 1])
            if d < best[0]: best = (d, x, y)
    return best


def clamp_swing(pb, axis, limit_deg, twist_deg=0.0):
    q = pb.rotation_quaternion.copy(); sw, t = armik.split_swing_twist(q, axis)
    if twist_deg and abs(t) > math.radians(twist_deg):
        t = math.copysign(math.radians(twist_deg), t); pb.rotation_quaternion = sw @ Quaternion(axis, t)
    ang = sw.angle if sw.angle <= math.pi else 2 * math.pi - sw.angle
    if ang > math.radians(limit_deg):
        pb.rotation_quaternion = Quaternion().slerp(sw, math.radians(limit_deg) / ang) @ Quaternion(axis, t)
        return math.degrees(ang)
    return 0.0


set_action(bpy.data.actions['Harrower_Standing']); sc.frame_set(0); ST = snap()
ST_PEL = armik.W(rig, 'B_Pelvis').translation.copy(); ST_YAW = chest_yaw()
report = {}
for c in CFG:
    src = bpy.data.actions[c['src']]; f0, f1 = c['window']; k = float(c.get('k', 1.0)); n = f1 - f0
    # pass 1: source pose, world pelvis and feet per frame
    S = []
    for f in range(f0, f1 + 1):
        set_action(src); sc.frame_set(f)
        S.append({'basis': snap(), 'pel': armik.W(rig, 'B_Pelvis').copy(), 'yaw': chest_yaw(),
                  'feet': {s: armik.W(rig, FEET[s][2]).copy() for s in 'LR'}})
    yaw = math.radians(c.get('yaw_deg', 0.0))
    C = Matrix.Rotation(yaw, 4, 'Z'); C3 = C.to_3x3(); p0 = S[0]['pel'].translation.copy()
    pivot = lambda x: Vector((ST_PEL.x, ST_PEL.y, 0)) + C3 @ Vector((x.x - p0.x, x.y - p0.y, 0)) + Vector((0, 0, x.z))
    poses = []; slide = 0.0
    for i, s_ in enumerate(S):
        base = {nm: m.copy() for nm, m in ST.items()}
        for nm in CORE:
            base[nm] = s_['basis'][nm].copy()
        restore(base)
        pw = s_['pel']; d = pw.translation - p0
        pos = pivot(p0 + Vector((d.x * k, d.y * k, d.z)))
        M = (C3 @ pw.to_3x3().normalized()).to_4x4(); M.translation = pos; armik.set_world(rig, 'B_Pelvis', M)
        if abs(k - 1.0) > 1e-6:
            for sd in 'LR':
                F = s_['feet'][sd]; F0 = S[0]['feet'][sd]
                tgt = pivot(F0.translation) + C3 @ ((F.translation - F0.translation) * k)
                tgt.z = pivot(F.translation).z
                two_bone(sd, tgt, C3 @ F.to_3x3().normalized())
                slide = max(slide, (armik.W(rig, FEET[sd][2]).translation - tgt).length)
        ab = math.radians(float(c.get('abduct_deg', 0.0)))
        if ab:
            fwd = (armik.W(rig, 'B_Spine2').to_3x3() @ CHEST_FWD).normalized()
            for sd, sg in (('L', 1), ('R', -1)):
                M = armik.W(rig, f'B_{sd}_UpperArm'); armik.set_world(rig, f'B_{sd}_UpperArm', armik.rot_world(M, Matrix.Rotation(sg * ab, 3, fwd) @ M.to_3x3().normalized()))
        for sd in 'LR':
            for bn, quat in G[sd]['finger_local'].items():
                pb = rig.pose.bones[bn]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(quat)
        bpy.context.view_layer.update(); poses.append(snap())
    # legs apart where spins cross them
    gap = float(c.get('leg_gap', 0.0)); offs = []
    for pz in poses:
        restore(pz); o = Vector()
        if gap:
            d, x, y = legs_gap()
            if d < gap:
                L = leg_points(); up = 'L' if L['L'][2].z > L['R'][2].z else 'R'
                push = (x - y) if up == 'L' else (y - x); push.z = 0
                if push.length > 1e-6: o = push.normalized() * (gap - d)
                o = (up, o)
        offs.append(o)
    if gap:
        for sd in 'LR':
            arr = np.array([list(o[1]) if isinstance(o, tuple) and o[0] == sd else [0, 0, 0] for o in offs])
            r = 4; kern = np.exp(-.5 * (np.arange(-r, r + 1) / 2.0) ** 2); kern /= kern.sum()
            sm = np.stack([np.convolve(np.pad(arr[:, j], r, mode='edge'), kern, mode='valid') for j in range(3)], 1)
            mag = np.linalg.norm(arr, axis=1); smag = np.linalg.norm(sm, axis=1)
            sm = np.where((mag > smag)[:, None], arr, sm)
            for pz, v in zip(poses, sm):
                if np.linalg.norm(v) < 1e-5: continue
                restore(pz); F = armik.W(rig, FEET[sd][2]); two_bone(sd, F.translation + Vector(v), F.to_3x3().normalized())
                for b in FEET[sd]: pz[b] = rig.pose.bones[b].matrix_basis.copy()
    # wrist swing and spine bend limits
    wmax = float(c.get('wrist_max', 0.0)); smax = float(c.get('spine_bend_max', 0.0)); clamped = {'wrist': 0.0, 'spine': 0.0}
    for pz in poses:
        restore(pz)
        if wmax:
            for sd in 'LR':
                fa, hd = rig.data.bones[f'B_{sd}_Forearm'], rig.data.bones[f'B_{sd}_Hand']
                axis = (hd.matrix_local.to_3x3().inverted() @ (hd.head_local - fa.head_local)).normalized()
                clamped['wrist'] = max(clamped['wrist'], clamp_swing(rig.pose.bones[hd.name], axis, wmax, float(c.get('twist_max', 0.0))))
        if smax:
            for bn in ('B_Spine', 'B_Spine1', 'B_Spine2'):
                clamped['spine'] = max(clamped['spine'], clamp_swing(rig.pose.bones[bn], Vector((0, 1, 0)), smax))
        bpy.context.view_layer.update()
        for bn in ('B_L_Hand', 'B_R_Hand', 'B_Spine', 'B_Spine1', 'B_Spine2'): pz[bn] = rig.pose.bones[bn].matrix_basis.copy()
    need = []
    for pz in poses:
        restore(pz); low = lowest_foot(); need.append(-low if c.get('ground', 'snap') == 'snap' else max(0.0, -low))
    need = np.array(need); r = 4; kern = np.exp(-.5 * (np.arange(-r, r + 1) / 1.5) ** 2); kern /= kern.sum()
    smooth = np.convolve(np.pad(need, r, mode='edge'), kern, mode='valid')
    dz = np.where(need > 0, np.maximum(smooth, need), smooth)
    for pz, z in zip(poses, dz):
        restore(pz); M = armik.W(rig, 'B_Pelvis'); M.translation.z += float(z); armik.set_world(rig, 'B_Pelvis', M)
        pz['B_Pelvis'] = rig.pose.bones['B_Pelvis'].matrix_basis.copy()
    # ease from and back to Standing frame 0
    PAULDRON = float(c.get('pauldron', 0.8))
    T = n / 30.0; bi = float(c.get('blend_in', .12)); bo = float(c.get('blend_out', .25)); out = []
    for i, pz in enumerate(poses):
        t = i / 30.0; w = min(1.0, t / bi if bi > 0 else 1.0, (T - t) / bo if bo > 0 else 1.0); w = max(0.0, w); w = w * w * (3 - 2 * w)
        mix = {}
        for nm, m in pz.items():
            a = ST[nm].to_quaternion(); b = m.to_quaternion()
            if a.dot(b) < 0: b = -b
            q = a.slerp(b, w); M = q.to_matrix().to_4x4(); M.translation = ST[nm].translation.lerp(m.translation, w); mix[nm] = M
        restore(mix); helpers(); out.append(snap())
    name = 'Harrower_' + c['name']
    if name in bpy.data.actions: bpy.data.actions.remove(bpy.data.actions[name])
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_action(act); prev = {}
    for f, pz in enumerate(out):
        for nm, m in pz.items():
            pb = rig.pose.bones[nm]; pb.rotation_mode = 'QUATERNION'; q = m.to_quaternion()
            if nm in prev and q.dot(prev[nm]) < 0: q = -q
            prev[nm] = q; pb.rotation_quaternion = q; pb.location = m.translation; pb.scale = m.to_scale()
            for prop in ('rotation_quaternion', 'location', 'scale'): pb.keyframe_insert(prop, frame=f)
    act.use_frame_range = True; act.frame_start = 0; act.frame_end = n
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    set_action(None)
    report[name] = {'source': c['src'], 'window': [f0, f1], 'seconds': T, 'k': k, 'yaw_deg': math.degrees(yaw), 'ik_miss_m': slide, 'ground_dz_m': [round(float(dz.min()), 3), round(float(dz.max()), 3)],
                    'clamped_from_deg': clamped, 'clearance': {k_: c[k_] for k_ in ('abduct_deg', 'wrist_max', 'twist_max', 'spine_bend_max', 'leg_gap', 'pauldron') if k_ in c}}
    print('CAND', name, json.dumps(report[name]), flush=True)
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(out_blend).resolve()))
(P / 'review/cand_fit.json').write_text(json.dumps(report, indent=2) + '\n')
