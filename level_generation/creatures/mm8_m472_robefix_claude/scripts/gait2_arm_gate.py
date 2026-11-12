"""gait2 (2026-10-21) arm and hand gate (playbook "Arm and hand gate" item 5) on locomotion actions, per half frame:
wrist swing (hand against forearm, swing part, deg; pass <= 60), forearm twist (hand roll about the forearm, deg;
continuous, <= 90), upper-arm roll change between cycles' first/last keys (loop seam, deg), hand-in-torso contacts
(hand/finger vertices inside the trunk capsule pelvis->neck of radius 0.10 m, a conservative closed-body stand-in),
G5 hand edge stretch (max posed/rest, pass <= ~4.5), and the largest per-half-frame rotation step of the hands.
Args: -- <blend> <action> [...]"""
import bpy, sys, math, json
import numpy as np
from mathutils import Vector, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
names = {g.index: g.name for g in body.vertex_groups}
rest = np.array([tuple(v.co) for v in me.vertices])
hw = np.array([sum(e.weight for e in v.groups if 'Hand' in names[e.group] or 'Finger' in names[e.group]) for v in me.vertices])
hand = hw > .5
E = np.array([tuple(e.vertices) for e in me.edges]); E = E[(hw[E[:, 0]] > .3) & (hw[E[:, 1]] > .3)]
rl = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)


def swing_twist(q, axis):
    v = Vector((q.x, q.y, q.z)); p = axis * v.dot(axis); tw = Quaternion((q.w, p.x, p.y, p.z)).normalized()
    sw = q @ tw.inverted(); return math.degrees(2 * math.acos(min(1, abs(sw.w)))), math.degrees(2 * math.atan2(v.dot(axis), q.w))


report = {}
for name in a[1:]:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots: rig.animation_data.action_slot = act.slots[0]
    r = {'wrist_swing_max_deg': 0., 'forearm_twist_max_deg': 0., 'forearm_twist_step_max_deg': 0., 'hand_in_trunk_max': 0,
         'hand_stretch_max': 0., 'hand_step_max_deg': 0., 'upper_arm_seam_deg': 0.}
    prev = {}; f = 0.
    while f <= act.frame_range[1] + 1e-6:
        sc.frame_set(int(f), subframe=f - int(f))
        for s in 'LR':
            fb, hb = rig.data.bones[f'B_{s}_Forearm'], rig.data.bones[f'B_{s}_Hand']
            seg = (fb.matrix_local.inverted() @ hb.head_local).normalized()
            rel = (rig.pose.bones[f'B_{s}_Forearm'].matrix.inverted() @ rig.pose.bones[f'B_{s}_Hand'].matrix).to_quaternion()
            dq = rel @ (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion().inverted()
            sw, tw = swing_twist(dq, seg)
            tw = (tw + 180) % 360 - 180
            r['wrist_swing_max_deg'] = max(r['wrist_swing_max_deg'], sw); r['forearm_twist_max_deg'] = max(r['forearm_twist_max_deg'], abs(tw))
            if ('tw', s) in prev: r['forearm_twist_step_max_deg'] = max(r['forearm_twist_step_max_deg'], abs(tw - prev['tw', s]))
            prev['tw', s] = tw
            q = rig.pose.bones[f'B_{s}_Hand'].matrix.to_quaternion()
            if ('q', s) in prev: r['hand_step_max_deg'] = max(r['hand_step_max_deg'], math.degrees(2 * math.acos(min(1, abs(q.dot(prev['q', s]))))))
            prev['q', s] = q
        if f == int(f):
            ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh(); P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
            A = np.array(rig.pose.bones['B_Pelvis'].head); B = np.array(rig.pose.bones['B_Neck'].head); ab = B - A
            t = np.clip((P[hand] - A) @ ab / (ab @ ab), 0, 1); d = np.linalg.norm(P[hand] - (A + t[:, None] * ab), axis=1)
            r['hand_in_trunk_max'] = max(r['hand_in_trunk_max'], int((d < .10).sum()))
            r['hand_stretch_max'] = max(r['hand_stretch_max'], float((np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / rl).max()))
        f += .5
    seam = []
    for s in 'LR':
        sc.frame_set(0); q0 = rig.pose.bones[f'B_{s}_UpperArm'].matrix.to_quaternion()
        sc.frame_set(int(act.frame_range[1])); q1 = rig.pose.bones[f'B_{s}_UpperArm'].matrix.to_quaternion()
        seam.append(math.degrees(2 * math.acos(min(1, abs(q0.dot(q1))))))
    r['upper_arm_seam_deg'] = max(seam)
    r = {k: round(v, 2) if isinstance(v, float) else v for k, v in r.items()}
    r['pass'] = r['wrist_swing_max_deg'] <= 60 and r['forearm_twist_max_deg'] <= 90 and r['hand_in_trunk_max'] == 0 and r['hand_stretch_max'] <= 4.5
    report[name] = r; print('ARM_GATE', name, json.dumps(r), flush=True)
