"""m504 G6 fix after clip_timing: the two-fisted smash (and the flex fidget) press the huge stone fists 9-12 cm into
each other and, on the downswing, into the head (the flex: onto a thigh). Per frame, each fist (its rest vertices' centre, carried by the hand
bone) is pushed away from the other fist and from the head centre to a contact distance; the push becomes the
smallest upper-arm swing about the shoulder that moves the fist by it (the forearm and hand follow). Swings are
smoothed over time (Gaussian, sigma 2 frames) and written in place.
Contact distances: GAP x (fist radius + fist radius) and GAP x (fist radius + head radius), radii = mean vertex
distance from the rest centres. Args: -- <in blend> <out blend> <action> [...]   (env GAP, default 0.95)"""
import bpy, sys, os, math
import numpy as np
from mathutils import Matrix, Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
GAP = float(os.environ.get('GAP', '0.95'))
TGAP = float(os.environ.get('TGAP', '1.0'))      # thighs: contact only (the fists hang beside them in Standing)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
vg = [g.name for g in body.vertex_groups]
co = np.array([tuple(v.co) for v in body.data.vertices])
def wsum(keys):
    return np.array([sum(e.weight for e in v.groups if vg[e.group] in keys) for v in body.data.vertices])
LOC = {}; RAD = {}
for s in 'LR':
    sel = wsum((f'B_{s}_Hand',)) > 0.5
    c = co[sel].mean(0); RAD[s] = float(np.linalg.norm(co[sel] - c, axis=1).mean())
    LOC[s] = rig.data.bones[f'B_{s}_Hand'].matrix_local.inverted() @ Vector(c)
sel = wsum(('B_Head',)) > 0.5; c = co[sel].mean(0); RAD['H'] = float(np.linalg.norm(co[sel] - c, axis=1).mean())
LOC['H'] = rig.data.bones['B_Head'].matrix_local.inverted() @ Vector(c)
for s_ in 'LR':                                 # thigh: a sphere at the thigh's middle (the flex lowers a fist onto it)
    th, ca = rig.data.bones[f'B_{s_}_Thigh'].head_local, rig.data.bones[f'B_{s_}_Calf'].head_local
    mid = (th + ca) / 2; sel = (wsum((f'B_{s_}_Thigh',)) > 0.5) & (np.abs(co[:, 2] - mid.z) < 0.08)
    RAD['T' + s_] = float(np.linalg.norm(co[sel][:, :2] - np.array(mid[:2]), axis=1).mean())
    LOC['T' + s_] = rig.data.bones[f'B_{s_}_Thigh'].matrix_local.inverted() @ mid
print('FISTCLEAR radii cm', {k: round(100 * v, 1) for k, v in RAD.items()})
def P(b, loc):
    return rig.matrix_world @ rig.pose.bones[b].matrix @ loc
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
    n = int(act.frame_range[1]) + 1
    rot = {s: [] for s in 'LR'}; worst = 0.0
    for f in range(n):
        sc.frame_set(f)
        F = {s: P(f'B_{s}_Hand', LOC[s]) for s in 'LR'}; H = P('B_Head', LOC['H'])
        for s, o in (('L', 'R'), ('R', 'L')):
            push = Vector()
            d = F[s] - F[o]; need = GAP * (RAD[s] + RAD[o]) - d.length
            if need > 0: push += d.normalized() * need / 2
            d = F[s] - H; need = GAP * (RAD[s] + RAD['H']) - d.length
            if need > 0: push += d.normalized() * need
            for t_ in 'LR':
                T = P(f'B_{t_}_Thigh', LOC['T' + t_]); d = F[s] - T; need = TGAP * (RAD[s] + RAD['T' + t_]) - d.length
                if need > 0: push += d.normalized() * need
            worst = max(worst, push.length)
            sh = rig.matrix_world @ rig.pose.bones[f'B_{s}_UpperArm'].head
            r0 = F[s] - sh; r1 = r0 + push
            rot[s].append(np.array(list(r0.rotation_difference(r1).to_axis_angle()[0] * r0.rotation_difference(r1).angle)))
    k = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2); k /= k.sum()
    for s in 'LR':
        R = np.array(rot[s]); pad = np.concatenate([np.repeat(R[:1], 6, 0), R, np.repeat(R[-1:], 6, 0)])
        R = np.array([(pad[i:i + 13] * k[:, None]).sum(0) for i in range(n)])
        # keep the strongest push (smoothing halves short peaks)
        rot[s] = R * np.clip(np.linalg.norm(np.array(rot[s]), axis=1).max() / max(np.linalg.norm(R, axis=1).max(), 1e-9), 1, 1.6)
    for f in range(n):
        sc.frame_set(f)
        for s in 'LR':
            v = Vector(rot[s][f]); ang = v.length
            if ang < 1e-5: continue
            pb = rig.pose.bones[f'B_{s}_UpperArm']; M = rig.matrix_world @ pb.matrix; t = M.translation.copy()
            M = Matrix.Rotation(ang, 4, v.normalized()) @ M; M.translation = t
            pb.rotation_mode = 'QUATERNION'; pb.matrix = rig.matrix_world.inverted() @ M
            bpy.context.view_layer.update(); pb.keyframe_insert('rotation_quaternion', frame=f)
    print(f'FISTCLEAR {an}: largest fist push {100 * worst:.1f} cm, peak swing L {math.degrees(np.linalg.norm(rot["L"], axis=1).max()):.0f} R {math.degrees(np.linalg.norm(rot["R"], axis=1).max()):.0f} deg')
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
