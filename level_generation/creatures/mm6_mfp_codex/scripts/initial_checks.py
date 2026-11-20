import bpy,sys,math,json,os,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
from cloth_volume import capped_tree
bpy.ops.wm.open_mainfile(filepath=os.environ.get('GATE_BLEND',str(P/'work/rig_equipped.blend')))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;me=b.data;gn={g.index:g.name for g in b.vertex_groups};co=np.array([v.co[:]for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);nv=len(co)
W=np.zeros((nv,len(gn)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
edges=np.array([e.vertices[:]for e in me.edges]);rl=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1);faces=[tuple(f.vertices)for f in me.polygons]
def wt(sd,keys):return W[:,[i for i,n in gn.items()if n.startswith('B_'+sd+'_')and any(k in n for k in keys)]].sum(1)
sole={};refs={};masks={}
for sd in 'LR':
 ids=np.flatnonzero((co[:,2]<.008)&(wt(sd,['Foot','Toe'])>.8));assert len(ids)>5
 y=co[ids,1];sole[sd]={'all':ids,'heel':ids[y>np.percentile(y,70)],'toe':ids[y<np.percentile(y,30)]}
 U,F,H=[r.data.bones[f'B_{sd}_'+n]for n in ['UpperArm','Forearm','Hand']];u=(F.head_local-U.head_local).normalized();f=(H.head_local-F.head_local).normalized();refs[sd]={'hinge':(U.matrix_local.to_3x3().inverted()@u.cross(f)).normalized(),'axis':(F.matrix_local.to_3x3().inverted()@f).normalized(),'rel':U.matrix_local.to_3x3().inverted()@F.matrix_local.to_3x3()}
 masks[sd]={'hand':wt(sd,['Hand','Finger'])>.5,'forearm':wt(sd,['Forearm'])>.5,'arm':wt(sd,['UpperArm','Clavicle','Forearm','Hand','Finger'])>.2}
skirtfaces=[f for f in faces if pv[f[0]]==1];legids=np.flatnonzero((co[:,2]<.875)&np.isin(pv,[0,13,14,16,17,22,23,24,25,26,27]))
headids=np.flatnonzero((co[:,2]>1.43)&(pv==0));headobs=(co[:,2]>1.1)&(co[:,2]<1.42)&(pv==0);headfaces=[fc for fc in faces if all(headobs[i]for i in fc)]
# Weld UV seams before closing the cut torso; jewellery is a separate surface.
_,head_first,head_map=np.unique(np.round(co,5),axis=0,return_index=True,return_inverse=True)
head_poly=[tuple(head_map[list(f)])for f in headfaces];head_poly=[f for f in head_poly if len(set(f))==len(f)]
head_edge_counts={}
for face in head_poly:
 for i,j in zip(face,list(face[1:])+[face[0]]):e=tuple(sorted((i,j)));head_edge_counts[e]=head_edge_counts.get(e,0)+1
head_boundary=[e for e,n in head_edge_counts.items()if n==1]
def inside(tree,point):
 votes=0
 for direction in [Vector((.371,.619,.693)).normalized(),Vector((-.713,.533,.455)).normalized(),Vector((.251,-.918,.307)).normalized()]:
  origin=point.copy();hits=0
  for _ in range(40):
   hit,normal,face,distance=tree.ray_cast(origin,direction,3)
   if hit is None:break
   hits+=1;origin=hit+direction*1e-5
  votes+=hits%2
 return votes>=2
counts={}
for face in skirtfaces:
 for i,j in zip(face,list(face[1:])+[face[0]]):e=tuple(sorted((i,j)));counts[e]=counts.get(e,0)+1
boundary=[e for e,n in counts.items()if n==1]
report={'sample_hz':48,'clips':{}};constraints={}
for a in [x for x in bpy.data.actions if x.name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']]:
 r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];nf=float(a.frame_range[1]);row={'elbow':{},'feet':{},'g4':{},'g5':{},'g6_mm':{},'cloth_mm':0.,'head_shoulder_mm':0.,'contact_witness':{},'cloth_witness':None,'pelvis_height_m':[999,-999],'trunk_lean_deg':[999,-999]}
 for sd in 'LR':
  row['elbow'][sd]={'flex':[999,-999],'roll_max':0.};row['feet'][sd]={'lowest_m':[999,-999],'heel_max_m':-999,'toe_max_m':-999,'swing_peak_m':0.,'knee_max_deg':0.};row['g4'][sd]={'p99_max':0.,'max':0.};row['g5'][sd]=0.;row['g6_mm'][sd]=0.
 for t in np.linspace(0,nf,math.ceil(nf*48/30)+1):
  sc.frame_set(int(t),subframe=float(t%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();pos=np.array([v.co[:]for v in m.vertices]);ev.to_mesh_clear();rat=np.linalg.norm(pos[edges[:,0]]-pos[edges[:,1]],axis=1)/np.maximum(rl,1e-6)
  pelvis=r.pose.bones['B_Pelvis'].head;neck=r.pose.bones['B_Neck'].head;lean=math.degrees((neck-pelvis).angle(Vector((0,0,1))))
  row['pelvis_height_m']=[min(row['pelvis_height_m'][0],pelvis.z),max(row['pelvis_height_m'][1],pelvis.z)];row['trunk_lean_deg']=[min(row['trunk_lean_deg'][0],lean),max(row['trunk_lean_deg'][1],lean)]
  for sd in 'LR':
   U,F,H=[r.pose.bones[f'B_{sd}_'+n]for n in ['UpperArm','Forearm','Hand']];u=(F.head-U.head).normalized();f=(H.head-F.head).normalized();h=U.matrix.to_3x3()@refs[sd]['hinge'];bend=math.degrees(math.atan2(h.dot(u.cross(f)),u.dot(f)));el=row['elbow'][sd];el['flex']=[min(el['flex'][0],bend),max(el['flex'][1],bend)]
   R=U.matrix.to_3x3()@refs[sd]['rel'];R=(R@refs[sd]['axis']).rotation_difference(f).to_matrix()@R;q=(R.inverted()@F.matrix.to_3x3()).to_quaternion();roll=math.degrees(2*math.atan2(Vector((q.x,q.y,q.z)).dot(refs[sd]['axis']),q.w));roll=(roll+180)%360-180;el['roll_max']=max(el['roll_max'],abs(roll))
   ft=row['feet'][sd];z=float(pos[sole[sd]['all'],2].min());ft['lowest_m']=[min(ft['lowest_m'][0],z),max(ft['lowest_m'][1],z)];ft['swing_peak_m']=max(ft['swing_peak_m'],z)
   for part in ['heel','toe']:ft[part+'_max_m']=max(ft[part+'_max_m'],float(pos[sole[sd][part],2].min()))
   T,C,A=[r.pose.bones[f'B_{sd}_'+n].head for n in ['Thigh','Calf','Foot']];ft['knee_max_deg']=max(ft['knee_max_deg'],math.degrees((C-T).angle(A-C)))
   for label,key in [('g4','arm'),('g5','hand')]:
    mask=masks[sd][key];ie=mask[edges[:,0]]&mask[edges[:,1]]&(rl>1e-5)
    if label=='g4':row[label][sd]['p99_max']=max(row[label][sd]['p99_max'],float(np.percentile(rat[ie],99)));row[label][sd]['max']=max(row[label][sd]['max'],float(rat[ie].max()))
    else:row[label][sd]=max(row[label][sd],float(rat[ie].max()))
   keep=~masks[sd]['arm'];fl=[fc for fc in faces if all(keep[i]for i in fc)];tree=BVHTree.FromPolygons(pos.tolist(),fl)
   for vid in np.flatnonzero(masks[sd]['hand']|masks[sd]['forearm']):
    point=pos[vid]
    loc,n,idx,d=tree.find_nearest(Vector(point),.05)
    if loc is not None and (Vector(point)-loc).dot(n)<-.7*d and d*1000>row['g6_mm'][sd]:
     row['g6_mm'][sd]=d*1000;row['contact_witness'][sd]={'frame':float(t),'vertex':int(vid),'piece':int(pv[vid]),'rest':co[vid].tolist(),'world':point.tolist(),'face_piece':int(pv[fl[idx][0]]),'closest':list(loc)}
  headtree=capped_tree(pos[head_first],head_poly,head_boundary)
  for vid in headids:
   point=Vector(pos[vid]);loc,n,idx,d=headtree.find_nearest(point,.05)
   if loc is not None and idx<len(head_poly) and inside(headtree,point) and d*1000>row['head_shoulder_mm']:
    row['head_shoulder_mm']=d*1000;row['head_witness']={'frame':float(t),'vertex':int(vid),'rest':co[vid].tolist(),'world':list(point),'closest':list(loc)}
  tree=capped_tree(pos,skirtfaces,boundary)
  for vid in legids:
   point=pos[vid]
   loc,n,idx,d=tree.find_nearest(Vector(point),.07)
   if loc is not None and idx<len(skirtfaces) and (Vector(point)-loc).dot(n)>.7*d:
    on_boundary=False;face=skirtfaces[idx]
    for e in boundary:
     if e[0]not in face or e[1]not in face:continue
     A=pos[e[0]];B=pos[e[1]];v=B-A;u=np.clip((np.array(loc)-A)@v/(v@v),0,1)
     if np.linalg.norm(np.array(loc)-(A+u*v))<1e-5:on_boundary=True;break
    if not on_boundary and d>.0008 and os.environ.get('FIT_CLOTH')=='1':
     L=sum((np.array((r.pose.bones[gn[g.group]].matrix@r.data.bones[gn[g.group]].matrix_local.inverted()).to_3x3())*g.weight for g in me.vertices[vid].groups if gn[g.group] in r.pose.bones),np.zeros((3,3)))
     normal=np.array(n)@L;constraints.setdefault(int(vid),[]).append((normal,-(d-.0008)))
    if not on_boundary and d*1000>row['cloth_mm']:
     row['cloth_mm']=d*1000;row['cloth_witness']={'frame':float(t),'vertex':int(vid),'piece':int(pv[vid]),'rest':co[vid].tolist(),'world':point.tolist(),'closest':list(loc)}
 report['clips'][a.name]=row;print('GATES',a.name,json.dumps(row),flush=True)
 Path(os.environ.get('GATE_REPORT',str(P/'review/initial_gates.json'))).write_text(json.dumps(report,indent=2))
if os.environ.get('FIT_CLOTH')=='1':
 corrections={}
 for vid,cons in constraints.items():
  shift=np.zeros(3)
  for iteration in range(30):
   for n,bound in cons:
    error=n@shift-bound
    if error>0:shift-=n*error/max(n@n,1e-9)
  assert np.linalg.norm(shift)<float(os.environ.get('FIT_MAX_M','.015')),('excessive hidden-leg correction',vid,shift)
  me.vertices[vid].co+=Vector(shift);corrections[vid]=list(shift)
 me.update()
 report['under_garment_vertex_corrections_m']=corrections
 Path(os.environ['GATE_REPORT']).write_text(json.dumps(report,indent=2))
 for a in bpy.data.actions:
  if a.name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:a.use_fake_user=True
 bpy.ops.wm.save_as_mainfile(filepath=os.environ['GATE_BLEND'])
 print('FIT_UNDER_GARMENT',len(corrections),max((np.linalg.norm(v)for v in corrections.values()),default=0),flush=True)
if os.environ.get('GATE_RENDER','1')!='0':
 # Six-frame clip sheets are assembled by the ordinary image helper after this run.
 common.workbench_clay(sc)
 for a in [x for x in bpy.data.actions if x.name in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']]:
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];folder=P/'review/clay_clips'/a.name;folder.mkdir(parents=True,exist_ok=True)
  for j,f in enumerate(np.linspace(0,a.frame_range[1],6)):
   sc.frame_set(int(f),subframe=float(f%1));common.render_views(str(folder/f'{j:02}'),.82,1.90,views=('front','left','three_quarter'),resolution=(280,420))
