"""Keep the supporting arm clear of the rear hand while keeping its fist on the lance's forward grip."""
import json
import math
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Quaternion, Vector
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P/'scripts'))
import armik
source, output, *clips = sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=source)
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Body']
rig.animation_data_create()
grip = json.loads((P/'work/grip_pose_L_tun.json').read_text())
centre_local, axis_local = Vector(grip['handle_centre_hand_local']), Vector(grip['handle_axis_hand_local']).normalized()
group_names = [g.name for g in body.vertex_groups]
right_indices = [v.index for v in body.data.vertices if sum(e.weight for e in v.groups
                 if group_names[e.group].startswith('B_R_') and any(p in group_names[e.group] for p in ('Hand','Finger'))) > .25]
bones = ['B_L_UpperArm','B_L_Forearm','B_L_Hand']

def capsule_clearance(points, start, end, radius):
    a, b = np.array(start), np.array(end)
    direction = b-a
    fraction = np.clip((points-a)@direction/direction.dot(direction), 0, 1)
    return float(np.linalg.norm(points-a-fraction[:,None]*direction, axis=1).min()-radius)

report = {}
for clip in clips:
    action = bpy.data.actions[clip]
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    keys, prior, records = {}, None, []
    for frame in range(int(action.frame_range[0]), int(action.frame_range[1])+1):
        bpy.context.scene.frame_set(frame)
        reference = {n: rig.pose.bones[n].matrix_basis.copy() for n in bones}
        hand = armik.W(rig, bones[2])
        centre = hand@centre_local
        axis = (hand.to_3x3()@axis_local).normalized()
        shoulder = armik.W(rig,bones[0]).translation.copy()
        elbow = armik.W(rig,bones[1]).translation.copy()
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        points = np.unique(np.array([body.matrix_world@mesh.vertices[i].co for i in right_indices]),axis=0)
        evaluated.to_mesh_clear()
        best = None
        for roll in range(-60,61,15):
            rotation = Quaternion(axis,math.radians(roll)).to_matrix()@hand.to_3x3().normalized()
            wrist = centre-rotation@centre_local
            for angle in range(-120,121,15):
                for n, matrix in reference.items():
                    rig.pose.bones[n].matrix_basis = matrix
                bpy.context.view_layer.update()
                pole = shoulder+Quaternion((wrist-shoulder).normalized(),math.radians(angle))@(elbow-shoulder)
                armik.solve(rig,'L',wrist,pole=pole,hand_rot=rotation)
                elbow_now = armik.W(rig,bones[1]).translation
                wrist_now = armik.W(rig,bones[2]).translation
                clearance = min(capsule_clearance(points,shoulder,elbow_now,.075),
                                capsule_clearance(points,elbow_now,wrist_now,.075))
                swing, twist = armik.wrist_cost(rig,'L',rotation)
                residual = (armik.W(rig,bones[2])@centre_local-centre).length
                cost = 100000*max(0,.008-clearance)+10000*max(0,swing-60)+2000*residual
                cost += swing+.15*abs(twist)+.03*abs(roll)+.03*abs(angle)
                if prior:
                    for n in bones:
                        delta = prior[n].rotation_difference(rig.pose.bones[n].matrix_basis.to_quaternion()).angle
                        cost += .08*math.degrees(min(delta,2*math.pi-delta))**2
                if best is None or cost < best[0]:
                    best = cost, {n:rig.pose.bones[n].matrix_basis.to_quaternion() for n in bones}, clearance, swing, residual
        keys[frame], prior = best[1], best[1]
        records.append({'frame':frame,'clearance_m':best[2],'wrist_deg':best[3],'grip_residual_m':best[4]})
    previous = {}
    for frame, pose in keys.items():
        for n, q in pose.items():
            if n in previous and previous[n].dot(q)<0:
                q=-q
            previous[n]=q.copy()
            bone=rig.pose.bones[n]
            bone.rotation_mode='QUATERNION'
            bone.rotation_quaternion=q
            bone.keyframe_insert('rotation_quaternion',frame=frame)
    report[clip]=records
    print('SUPPORT_CLEAR',clip,min(r['clearance_m'] for r in records),max(r['wrist_deg'] for r in records),flush=True)
(P/'review/support_clearance.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=output)
