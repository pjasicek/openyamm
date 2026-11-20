import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from timing import phase
"""96 Hz arm, signed palm, full sole plane, locomotion and two-hand attachment audit."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_jak1_runtime_lod0.glb'));rig=next(o for o in sc.objects if o.type=='ARMATURE');body=next(o for o in sc.objects if o.type=='MESH' and o.parent is rig and 'Staff' in o.vertex_groups)
names={g.index:g.name for g in body.vertex_groups};rest={};soles={};hand={s:json.loads((P/f'work/grip_pose{suffix}.json').read_text())for s,suffix in [('R',''),('L','_left')]}
for sd in 'LR':
 a,b,c=[rig.data.bones[f'B_{sd}_{n}']for n in ['UpperArm','Forearm','Hand']];u=(b.head_local-a.head_local).normalized();v=(c.head_local-b.head_local).normalized()
 rest[sd]={'hinge':Vector((0,0,-1)),'upper_axis':a.matrix_local.to_3x3().inverted()@u,'fore_axis':b.matrix_local.to_3x3().inverted()@v,'rel':a.matrix_local.to_3x3().inverted()@b.matrix_local.to_3x3(),'palm':Vector(json.loads((P/'work/hand_rest_roll.json').read_text())[sd]['palm_local'])}
 ids=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups if names[g.group].startswith((f'B_{sd}_Foot',f'B_{sd}_Toe')))>.5];z=min(body.data.vertices[i].co.z for i in ids);ids=[i for i in ids if body.data.vertices[i].co.z<z+.006];ys=[body.data.vertices[i].co.y for i in ids];lo,hi=min(ys),max(ys)
 soles[sd]={'all':ids,'heel':[i for i in ids if body.data.vertices[i].co.y>hi-(hi-lo)*.25],'toe':[i for i in ids if body.data.vertices[i].co.y<lo+(hi-lo)*.25]}
def twist(q,axis):return math.degrees((2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi)
report={}
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows={sd:[]for sd in 'LR'};grips=[];grip_reference=None
 for f in np.arange(0,act.frame_range[1]+.001,30/96):
  sc.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();hm={s:rig.matrix_world@rig.pose.bones[f'B_{s}_Hand'].matrix for s in 'LR'};gc={s:hm[s]@Vector(hand[s]['handle_centre_hand_local'])for s in 'LR'};ga={s:(hm[s].to_3x3()@Vector(hand[s]['handle_axis_hand_local'])).normalized()for s in 'LR'}
  for sd in 'LR':
   a,b,c=[rig.pose.bones[f'B_{sd}_{n}']for n in ['UpperArm','Forearm','Hand']];u=(b.head-a.head).normalized();v=(c.head-b.head).normalized();n=(a.matrix.to_3x3()@rest[sd]['hinge']).normalized();flex=math.degrees(math.atan2(u.cross(v).dot(n),u.dot(v)));plane=math.degrees(math.asin(min(1,abs(v.dot(n)))));base=a.matrix.to_3x3()@rest[sd]['rel'];base=(base@rest[sd]['fore_axis']).rotation_difference(v).to_matrix()@base;fore=abs(twist((base.inverted()@b.matrix.to_3x3()).to_quaternion(),rest[sd]['fore_axis']));upper=twist(a.rotation_quaternion,rest[sd]['upper_axis']);helper_matrix=rig.pose.bones[f'B_{sd}_ForearmTwist'].matrix.to_3x3();helper=math.radians(abs(twist((base.inverted()@helper_matrix).to_quaternion(),rest[sd]['fore_axis'])))
   pts=np.array([tuple(body.matrix_world@me.vertices[i].co)for i in soles[sd]['all']]);sn=Vector(np.linalg.svd(pts-pts.mean(0))[2][-1]);tilt=math.degrees(math.acos(min(1,abs(sn.z))));height={k:min((body.matrix_world@me.vertices[i].co).z for i in ids)for k,ids in soles[sd].items()};pn=(hm[sd].to_3x3()@rest[sd]['palm']).normalized();thigh=rig.matrix_world@rig.pose.bones[f'B_{sd}_Thigh'].head;bodydir=thigh-hm[sd].translation;bodydir.z=0
   fd=rig.matrix_world@(rig.pose.bones[f'B_{sd}_Toe0'].head-rig.pose.bones[f'B_{sd}_Foot'].head);yaw=math.degrees(math.atan2(fd.x,-fd.y));kn=sum((rig.matrix_world@rig.pose.bones[f'B_{sd}_Finger{i}'].head for i in range(1,5)),Vector())/4;rad=gc[sd]-kn;rad-=ga[sd]*rad.dot(ga[sd]);held=(sd=='R' and act.name!='Dead' and (act.name!='Death' or f/30<=phase('Death',.25))) or (sd=='L' and act.name=='Attack' and phase('Attack',.4)<=f/30<=phase('Attack',1.2));staff=rig.matrix_world@rig.pose.bones['Staff'].matrix;axis=staff.to_3x3().col[2].normalized();rad=staff.translation-kn;rad-=axis*rad.dot(axis);palm_shaft=pn.dot(rad.normalized()) if held else None;h,k,ank=[rig.pose.bones[f'B_{sd}_{n}'].head for n in ['Thigh','Calf','Foot']];knee=math.degrees((k-h).angle(ank-k))
   rows[sd].append({'seconds':float(f/30),'flex':flex,'plane':plane,'fore':fore,'upper':upper,'helper':math.degrees(helper),'heel':height['heel'],'toe':height['toe'],'sole_min':float(pts[:,2].min()),'sole_max':float(pts[:,2].max()),'sole_tilt':tilt,'palm_to_body':pn.dot(bodydir.normalized()),'palm_to_shaft':palm_shaft,'palm_forward':pn.dot(Vector((0,-1,0))),'knee':knee,'toe_yaw':yaw})
  if act.name=='Attack' and phase('Attack',.4)-1e-6<=f/30<=phase('Attack',1.2)+1e-6:
   relative=(hm['R'].to_quaternion().inverted()@hm['L'].to_quaternion());grip_reference=grip_reference or relative.copy();angle=math.degrees(grip_reference.rotation_difference(relative).angle);angle=min(angle,360-angle)
   v=gc['L']-gc['R'];grips.append({'seconds':float(f/30),'offaxis_m':(v-ga['R']*v.dot(ga['R'])).length,'span_m':v.dot(ga['R']),'axes_dot':ga['L'].dot(ga['R']),'relative_rotation_deg':angle})
  ev.to_mesh_clear()
 row={}
 for sd,data in rows.items():
  peak=max(data,key=lambda x:x['sole_min']);row[sd]={'flex_min_deg':min(v['flex']for v in data),'flex_max_deg':max(v['flex']for v in data),'plane_error_max_deg':max(v['plane']for v in data),'forearm_roll_max_deg':max(v['fore']for v in data),'helper_roll_max_deg':max(v['helper']for v in data),'upper_roll_max_deg':max(abs(v['upper'])for v in data),'upper_roll_range_deg':max(v['upper']for v in data)-min(v['upper']for v in data),'heel_min_m':min(v['heel']for v in data),'heel_max_m':max(v['heel']for v in data),'toe_min_m':min(v['toe']for v in data),'toe_max_m':max(v['toe']for v in data),'heel_toe_max_delta_m':max(abs(v['heel']-v['toe'])for v in data),'sole_tilt_max_deg':max(v['sole_tilt']for v in data),'sole_patch_max_z_m':max(v['sole_max']for v in data),'sole_min_z_m':min(v['sole_min']for v in data),'swing_peak_m':peak['sole_min'],'knee_at_swing_peak_deg':peak['knee'],'palm_to_body_min_dot':min(v['palm_to_body']for v in data),'palm_to_shaft_min_dot':min((v['palm_to_shaft']for v in data if v['palm_to_shaft'] is not None),default=None),'held_samples':sum(v['palm_to_shaft'] is not None for v in data),'gesture_forward_min_dot':min((v['palm_forward']for v in data if act.name=='Cast' and sd=='L' and phase('Cast',.3)<=v['seconds']<=phase('Cast',.966666667)),default=None),'toe_yaw_max_deg':max(abs(v['toe_yaw'])for v in data)}
 if grips:(P/'review/round2/two_hand_grip.json').write_text(json.dumps({'sample_hz':96,'max_relative_rotation_deg':max(v['relative_rotation_deg']for v in grips),'max_offaxis_m':max(v['offaxis_m']for v in grips),'span_range_m':[min(v['span_m']for v in grips),max(v['span_m']for v in grips)],'min_abs_axes_dot':min(abs(v['axes_dot'])for v in grips),'samples':grips},indent=2))
 report[act.name]=row
 print('POSE',act.name,{sd:{k:(round(v,4) if v is not None else None)for k,v in r.items()}for sd,r in row.items()},flush=True)
(P/'review/batch_pose_audit.json').write_text(json.dumps(report,indent=2))
