"""Actual grip surface, palm direction, sleeve exit and locomotion checks, all clips at 48 Hz."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];prop=bpy.data.objects['BowAsset'];sc=bpy.context.scene
piece=np.array([a.value for a in b.data.attributes['piece'].data]);finger=np.array([a.value for a in b.data.attributes['finger'].data]);rest=np.array([v.co[:]for v in b.data.vertices]);gn={g.index:g.name for g in b.vertex_groups}
# Static grip triangles in the Bow node's local frame; deformation is measured in that frame.
inv=r.data.bones['Bow'].matrix_local.inverted();pv=[inv@v.co for v in prop.data.vertices];faces=[tuple(f.vertices)for f in prop.data.polygons if all(abs(pv[i].z)<.076 and math.hypot(pv[i].x,pv[i].y)<.019 for i in f.vertices)]
tree=BVHTree.FromPolygons(pv,faces);assert len(faces)>=4
b.data.calc_loop_triangles();triangles=[list(t.vertices)for t in b.data.loop_triangles if all(piece[i]==2 for i in t.vertices)]
sample_ids=[];sample_weights=[];sample_labels=[]
for ids in triangles:
 for i in range(9):
  for j in range(9-i):
   weights=[i/8,j/8,(8-i-j)/8];sample_ids.append(ids);sample_weights.append(weights);sample_labels.append(int(finger[ids[int(np.argmax(weights))]]))
sample_ids=np.array(sample_ids);sample_weights=np.array(sample_weights);sample_labels=np.array(sample_labels)
sets={str(i):np.flatnonzero((piece==2)&(finger==i)).tolist()for i in range(6)}
soles={s:[v.index for v in b.data.vertices if v.co.z<.009 and sum(g.weight for g in v.groups if gn[g.group]in[f'B_{s}_Foot',f'B_{s}_Toe0'])>.8]for s in 'LR'}
sleeves={s:[tuple(f.vertices)for f in b.data.polygons if all(piece[i]==0 and rest[i,2]>1.12 and rest[i,0]*(1 if s=='L'else -1)>.13 for i in f.vertices)]for s in 'LR'}
report={'hz':48,'surface_sampling':'Barycentric eighths (45 points per triangle); each reported contact is a point on the actual surface','limits_mm':{'grip_gap':3,'grip_penetration':3,'sleeve_penetration':2},'clips':{}}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];row={'grip_gap_mm':{k:0 for k in sets},'grip_penetration_mm':0,'sleeve_penetration_mm':0,'palm_inward_dot':[1,-1],'sole_height_m':{s:[999,-999]for s in 'LR'},'knee_at_peak_deg':{},'foot_yaw_deg':{s:[999,-999]for s in 'LR'},'bow_tilt_deg':[999,-999], 'bow_string_inward_dot':[1,-1], 'support_fraction':0};peaks={s:-1 for s in 'LR'}
 samples=np.linspace(0,float(a.frame_range[1]),math.ceil(a.frame_range[1]*48/30)+1);support=0
 for f in samples:
  sc.frame_set(int(f),subframe=float(f-int(f)));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=[x.co.copy()for x in me.vertices];ev.to_mesh_clear();inv=r.pose.bones['Bow'].matrix.inverted()
  world=np.array(v);local=np.c_[world,np.ones(len(world))]@np.array(inv).T;points=(local[sample_ids,:3]*sample_weights[:,:,None]).sum(1)
  for k in sets:
   near=points[(sample_labels==int(k))&(abs(points[:,2])<.052)]
   if not len(near):continue
   ds=[tree.find_nearest(Vector(q))[3]for q in near];row['grip_gap_mm'][k]=max(row['grip_gap_mm'][k],1000*min(ds));rad=np.linalg.norm(near[:,:2],axis=1).min();row['grip_penetration_mm']=max(row['grip_penetration_mm'],1000*max(0,.011-rad))
  heights=[]
  axis=r.pose.bones['Bow'].matrix.to_3x3().col[2].normalized();tilt=math.degrees(math.acos(min(1,abs(axis.z))));row['bow_tilt_deg']=[min(row['bow_tilt_deg'][0],tilt),max(row['bow_tilt_deg'][1],tilt)]
  string=r.pose.bones['Bow'].matrix.to_3x3().col[1].normalized();inward=(r.pose.bones['B_L_Thigh'].head-r.pose.bones['Bow'].head);inward.z=0;dot=string.dot(inward.normalized());row['bow_string_inward_dot']=[min(row['bow_string_inward_dot'][0],dot),max(row['bow_string_inward_dot'][1],dot)]
  for s in 'LR':
   st=BVHTree.FromPolygons(v,sleeves[s]);ids=np.flatnonzero(piece==(2 if s=='L'else 3))
   for i in ids:
    p,n,ix,d=st.find_nearest(v[i],.02)
    if p is not None and (v[i]-p).dot(n)<-.7*d:row['sleeve_penetration_mm']=max(row['sleeve_penetration_mm'],d*1000)
   heel=np.array([v[i][:]for i in soles[s]if rest[i,1]>.005]).mean(0);toe=np.array([v[i][:]for i in soles[s]if rest[i,1]<-.065]).mean(0);direction=toe-heel;yaw=math.degrees(math.atan2(direction[0],-direction[1]));lo,hi=row['foot_yaw_deg'][s];row['foot_yaw_deg'][s]=[min(lo,yaw),max(hi,yaw)]
   z=min(v[i].z for i in soles[s]);heights.append(z);lo,hi=row['sole_height_m'][s];row['sole_height_m'][s]=[min(lo,z),max(hi,z)]
   if z>peaks[s]:
    peaks[s]=z;H,K,A=[r.pose.bones[f'B_{s}_'+x].head for x in ['Thigh','Calf','Foot']];row['knee_at_peak_deg'][s]=math.degrees((K-H).angle(A-K))
  support+=min(heights)<.01
  H=r.pose.bones['B_R_Hand'];kn=r.pose.bones['B_R_Finger2'].head-H.head;across=r.pose.bones['B_R_Finger1'].head-r.pose.bones['B_R_Finger4'].head;normal=-kn.cross(across).normalized();inward=(r.pose.bones['B_R_Thigh'].head-H.head);inward.z=0;dot=normal.dot(inward.normalized());row['palm_inward_dot']=[min(row['palm_inward_dot'][0],dot),max(row['palm_inward_dot'][1],dot)]
 row['support_fraction']=support/len(samples)
 report['clips'][a.name]=row;print('R2_CONTACT',a.name,json.dumps(row),flush=True)
report['cloth_scope']='Puff sleeves checked explicitly; fitted trousers and boots have no separate skirt/robe shell. Other body/garment intersections remain covered by G6.'
(P/'review/round2/contact_gates.json').write_text(json.dumps(report,indent=2))

fail=[]
for clip,row in report['clips'].items():
 if max(row['grip_gap_mm'].values())>3 or row['grip_penetration_mm']>3:fail.append((clip,'grip'))
 if row['sleeve_penetration_mm']>2:fail.append((clip,'sleeves'))
 if clip in ('Standing','Fidget')and row['palm_inward_dot'][0]<.8:fail.append((clip,'free palm'))
 if clip in ('Standing','Fidget','Walking'):
  if any(max(abs(x)for x in values)>10 for values in row['foot_yaw_deg'].values()):fail.append((clip,'foot yaw'))
  if row['bow_tilt_deg'][1]>10:fail.append((clip,'bow vertical'))
 if clip=='Walking':
  if any(not .08<=v[1]<=.12 for v in row['sole_height_m'].values()):fail.append((clip,'swing lift'))
  if any(not 40<=v<=60 for v in row['knee_at_peak_deg'].values()):fail.append((clip,'swing knee'))
report['failures']=fail
(P/'review/round2/contact_gates.json').write_text(json.dumps(report,indent=2));assert not fail,fail
