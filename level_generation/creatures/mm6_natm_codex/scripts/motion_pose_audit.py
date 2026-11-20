"""48 Hz arm, signed palm, full sole plane, locomotion and two-hand attachment audit."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/material_master.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];FPS=sc.render.fps
names={g.index:g.name for g in body.vertex_groups};rest={};soles={};hand={s:json.loads((P/'work/grip_pose.json').read_text()) for s in 'LR'};HF=json.loads((P/'work/hand_frames.json').read_text())
for sd in 'LR':
 a,b,c=[rig.data.bones[f'B_{sd}_{n}']for n in ['UpperArm','Forearm','Hand']];u=(b.head_local-a.head_local).normalized();v=(c.head_local-b.head_local).normalized()
 rest[sd]={'hinge':Vector((0,0,-1)),'upper_axis':a.matrix_local.to_3x3().inverted()@u,'fore_axis':b.matrix_local.to_3x3().inverted()@v,'rel':a.matrix_local.to_3x3().inverted()@b.matrix_local.to_3x3(),'palm':Vector(HF[sd]['palm'])}
 ids=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if names[g.group].startswith((f'B_{sd}_Foot',f'B_{sd}_Toe')))>.5];z=min(body.data.vertices[i].co.z for i in ids);ids=[i for i in ids if body.data.vertices[i].co.z<z+.006];ys=[body.data.vertices[i].co.y for i in ids];lo,hi=min(ys),max(ys)
 soles[sd]={'all':ids,'heel':[i for i in ids if body.data.vertices[i].co.y>hi-(hi-lo)*.25],'toe':[i for i in ids if body.data.vertices[i].co.y<lo+(hi-lo)*.25]}
def twist(q,axis):return math.degrees((2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi)
report={}
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows={sd:[]for sd in 'LR'};grips=[]
 for f in np.arange(0,act.frame_range[1]+.001,FPS/48):
  sc.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();hm={s:rig.matrix_world@rig.pose.bones[f'B_{s}_Hand'].matrix for s in 'LR'};gc={s:hm[s]@Vector(hand[s]['handle_centre_hand_local'])for s in 'LR'};ga={s:(hm[s].to_3x3()@Vector(hand[s]['handle_axis_hand_local'])).normalized()for s in 'LR'}
  for sd in 'LR':
   a,b,c=[rig.pose.bones[f'B_{sd}_{n}']for n in ['UpperArm','Forearm','Hand']];u=(b.head-a.head).normalized();v=(c.head-b.head).normalized();n=(a.matrix.to_3x3()@rest[sd]['hinge']).normalized();flex=math.degrees(math.atan2(u.cross(v).dot(n),u.dot(v)));plane=math.degrees(math.asin(min(1,abs(v.dot(n)))));base=a.matrix.to_3x3()@rest[sd]['rel'];base=(base@rest[sd]['fore_axis']).rotation_difference(v).to_matrix()@base;fore=abs(twist((base.inverted()@b.matrix.to_3x3()).to_quaternion(),rest[sd]['fore_axis']));upper=twist(a.rotation_quaternion,rest[sd]['upper_axis']);helper=rig.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion.angle;helper=min(helper,math.tau-helper)
   pts=np.array([tuple(body.matrix_world@me.vertices[i].co)for i in soles[sd]['all']]);sn=Vector(np.linalg.svd(pts-pts.mean(0))[2][-1]);tilt=math.degrees(math.acos(min(1,abs(sn.z))));height={k:min((body.matrix_world@me.vertices[i].co).z for i in ids)for k,ids in soles[sd].items()};pn=(hm[sd].to_3x3()@rest[sd]['palm']).normalized();thigh=rig.matrix_world@rig.pose.bones[f'B_{sd}_Thigh'].head;bodydir=thigh-hm[sd].translation;bodydir.z=0
   kn=sum((rig.matrix_world@rig.pose.bones[f'B_{sd}_Finger{i}'].head for i in range(1,5)),Vector())/4;rad=gc[sd]-kn;rad-=ga[sd]*rad.dot(ga[sd]);palm_shaft=pn.dot(rad.normalized());h,k,ank=[rig.pose.bones[f'B_{sd}_{n}'].head for n in ['Thigh','Calf','Foot']];knee=math.degrees((k-h).angle(ank-k))
   rows[sd].append({'seconds':float(f/FPS),'flex':flex,'plane':plane,'fore':fore,'upper':upper,'helper':math.degrees(helper),'heel':height['heel'],'toe':height['toe'],'sole_min':float(pts[:,2].min()),'sole_max':float(pts[:,2].max()),'sole_tilt':tilt,'palm_to_body':pn.dot(bodydir.normalized()),'palm_to_shaft':palm_shaft,'knee':knee})
  if False and .3-1e-6<=f/FPS<=1.5+1e-6:
   v=gc['L']-gc['R'];grips.append({'seconds':float(f/FPS),'offaxis_m':(v-ga['R']*v.dot(ga['R'])).length,'span_m':v.dot(ga['R']),'axes_dot':ga['L'].dot(ga['R'])})
  ev.to_mesh_clear()
 row={}
 for sd,data in rows.items():
  peak=max(data,key=lambda x:x['sole_min']);row[sd]={'flex_min_deg':min(v['flex']for v in data),'flex_max_deg':max(v['flex']for v in data),'plane_error_max_deg':max(v['plane']for v in data),'forearm_roll_max_deg':max(v['fore']for v in data),'helper_roll_max_deg':max(v['helper']for v in data),'upper_roll_max_deg':max(abs(v['upper'])for v in data),'upper_roll_range_deg':max(v['upper']for v in data)-min(v['upper']for v in data),'heel_min_m':min(v['heel']for v in data),'heel_max_m':max(v['heel']for v in data),'toe_min_m':min(v['toe']for v in data),'toe_max_m':max(v['toe']for v in data),'heel_toe_max_delta_m':max(abs(v['heel']-v['toe'])for v in data),'sole_tilt_max_deg':max(v['sole_tilt']for v in data),'sole_patch_max_z_m':max(v['sole_max']for v in data),'sole_min_z_m':min(v['sole_min']for v in data),'swing_peak_m':peak['sole_min'],'knee_at_swing_peak_deg':peak['knee'],'palm_to_body_min_dot':min(v['palm_to_body']for v in data),'palm_to_shaft_min_dot':min(v['palm_to_shaft']for v in data)}
 if grips:(P/'review/round2/two_hand_grip.json').write_text(json.dumps({'sample_hz':48,'max_offaxis_m':max(v['offaxis_m']for v in grips),'span_range_m':[min(v['span_m']for v in grips),max(v['span_m']for v in grips)],'min_abs_axes_dot':min(abs(v['axes_dot'])for v in grips),'samples':grips},indent=2))
 report[act.name]=row
 print('POSE',act.name,{sd:{k:round(v,4)for k,v in r.items()}for sd,r in row.items()},flush=True)
(P/'review/motion_pose_audit.json').write_text(json.dumps(report,indent=2))
