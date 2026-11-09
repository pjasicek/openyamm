import bpy,numpy as np,json,math,os
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/os.environ.get('GATE_BLEND','work/anim_twist.blend')))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;sc=bpy.context.scene;B=r.data.bones
co=np.array([v.co[:] for v in me.vertices]);E=np.array([e.vertices[:] for e in me.edges]);lens=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);names=[g.name for g in b.vertex_groups];W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
pv=np.array([v.value for v in me.attributes['piece'].data]);regions={}
for sd in ['L','R']:
 for region,keys in [('arm',['UpperArm','Forearm','Hand']),('hand',['Hand','Finger'])]:
  vs=W[:,[i for i,n in enumerate(names) if n.startswith(f'B_{sd}_') and any(k in n for k in keys)]].sum(1)>.3
  regions[sd+'_'+region]=vs[E[:,0]] & vs[E[:,1]]
report={}
for a in bpy.data.actions:
 if not a.use_fake_user:continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];worst={k:{'p99':0.,'max':0.} for k in regions};heights=[];leans=[];floors=[];soles={s:[] for s in 'LR'};knees={s:[] for s in 'LR'};rolls={s:[] for s in 'LR'};elbows={s:[] for s in 'LR'};planes={s:[] for s in 'LR'};wrists={s:[] for s in 'LR'};ua={s:[] for s in 'LR'}
 for f in sorted(set(list(np.arange(0,float(a.frame_range[1])+.00001,30/48))+[float(a.frame_range[1])])):
  sc.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();P=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();st=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)/np.maximum(lens,1e-6)
  for k,mask in regions.items():
   for label,value in [('p99',np.percentile(st[mask],99)),('max',st[mask].max())]:
    if value>worst[k][label]:worst[k][label]=float(value);worst[k][label+'_frame']=float(f)
  pelvis=r.pose.bones['B_Pelvis'].head;neck=r.pose.bones['B_Neck'].head;v=neck-pelvis;heights.append(pelvis.z);leans.append(math.degrees(math.atan2(math.hypot(v.x,v.y),v.z)));floors.append(float(P[:,2].min()))
  for sd,pi in [('L',11),('R',10)]:
   soles[sd].append([float(P[pv==pi,2].min()),float(P[pv==pi,2].max())]);sh,el,wr=[r.pose.bones[f'B_{sd}_{n}'].head for n in ['UpperArm','Forearm','Hand']];up=(el-sh).normalized();fa=(wr-el).normalized();ub,fb,hb=[B[f'B_{sd}_{n}'] for n in ['UpperArm','Forearm','Hand']]
   ur=(fb.head_local-ub.head_local).normalized();fr=(hb.head_local-fb.head_local).normalized();nr=ur.cross(Vector((0,-1,0))).normalized();Ru=r.pose.bones[ub.name].matrix.to_3x3()@ub.matrix_local.to_3x3().inverted();normal=Ru@nr
   elbows[sd].append(math.degrees(math.atan2(up.cross(fa).dot(normal),up.dot(fa))));planes[sd].append(math.degrees(math.asin(min(1,abs(fa.dot(normal))))))
   Rf=r.pose.bones[fb.name].matrix.to_3x3()@fb.matrix_local.to_3x3().inverted();Rh=r.pose.bones[hb.name].matrix.to_3x3()@hb.matrix_local.to_3x3().inverted();q=(Rf.inverted()@Rh).to_quaternion();tw=math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).dot(fr),q.w));rolls[sd].append((tw+180)%360-180)
   finger=(B[f'B_{sd}_Finger2'].head_local-hb.head_local).normalized();wrists[sd].append(math.degrees((Rh@finger).angle(fa)))
   uq=r.pose.bones[ub.name].matrix_basis.to_quaternion();axis=(ub.matrix_local.inverted()@fb.head_local).normalized();ut=math.degrees(2*math.atan2(Vector((uq.x,uq.y,uq.z)).dot(axis),uq.w));ua[sd].append((ut+180)%360-180)
   th,kn,ank=[r.pose.bones[f'B_{sd}_{n}'].head for n in ['Thigh','Calf','Foot']];knees[sd].append(math.degrees((kn-th).angle(ank-kn)))
 row={'samples_48hz':len(floors),'stretch':worst,'pelvis_height_m':[min(heights),max(heights)],'trunk_lean_deg':[min(leans),max(leans)],'min_floor_mm':min(floors)*1000,'arms':{},'feet':{}}
 for sd in 'LR':
  sol=np.array(soles[sd]);i=int(sol[:,0].argmax());row['feet'][sd]={'lowest_sole_mm':float(sol[:,0].min()*1000),'swing_peak_mm':float(sol[:,0].max()*1000),'knee_at_peak_deg':knees[sd][i],'max_knee_deg':max(knees[sd]),'max_sole_top_mm':float(sol[:,1].max()*1000)}
  row['arms'][sd]={'elbow_deg':[min(elbows[sd]),max(elbows[sd])],'hinge_offplane_max_deg':max(planes[sd]),'forearm_roll_deg':[min(rolls[sd]),max(rolls[sd])],'upper_arm_roll_deg':[min(ua[sd]),max(ua[sd])],'wrist_swing_max_deg':max(wrists[sd])}
 row['both_feet_air_fraction']=float(np.mean((np.array(soles['L'])[:,0]>.01)&(np.array(soles['R'])[:,0]>.01)))
 row['G4_pass']=max(worst[k]['p99'] for k in ['L_arm','R_arm'])<=2.;row['G5_pass']=max(worst[k]['max'] for k in ['L_hand','R_hand'])<=4.5
 row['elbow_pass']=all(min(elbows[s])>=-5 and max(planes[s])<5 for s in 'LR');row['roll_pass']=all(max(abs(x) for x in rolls[s])<=90.5 for s in 'LR')
 report[a.name]=row;print('DENSE',a.name,json.dumps(row),flush=True)
(p/os.environ.get('GATE_REPORT','work/dense_gates.json')).write_text(json.dumps(report,indent=2))
