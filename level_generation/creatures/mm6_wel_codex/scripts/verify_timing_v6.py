"""Measure the delivered low thrust, including both arms and torso contribution."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene;R={b.name:b.matrix_local for b in r.data.bones}
G=json.loads((P/'work/grip_pose.json').read_text());r.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.context.view_layer.update()
base={n:p.rotation_quaternion.copy() for n,p in r.pose.bones.items()};r.animation_data.action=bpy.data.actions['Attack'];rows=[]
for f in range(159):
 frame=1+f*.5;sc.frame_set(int(frame),subframe=frame%1);m={n:b.matrix for n,b in r.pose.bones.items()}
 U,F,H=[m['B_R_'+n] for n in ['UpperArm','Forearm','Hand']]
 neutral=F.to_3x3()@R['B_R_Forearm'].to_3x3().transposed()@R['B_R_Hand'].to_3x3()
 q=(neutral.transposed()@H.to_3x3()).to_quaternion();tw=Quaternion((q.w,0,q.y,0));tw.normalize();sw=q@tw.inverted();swing=math.degrees(min(sw.angle,2*math.pi-sw.angle));twist=math.degrees((2*math.atan2(q.y,q.w)+math.pi)%(2*math.pi)-math.pi)
 delta=base['B_R_Forearm'].inverted()@r.pose.bones['B_R_Forearm'].rotation_quaternion;ft=math.degrees((2*math.atan2(delta.y,delta.w)+math.pi)%(2*math.pi)-math.pi)
 hand_delta=base['B_R_Hand'].rotation_difference(r.pose.bones['B_R_Hand'].rotation_quaternion).angle;hand_delta=min(hand_delta,2*math.pi-hand_delta)
 tm=m['Trident'];axis=(tm.to_3x3()@Vector((0,1,0))).normalized();palm=H@Vector(G['handle_centre_hand_local']);tip=tm@Vector((0,1.62,0))
 length_error=max(abs((m[f'B_{side}_{b}'].translation-m[f'B_{side}_{a}'].translation).length-(R[f'B_{side}_{b}'].translation-R[f'B_{side}_{a}'].translation).length) for side in ['R','L'] for a,b in [('UpperArm','Forearm'),('Forearm','Hand')])
 rows.append({'time':f/120,'tip':list(tip),'shaft_axis':list(axis),'right_grip':list(palm),'left_wrist':list(m['B_L_Hand'].translation),'head':list(m['B_Head'].translation),'pelvis':list(m['B_Pelvis'].translation),'tail_mid':list(m['Serpent_05'].translation),'fluke':list(m['Serpent_28'].translation),'grip_error':(palm-tm.translation).length,'arm_length_error':length_error,'wrist_swing':swing,'wrist_twist':twist,'wrist_change_from_ready':math.degrees(hand_delta),'forearm_local_axial_change':ft})
strike=[v for v in rows if 32/60<=v['time']<=44/60];cosines=[]
for a,b in zip(strike,strike[1:]):
 v=Vector(b['tip'])-Vector(a['tip'])
 if v.length>.0005:cosines.append(v.normalized().dot(Vector(b['shaft_axis'])))
start=rows[0];wind=rows[64];hit=rows[88];drive=Vector(hit['right_grip'])-Vector(wind['right_grip']);tipdrive=Vector(hit['tip'])-Vector(wind['tip'])
report={'duration':79/60,'impact':44/60,'grip_windup_delta_m':list(Vector(wind['right_grip'])-Vector(start['right_grip'])),'grip_release_delta_m':list(drive),'tip_release_delta_m':list(tipdrive),'min_drive_direction_cosine':min(cosines),'max_grip_error_m':max(v['grip_error'] for v in rows),'max_arm_length_error_m':max(v['arm_length_error'] for v in rows),'max_wrist_swing_deg':max(v['wrist_swing'] for v in rows),'max_wrist_twist_deg':max(abs(v['wrist_twist']) for v in rows),'max_wrist_change_from_ready_deg':max(v['wrist_change_from_ready'] for v in rows),'max_forearm_local_axial_change_deg':max(abs(v['forearm_local_axial_change']) for v in rows),'left_wrist_windup':wind['left_wrist'],'left_wrist_impact':hit['left_wrist'],'head_windup':wind['head'],'head_impact':hit['head'],'tip_impact':hit['tip'],'pelvis_windup':wind['pelvis'],'pelvis_impact':hit['pelvis'],'tail_mid_windup':wind['tail_mid'],'tail_mid_impact':hit['tail_mid'],'fluke_windup':wind['fluke'],'fluke_impact':hit['fluke'],'samples':rows}
(P/'review/attack_timing_v6/mechanics.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='samples'})
assert report['grip_windup_delta_m'][1]>.08 and report['grip_windup_delta_m'][2]<-.01
assert drive.x>.1 and drive.y<-.3 and drive.z>.12
assert tipdrive.y<-.3 and tipdrive.z>0
assert min(cosines)>.75
assert report['max_grip_error_m']<.0001 and report['max_arm_length_error_m']<.0001
assert report['max_wrist_change_from_ready_deg']<19
assert report['max_forearm_local_axial_change_deg']<60
assert wind['left_wrist'][0]<.12 and hit['left_wrist'][0]>.4

assert -.13 < hit['tip'][0] < .05 and hit['tip'][1] < -1.97, 'Aim inward to the right-pectoral line and farther forward'
assert hit['pelvis'][1] < wind['pelvis'][1]-.10, 'Pelvis drives with the attack'
assert (Vector(hit['tail_mid'])-Vector(wind['tail_mid'])).length>.025, 'Visible tail motion accompanies the larger pelvis drive'

# Every frame of the previously frozen interval must now advance into the target.
advances=[(Vector(rows[2*(f+1)]['tip'])-Vector(rows[2*f]['tip'])).dot(Vector(rows[2*f]['shaft_axis'])) for f in range(32,40)]
assert min(advances)>.001, advances
report['release_frames']=12
report['tip_advance_frames_32_40_m']=advances
report['pass']=True
(P/'review/attack_timing_v6/mechanics.json').write_text(json.dumps(report,indent=2))
