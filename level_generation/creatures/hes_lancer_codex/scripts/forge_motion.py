"""Fit the local two-handed hammer motions to the shared Kreegan hands and the fitted run."""
import json
import math
import os
from pathlib import Path
import runpy
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import armik

source = str(P.parents[2] / 'anim_library/humanoid_set/2Hand Axe.glb')
arguments = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
attack_only = bool(arguments)
only_role = arguments[0] if arguments and arguments[0] in ('Standing', 'Walking', 'Running', 'Hit', 'Fidget') else 'Attack'
attack_clip = arguments[0] if arguments and arguments[0].startswith('2Hand') else '2HandAxeAttack1'
source_roles = {'Standing': '2HandAxeIdle', 'Walking': '2HandAxeWalk', 'Running': '2HandAxeIdle',
                'Hit': '2HandAxeGetHitF1', 'Fidget': '2HandAxeIdleAlert1', 'Attack': attack_clip}
sources = [(source_roles[only_role], only_role)] if attack_only else [
    ('2HandAxeIdle', 'Standing'), ('2HandAxeWalk', 'Walking'),
    (attack_clip, 'Attack'), ('2HandAxeGetHitF1', 'Hit'), ('2HandAxeIdleAlert1', 'Fidget')]
sys.argv = [__file__, '--', str(P / ('work/forge_motion.blend' if attack_only else 'work/lancer_polished.blend')),
            str(P / 'work/forge_raw.blend'), *[f'{source}:{clip}:Forge_{role}' for clip, role in sources]]
runpy.run_path(str(P / 'scripts/retarget.py'), run_name='__main__')
rig = bpy.data.objects['Rig']
body = bpy.data.objects['Body']
body_groups = [g.name for g in body.vertex_groups]
right_hand_indices = [v.index for v in body.data.vertices if sum(e.weight for e in v.groups
                      if body_groups[e.group].startswith('B_R_') and any(t in body_groups[e.group] for t in ('Hand','Finger')))>.25]
assert right_hand_indices
right_hand_points = None
scene = bpy.context.scene
grips = {s: json.loads((P / f'work/grip_pose_{"R" if s == "R" else "L_tun"}.json').read_text()) for s in 'LR'}
source_grips = json.loads((P / 'work/maul_source_grips.json').read_text())
C = {s: Vector(grips[s]['handle_centre_hand_local']) for s in 'LR'}
A = {s: Vector(grips[s]['handle_axis_hand_local']).normalized() for s in 'LR'}
S = {s: Vector(source_grips[s]['axis_hand']).normalized() for s in 'LR'}
leg_names = {b.name for b in rig.pose.bones if any(t in b.name for t in ('Thigh', 'Calf', 'Foot', 'Toe'))}
leg_names.add('B_Pelvis')

def sample(action, frame):
    rig.animation_data_create()
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    scene.frame_set(int(frame), subframe=frame-int(frame))
    return {b.name: b.matrix_basis.copy() for b in rig.pose.bones}

def restore(pose):
    rig.animation_data.action = None
    for n, mat in pose.items():
        rig.pose.bones[n].matrix_basis = mat
    bpy.context.view_layer.update()

def key_action(name, poses):
    if name in bpy.data.actions:
        bpy.data.actions.remove(bpy.data.actions[name])
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    rig.animation_data.action = act
    previous = {}
    for f, pose in enumerate(poses):
        for n, mat in pose.items():
            bone = rig.pose.bones[n]
            bone.rotation_mode = 'QUATERNION'
            q = mat.to_quaternion()
            if n in previous and q.dot(previous[n]) < 0:
                q = -q
            previous[n] = q.copy()
            bone.rotation_quaternion = q
            bone.location = mat.translation
            bone.keyframe_insert('rotation_quaternion', frame=f)
            bone.keyframe_insert('location', frame=f)
    act.use_frame_range = True
    act.frame_start, act.frame_end = 0, len(poses)-1
    rig.animation_data.action = None

def fit_hand(side, centre, axis, prior):
    names = [f'B_{side}_{part}' for part in ('UpperArm', 'Forearm', 'Hand')]
    reference = previous_arms[side] or {n: rig.pose.bones[n].matrix_basis.copy() for n in names}
    for n,mat in reference.items():
        rig.pose.bones[n].matrix_basis=mat
    bpy.context.view_layer.update()
    shoulder = armik.W(rig, names[0]).translation.copy()
    elbow = armik.W(rig, names[1]).translation.copy()
    best = None
    def cost_of(swing, twist, error, angle):
        upper = rig.data.bones[names[0]]
        segment = (upper.matrix_local.inverted() @ rig.data.bones[names[1]].head_local).normalized()
        _, roll = armik.split_swing_twist(rig.pose.bones[names[0]].matrix_basis.to_quaternion(), segment)
        cost = swing+.2*abs(twist)+1500*error+.15*abs(angle)+1.5*abs(math.degrees(roll))
        limit = 155 if role == 'Running' else 170
        cost += 10000*max(0, swing-55) + 10000*max(0, abs(twist)-limit)
        # Expanded chest envelope, measured from the bulked master; elbows must pass outside the shell.
        pelvis = armik.W(rig, 'B_Pelvis').translation
        chest = Vector((pelvis.x, pelvis.y-.12, pelvis.z+.21))
        elbow_now = armik.W(rig, names[1]).translation
        wrist_now = armik.W(rig, names[2]).translation
        for point in (elbow_now, elbow_now.lerp(wrist_now, .5)):
            relative = point-chest
            distance = math.sqrt((relative.x/.34)**2+(relative.y/.38)**2+(relative.z/.37)**2)
            cost += 20000*max(0, 1-distance)**2
        if side == 'L' and right_hand_points is not None:
            for start,end,radius in ((shoulder,elbow_now,.085),(elbow_now,wrist_now,.085)):
                a,b = np.array(start),np.array(end)
                segment = b-a
                fraction = np.clip((right_hand_points-a) @ segment / segment.dot(segment),0,1)
                clearance = float(np.linalg.norm(right_hand_points-a-fraction[:,None]*segment,axis=1).min())-radius
                cost += 160000*max(0,.008-clearance)
        if previous_twist[side] is not None:
            cost += 10000*max(0,abs(twist-previous_twist[side])-50)
        if previous_arms[side]:
            for n in names:
                delta = previous_arms[side][n].to_quaternion().rotation_difference(rig.pose.bones[n].matrix_basis.to_quaternion()).angle
                degrees = math.degrees(min(delta, 2*math.pi-delta))
                cost += .3*degrees*degrees
        return cost
    for angle in range(-180, 181, 15):
        for n, mat in reference.items():
            rig.pose.bones[n].matrix_basis = mat
        bpy.context.view_layer.update()
        for _ in range(2):
            rotation, roll, _, _ = armik.hand_for_axis(rig, side, A[side], axis, prev_roll=None, step=10)
            wrist = centre-rotation @ C[side]
            pole = shoulder+Quaternion((wrist-shoulder).normalized(), math.radians(angle)) @ (elbow-shoulder)
            armik.solve(rig, side, wrist, pole=pole, hand_rot=rotation)
        swing, twist = armik.wrist_cost(rig, side, rotation)
        error = (armik.W(rig, names[2]) @ C[side]-centre).length
        cost = cost_of(swing, twist, error, angle)
        if best is None or cost < best[0]:
            best = (cost, {n: rig.pose.bones[n].matrix_basis.copy() for n in names}, roll, error, swing)
    if best[4] > 55 or best[0] > 10000 or previous_arms[side] is None:
        for angle in range(-180, 181, 30):
            for roll in range(0, 360, 15):
                for n, mat in reference.items():
                    rig.pose.bones[n].matrix_basis = mat
                bpy.context.view_layer.update()
                rotation = armik.hand_rot(A[side], axis, roll)
                wrist = centre-rotation @ C[side]
                pole = shoulder+Quaternion((wrist-shoulder).normalized(), math.radians(angle)) @ (elbow-shoulder)
                armik.solve(rig, side, wrist, pole=pole, hand_rot=rotation)
                swing, twist = armik.wrist_cost(rig, side, rotation)
                error = (armik.W(rig, names[2]) @ C[side]-centre).length
                cost = cost_of(swing, twist, error, angle)
                if cost < best[0]:
                    best = (cost, {n: rig.pose.bones[n].matrix_basis.copy() for n in names}, None, error, swing)
    for n, mat in best[1].items():
        rig.pose.bones[n].matrix_basis = mat
    bpy.context.view_layer.update()
    return best

# Keep the fitted demon torso and locomotion; the library supplies the arms and maul stroke.
report = json.loads((P / 'review/forge_grips.json').read_text()) if attack_only else {}
roles = {'Standing': 'Carbine_Standing', 'Walking': 'Carbine_Walking', 'Running': 'Lancer_Running',
         'Attack': 'Carbine_Standing', 'Hit': 'Carbine_Standing', 'Fidget': 'Carbine_Standing'}
if attack_only:
    roles = {only_role: roles[only_role]}
raw_sources = {role: bpy.data.actions['Forge_Standing' if role == 'Running' and not attack_only else f'Forge_{role}'].copy()
               for role in roles}
for role, lower_name in roles.items():
    raw = raw_sources[role]
    lower = bpy.data.actions[lower_name]
    duration = int(lower.frame_range[1] if role == 'Running' else raw.frame_range[1])
    poses = []
    errors = []
    prior_roll = {'L': None, 'R': None}
    previous_arms = {'L': None, 'R': None}
    previous_twist = {'L': None, 'R': None}
    ready = sample(raw, 0)
    for f in range(duration+1):
        upper = sample(raw, f/duration*raw.frame_range[1])
        source_axis = (armik.W(rig,'B_R_Hand').to_3x3().normalized() @ S['R']).normalized()
        source_centre = armik.W(rig,'B_R_Hand') @ C['R']
        if role in ('Attack', 'Hit', 'Fidget'):
            for n in upper:
                if any(n == f'B_{s}_{part}' for s in 'LR' for part in ('Clavicle', 'UpperArm', 'Forearm', 'Hand')):
                    amplitude = .60 if role == 'Attack' else .65
                    upper[n] = ready[n].to_quaternion().slerp(upper[n].to_quaternion(), amplitude).to_matrix().to_4x4()
                    upper[n].translation = ready[n].translation
        lower_pose = sample(lower, f/duration*lower.frame_range[1])
        arm_names = {f'B_{s}_{part}' for s in 'LR' for part in ('Clavicle', 'UpperArm', 'Forearm', 'Hand')}
        if role == 'Attack':
            for n in ('B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'):
                change=ready[n].to_quaternion().inverted() @ upper[n].to_quaternion()
                q=lower_pose[n].to_quaternion() @ Quaternion().slerp(change,.85)
                matrix=q.to_matrix().to_4x4(); matrix.translation=lower_pose[n].translation
                lower_pose[n]=matrix
        restore({n: upper[n] if n in arm_names else lower_pose[n] for n in upper})
        for side in 'LR':
            for n, q in grips[side]['finger_local'].items():
                rig.pose.bones[n].rotation_mode = 'QUATERNION'
                rig.pose.bones[n].rotation_quaternion = Quaternion(q)
        bpy.context.view_layer.update()
        right = armik.W(rig, 'B_R_Hand').copy()
        axis = (right.to_3x3().normalized() @ S['R']).normalized()
        if role == 'Attack':
            axis = source_axis
        centre = source_centre.copy() if role == 'Attack' else right @ C['R']
        if role == 'Attack':
            centre.z = max(.75,centre.z)
            centre.y = max(-.95,centre.y)
        # The source has a narrow human chest; the demon's fitted fists must clear its broad shell.
        centre.y = min(centre.y, -.61)
        left = armik.W(rig, 'B_L_Hand')
        along = min(.62, max(.28, (left @ C['L']-centre).dot(axis)))
        results = {}
        for iteration in range(3):
            # Project the shared haft into the reach of both arms, instead of letting either fist float.
            for side in 'RL':
                offset = axis*along if side == 'L' else Vector()
                rotation, _, _, _ = armik.hand_for_axis(rig, side, A[side], axis if side == 'R' else -axis,
                                                       prev_roll=prior_roll[side], step=10)
                sh = armik.W(rig, f'B_{side}_UpperArm').translation
                el = armik.W(rig, f'B_{side}_Forearm').translation
                wr = armik.W(rig, f'B_{side}_Hand').translation
                radius = .93*((el-sh).length+(wr-el).length)
                anchor = sh+rotation @ C[side]-offset
                delta = centre-anchor
                if delta.length > radius:
                    centre = anchor+delta.normalized()*radius
            for side in 'RL':
                target = centre+(axis*along if side == 'L' else Vector())
                if side == 'L':
                    evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
                    mesh = evaluated.to_mesh()
                    right_hand_points = np.unique(np.array([body.matrix_world @ mesh.vertices[i].co for i in right_hand_indices]),axis=0)
                    evaluated.to_mesh_clear()
                results[side] = fit_hand(side, target, axis if side == 'R' else -axis, prior_roll[side])
        prior_roll = {s: results[s][2] for s in 'LR'}
        previous_arms = {s: results[s][1] for s in 'LR'}
        previous_twist = {s: armik.wrist_cost(rig,s,armik.W(rig,f'B_{s}_Hand').to_3x3().normalized())[1] for s in 'LR'}
        errors.append({'frame': f, 'left_grip_residual_m': results['L'][3],
                       'right_grip_residual_m': results['R'][3], 'left_wrist_deg': results['L'][4],
                       'right_wrist_deg': results['R'][4], 'spacing_m': along})
        poses.append({b.name: b.matrix_basis.copy() for b in rig.pose.bones})
        if f%10==0: print('FIT_FRAME',role,f,round(results['L'][4],1),round(results['R'][4],1),flush=True)
    if role in ('Standing', 'Walking', 'Running'):
        poses[-1] = poses[0]
    key_action(f'Forge_{role}', poses)
    if role == 'Attack':
        z = Vector((0,1,0)); z = (z-A['R']*z.dot(A['R'])).normalized()
        point = C['R']+A['R']*1.02+A['R'].cross(z).normalized()*.335
        trajectory=[]
        for frame in range(duration+1):
            sample(bpy.data.actions['Forge_Attack'],frame)
            position=armik.W(rig,'B_R_Hand') @ point
            trajectory.append({'time':frame/30,'impact_socket_y_up':[position.x,position.z,-position.y]})
        (P/'review/maul_strike_trajectory.json').write_text(json.dumps(trajectory,indent=2)+'\n')
    report[role] = errors
    print('FORGE_GRIP', role, max(e['left_grip_residual_m'] for e in errors),
          max(e['left_wrist_deg'] for e in errors), max(e['right_wrist_deg'] for e in errors), flush=True)

for role, source_name in ([] if attack_only else [('Death', 'Carbine_Death'), ('Dead', 'Carbine_Dead'),
                                                ('Cast', 'Demon_Cast_FireBolt')]):
    source_action = bpy.data.actions[source_name]
    poses = []
    held = sample(bpy.data.actions['Forge_Standing'], 0)
    for f in range(int(source_action.frame_range[1])+1):
        pose = sample(source_action, f)
        if role == 'Cast':
            pose.update({n: mat for n, mat in held.items() if n in leg_names or n.startswith('B_R_') or
                         n in ('Bone_020','Bone_019','Bone_018','Bone_017','Bone_016','Bone_015')})
        restore(pose)
        for n, q in grips['R']['finger_local'].items():
            rig.pose.bones[n].rotation_quaternion = Quaternion(q)
        poses.append({b.name: b.matrix_basis.copy() for b in rig.pose.bones})
    key_action(f'Forge_{role}', poses)
for action in raw_sources.values():
    bpy.data.actions.remove(action)

(P / 'review/forge_grips.json').write_text(json.dumps(report, indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/forge_motion.blend'))
