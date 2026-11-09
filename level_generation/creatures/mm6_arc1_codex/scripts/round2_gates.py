"""Signed anatomy, sole-contact and native rest measurements at 48 Hz, independent of authoring."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'))
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;gn={g.index:g.name for g in body.vertex_groups};rest=np.array([v.co[:]for v in body.data.vertices]);sole={};ref={}
for s in 'LR':
 ix=[v.index for v in body.data.vertices if v.co.z<.009 and sum(g.weight for g in v.groups if gn[g.group]in[f'B_{s}_Foot',f'B_{s}_Toe0'])>.8]
 assert len(ix)>=3
 sole[s]={'all':ix,'heel':[i for i in ix if rest[i,1]>.005],'toe':[i for i in ix if rest[i,1]<-.065]}
 assert len(sole[s]['heel'])>=1 and len(sole[s]['toe'])>=1,sole[s]
 U,F,H=[r.data.bones[f'B_{s}_'+n]for n in ['UpperArm','Forearm','Hand']];ua=(F.head_local-U.head_local).normalized();fa=(H.head_local-F.head_local).normalized()
 ref[s]={'hinge':(U.matrix_local.to_3x3().inverted()@ua.cross(fa)).normalized(),'axis':(F.matrix_local.to_3x3().inverted()@fa).normalized(),'relative':U.matrix_local.to_3x3().inverted()@F.matrix_local.to_3x3()}
report={'sample_rate_hz':48,'limits':{'hyperextension_degrees':5,'forearm_roll_degrees':90,'sole_tilt_degrees':3,'heel_and_toe_height_m':.01},'sole_vertices':sole,'clips':{}}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];row={'elbow':{s:{'signed_flexion_degrees':[999,-999],'max_forearm_roll_degrees':0}for s in 'LR'},'soles':{s:{'max_tilt_degrees':0,'heel_height_m':[999,-999],'toe_height_m':[999,-999]}for s in 'LR'} if a.name in ('Standing','Fidget')else{}}
 for t in np.linspace(0,float(a.frame_range[1]),math.ceil(a.frame_range[1]*48/30)+1):
  sc.frame_set(int(t),subframe=float(t-int(t)))
  for s in 'LR':
   U,F,H=[r.pose.bones[f'B_{s}_'+n]for n in ['UpperArm','Forearm','Hand']];u=(F.head-U.head).normalized();f=(H.head-F.head).normalized();h=U.matrix.to_3x3()@ref[s]['hinge'];bend=math.degrees(math.atan2(h.dot(u.cross(f)),u.dot(f)));e=row['elbow'][s];e['signed_flexion_degrees']=[min(e['signed_flexion_degrees'][0],bend),max(e['signed_flexion_degrees'][1],bend)]
   R=U.matrix.to_3x3()@ref[s]['relative'];R=(R@ref[s]['axis']).rotation_difference(f).to_matrix()@R;q=(R.inverted()@F.matrix.to_3x3()).to_quaternion();roll=math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).dot(ref[s]['axis']),q.w));roll=(roll+180)%360-180;e['max_forearm_roll_degrees']=max(e['max_forearm_roll_degrees'],abs(roll))
  if row['soles']:
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([x.co[:]for x in m.vertices]);ev.to_mesh_clear()
   for s in 'LR':
    so=row['soles'][s];pts=v[sole[s]['all']];normal=np.linalg.svd(pts-pts.mean(0))[2][-1];tilt=math.degrees(math.acos(min(1,abs(float(normal[2])))));so['max_tilt_degrees']=max(so['max_tilt_degrees'],tilt)
    for part in ['heel','toe']:
     z=float(v[sole[s][part],2].min());lo,hi=so[part+'_height_m'];so[part+'_height_m']=[min(lo,z),max(hi,z)]
 report['clips'][a.name]=row
 print('ANATOMY',a.name,row)
# Direct front orthographic measures, with native landmarks retained for reproducibility.
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([x.co[:]for x in m.vertices]);ev.to_mesh_clear();height=float(v[:,2].max()-v[:,2].min());centres={s:v[sole[s]['all']].mean(0)for s in 'LR'}
measure={'height_m':height,'foot_spacing_per_height':float(abs(centres['L'][0]-centres['R'][0])/height),'body_width_per_height':float(np.ptp(v[:,0])/height),'upper_arm_front_angle_degrees':{},'forearm_front_angle_degrees':{}}
for s in 'LR':
 for field,A,B in [('upper_arm_front_angle_degrees','UpperArm','Forearm'),('forearm_front_angle_degrees','Forearm','Hand')]:
  d=r.pose.bones[f'B_{s}_'+B].head-r.pose.bones[f'B_{s}_'+A].head;measure[field][s]=math.degrees(math.atan2(abs(d.x),abs(d.z)))
report['native_comparison']={'native_file':'../mm6_arc1/native/arc1sta0.png','native_opaque_height_px':256,'native_front_landmarks_px':{'right_shoulder':[183,104],'right_elbow':[183,141],'right_wrist':[178,173],'left_shoulder':[231,104],'left_elbow':[231,141],'left_wrist':[234,173],'foot_centres':[196,219],'body_silhouette_x':[175,239]},'native':{'foot_spacing_per_height':23/256,'body_width_per_height':64/256,'upper_arm_front_angle_degrees':0,'forearm_front_angle_degrees':[math.degrees(math.atan2(5,32)),math.degrees(math.atan2(3,32))]},'model':measure,'landmark_uncertainty_px':2}
fail=[]
for name,row in report['clips'].items():
 for side,e in row['elbow'].items():
  if e['signed_flexion_degrees'][0]<-5:fail.append(f'{name} {side} elbow hyperextension')
  if e['max_forearm_roll_degrees']>90:fail.append(f'{name} {side} forearm roll')
 for side,e in row['soles'].items():
  if e['max_tilt_degrees']>3:fail.append(f'{name} {side} sole tilt')
  for part in ['heel','toe']:
   if max(abs(x)for x in e[part+'_height_m'])>.01:fail.append(f'{name} {side} {part} contact')
report['failures']=fail;(P/'review/round2/anatomy_and_feet.json').write_text(json.dumps(report,indent=2));print('FAILURES',fail)
assert not fail,fail
