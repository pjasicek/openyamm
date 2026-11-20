"""Check actual skinned attack: point-led contact, grip, fixed arm lengths and wrist anatomy."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'))
r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions['Attack'];sc=bpy.context.scene
G=json.loads((P/'work/grip_pose.json').read_text());rows=[]
R={b.name:b.matrix_local for b in r.data.bones}
for f in range(193):
 frame=1+f*.5;sc.frame_set(int(frame),subframe=frame%1)
 m={n:b.matrix for n,b in r.pose.bones.items()}
 U,F,H=[m['B_R_'+n] for n in ['UpperArm','Forearm','Hand']]
 neutral=F.to_3x3()@R['B_R_Forearm'].to_3x3().transposed()@R['B_R_Hand'].to_3x3()
 q=(neutral.transposed()@H.to_3x3()).to_quaternion();tw=Quaternion((q.w,0,q.y,0));tw.normalize();sw=q@tw.inverted();swing=math.degrees(min(sw.angle,2*math.pi-sw.angle));twist=math.degrees((2*math.atan2(q.y,q.w)+math.pi)%(2*math.pi)-math.pi)
 tm=m['Trident'];axis=(tm.to_3x3()@Vector((0,1,0))).normalized();palm=H@Vector(G['handle_centre_hand_local']);tip=tm@Vector((0,1.62,0))
 length_error=max(abs((F.translation-U.translation).length-(R['B_R_Forearm'].translation-R['B_R_UpperArm'].translation).length),abs((H.translation-F.translation).length-(R['B_R_Hand'].translation-R['B_R_Forearm'].translation).length))
 rows.append({'time':f/120,'tip':list(tip),'shaft_axis':list(axis),'grip_error':(palm-tm.translation).length,'arm_length_error':length_error,'wrist_swing':swing,'wrist_twist':twist})
aim=Vector((.025,-.985,-.17)).normalized();strike=[v for v in rows if .70<=v['time']<=1.02]
vectors=[Vector(b['tip'])-Vector(a['tip']) for a,b in zip(strike,strike[1:])]
cosines=[v.normalized().dot(aim) for v in vectors if v.length>.0005]
displacement=Vector(strike[-1]['tip'])-Vector(strike[0]['tip'])
report={'duration':1.6,'impact':1.02,'tip_forward_drive_m':displacement.dot(aim),'min_drive_direction_cosine':min(cosines),'max_shaft_aim_error_deg':max(math.degrees(aim.angle(Vector(v['shaft_axis']))) for v in strike),'max_grip_error_m':max(v['grip_error'] for v in rows),'max_arm_length_error_m':max(v['arm_length_error'] for v in rows),'max_wrist_swing_deg':max(v['wrist_swing'] for v in rows),'max_wrist_twist_deg':max(abs(v['wrist_twist']) for v in rows),'samples':rows}
(P/'review/attack_thrust_v3/mechanics.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='samples'})
assert report['tip_forward_drive_m']>.5
assert report['min_drive_direction_cosine']>.85
assert report['max_shaft_aim_error_deg']<1
assert report['max_grip_error_m']<.0001 and report['max_arm_length_error_m']<.0001
assert report['max_wrist_swing_deg']<60 and report['max_wrist_twist_deg']<60
