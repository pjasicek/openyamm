"""Measure actual reimported mesh motion, staff-tip release, planted feet and posture at 240 Hz."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/runtime_reimport.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];scene=bpy.context.scene
G=json.loads((p/'work/runtime_grip_pose.json').read_text());H=rig.matrix_world@rig.data.bones['B_R_Hand'].matrix_local
C=H@Vector(G['handle_centre_hand_local']);A=(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
staff_rest=[staff.matrix_world@v.co for v in staff.data.vertices];along=np.array([(v-C).dot(A) for v in staff_rest]);ids=np.where(along>along.max()-.006)[0];tip=sum((staff_rest[int(i)] for i in ids),Vector())/len(ids)
B0=rig.matrix_world@rig.data.bones['B_Staff'].matrix_local;inverse=B0.inverted();hemids=[i for i,a in enumerate(body.data.attributes['piece'].data) if a.value==100 and body.data.vertices[i].co.z<.35]
report={};release={};dt=1/240
for role in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']:
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 ts=np.arange(0,act.frame_range[1]/scene.render.fps+1e-6,dt);tipxyz=[];axes=[];feet={s:[] for s in 'LR'};knee={s:[] for s in 'LR'};hands={s:[] for s in 'LR'};staff_angles=[];hems=[];palms=[];sockets=[];floor=[]
 for t in ts:
  f=t*scene.render.fps;scene.frame_set(int(f),subframe=float(f-int(f)))
  D=(rig.matrix_world@rig.pose.bones['B_Staff'].matrix)@inverse;tipxyz.append(list(D@tip));axis=(D.to_3x3()@A).normalized();axes.append(list(axis))
  floor.append(min((D@v).z for v in staff_rest))
  joint=lambda n:rig.matrix_world@rig.pose.bones[n].head
  for s in 'LR':
   feet[s].append(list(joint('B_'+s+'_Foot')));hands[s].append(list(joint('B_'+s+'_Hand')))
   thigh,calf,foot=[joint('B_'+s+'_'+b) for b in ['Thigh','Calf','Foot']];knee[s].append(math.degrees((calf-thigh).angle(foot-calf)))
  staff_angles.append(math.degrees((joint('B_R_Hand')-joint('B_R_Forearm')).angle(axis)))
  palms.append(list(joint('Socket_Palm_Left')));sockets.append(list(joint('Socket_Staff_Head')))
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();hems.append([list(body.matrix_world@me.vertices[i].co) for i in hemids]);ev.to_mesh_clear()
 tipxyz=np.array(tipxyz);axes=np.array(axes);hems=np.array(hems);sockets=np.array(sockets)
 speed=np.linalg.norm(np.gradient(tipxyz,dt,axis=0),axis=1);vforward=-np.gradient(tipxyz,dt,axis=0)[:,1]
 result={'seconds':float(ts[-1]),'sample_fps':240,'staff_tip_excursion_m':float(np.linalg.norm(tipxyz-tipxyz[0],axis=1).max()),'staff_floor_min_mm':min(floor)*1000,'hand_excursion_m':{s:float(np.linalg.norm(np.array(hands[s])-hands[s][0],axis=1).max()) for s in 'LR'},'knee_bend_deg':{s:[min(knee[s]),max(knee[s])] for s in 'LR'},'hem_excursion_p95_mm':float(np.percentile(np.linalg.norm(hems-hems[0],axis=2).max(0),95)*1000),'hem_frame_acceleration_p99_mm':float(np.percentile(np.linalg.norm(np.diff(hems,n=2,axis=0),axis=2),99)*1000),'staff_forearm_angle_deg':[min(staff_angles),max(staff_angles)]}
 if role=='Cast':
  valid=(ts>.50)&(ts<1.1)&(-axes[:,1]>math.cos(math.radians(15)))&(vforward>0)
  assert valid.any();i=int(np.where(valid,speed,-1).argmax())
  release[role]={'release_seconds':round(float(ts[i]),6),'tip_speed_mps':float(speed[i]),'forward_speed_mps':float(vforward[i]),'staff_forward_dot':float(-axes[i,1]),'aim_off_forward_deg':math.degrees(math.acos(float(-axes[i,1]))),'tip_position_m':tipxyz[i].tolist(),'launch_socket':'Socket_Staff_Head','socket_position_m':sockets[i].tolist(),'staff_forearm_angle_deg':staff_angles[i],'criterion':'Maximum actual crown-tip speed while its axis is within 15 degrees of forward and moving toward the target, excluding recovery.'}
  left,right=[np.array(feet[s]) for s in 'LR'];phases=[(0,.22),(.50,1.30),(1.64,2.05)]
  drifts=[float(np.linalg.norm(left[(ts>=a)&(ts<=b)]-left[np.where(ts>=a)[0][0]],axis=1).max()*1000) for a,b in phases]
  result['feet']={'left_step_m':float(left[0,1]-left[:,1].min()),'left_lift_m':float(left[:,2].max()-left[0,2]),'left_plant_drift_mm':drifts,'right_plant_drift_mm':float(np.linalg.norm(right-right[0],axis=1).max()*1000),'simultaneous_airborne_samples':int(((left[:,2]-left[0,2]>.001)&(right[:,2]-right[0,2]>.001)).sum())}
  assert .6<=ts[i]<=.9 and release[role]['staff_forward_dot']>.965 and speed[i]>.5
  assert max(drifts)<.2 and result['feet']['right_plant_drift_mm']<.2 and result['feet']['simultaneous_airborne_samples']==0
 elif role=='Attack':
  velocity=np.gradient(np.array(palms),dt,axis=0);valid=(ts>.6)&(ts<.9);i=int(np.where(valid,-velocity[:,1],-1).argmax());release[role]={'release_seconds':round(float(ts[i]),6),'forward_speed_mps':float(-velocity[i,1]),'launch_socket':'Socket_Palm_Left','criterion':'Peak forward left palm socket speed during release.'};assert -velocity[i,1]>.4
 if role in ['Hit','Fidget']:
  assert result['staff_tip_excursion_m']>.10 and result['hand_excursion_m']['R']>.02
  assert max(max(knee[s])-min(knee[s]) for s in 'LR')>5 and result['hem_excursion_p95_mm']>5
 result['staff_floor_pass']=min(floor)>-.002
 report[role]=result;print('MOTION_METRICS',role,json.dumps(result),flush=True)
(p/'work/round1_motion_metrics.json').write_text(json.dumps(report,indent=2));(p/'work/motion_details.json').write_text(json.dumps(release,indent=2));print('RELEASE',json.dumps(release),flush=True)

assert all(r['staff_floor_pass'] for r in report.values()), 'Staff/floor clearance failed'
