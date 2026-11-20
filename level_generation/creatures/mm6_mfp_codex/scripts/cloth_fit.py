"""Bake a three-ring garment control cage against the moving lower legs at 48 Hz."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;sc=bpy.context.scene
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();co=np.array([v.co[:]for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);skids=np.flatnonzero(pv==1);skfaces=[f.vertices[:]for f in me.polygons if pv[f.vertices[0]]==1];legids=np.flatnonzero((co[:,2]<.405)&np.isin(pv,[0,13,14,16,17,22,23,24,25,26,27]))
# Discard the first coarse meridians and their channels before fitting the finer cage.
for a in bpy.data.actions:
 for lay in a.layers:
  for st in lay.strips:
   for bag in st.channelbags:
    for fc in list(bag.fcurves):
     if 'Skirt_'in fc.data_path:bag.fcurves.remove(fc)
for g in list(b.vertex_groups):
 if g.name.startswith('Skirt_'):b.vertex_groups.remove(g)
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for bo in list(r.data.edit_bones):
 if bo.name.startswith('Skirt_'):r.data.edit_bones.remove(bo)
levels=[.955,.64,.325];N=12
for j,z in enumerate(levels):
 for c in range(N):
  a=c*math.tau/N;rad=.16 if j==0 else .19;pt=Vector((rad*math.cos(a),-.03+rad*.8*math.sin(a),z));bo=r.data.edit_bones.new(f'Skirt_{j}_{c}');bo.head=pt;bo.tail=pt+Vector((0,0,-.08));bo.parent=r.data.edit_bones['B_Pelvis']
bpy.ops.object.mode_set(mode='OBJECT');names=[f'Skirt_{j}_{c}'for j in range(3)for c in range(N)]
for n in names:b.vertex_groups.new(name=n)
for i in skids:
 v=me.vertices[i];a=math.atan2(v.co.y+.03,v.co.x)%math.tau;x=a/math.tau*N;c=int(x);m=x-c;u=np.clip((levels[0]-v.co.z)/(levels[0]-levels[1]),0,2);j=min(1,int(u));t=u-j;pin=float(np.clip((v.co.z-.955)/.06,0,1));weights={'B_Pelvis':pin}
 for ring,w in [(j,1-t),(j+1,t)]:
  for cc,ww in [(c,1-m),((c+1)%N,m)]:weights[f'Skirt_{ring}_{cc}']=w*ww*(1-pin)
 for g in b.vertex_groups:g.remove([int(i)])
 for n,w in weights.items():
  if w>1e-6:b.vertex_groups[n].add([int(i)],float(w),'REPLACE')
# Dense control weights make a local collision correction independent of the authoring solver.
idx={b.vertex_groups[n].index:k for k,n in enumerate(names)};CW=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:
  if g.group in idx:CW[v.index,idx[g.group]]=g.weight
rb=r.data.bones;inv={n:rb[n].matrix_local.inverted()for n in ['B_Pelvis','B_L_Thigh','B_R_Thigh','B_L_Calf','B_R_Calf']}
boundary=[];counts={}
for f in skfaces:
 for a,z in zip(f,list(f[1:])+[f[0]]):key=tuple(sorted((a,z)));counts[key]=counts.get(key,0)+1
boundary=[e for e,n in counts.items()if n==1]
def evaluate():
 ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.array([v.co[:]for v in m.vertices]);ev.to_mesh_clear();return p
report={}
for act in bpy.data.actions:
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];nf=float(act.frame_range[1]);records=[]
 # Native body samples are read before adding the new cage tracks.
 for f in np.linspace(0,nf,math.ceil(nf*48/30)+1):
  sc.frame_set(int(f),subframe=float(f%1));D={n:r.pose.bones[n].matrix@inv[n]for n in inv}
  # Cloth follows the leg's bending plane, not its source animation axial roll.
  for sd in 'LR':
   for part,child in [('Thigh','Calf'),('Calf','Foot')]:
    n=f'B_{sd}_{part}';cn=f'B_{sd}_{child}';axis=(rb[cn].head_local-rb[n].head_local).normalized();posed=(r.pose.bones[cn].head-r.pose.bones[n].head).normalized();R=D['B_Pelvis'].to_3x3();R=(R@axis).rotation_difference(posed).to_matrix()@R;mat=R.to_4x4();mat.translation=r.pose.bones[n].head-R@rb[n].head_local;D[n]=mat
  records.append((f,D))
 r.animation_data.action=None;worst=0.;maxshift=0.;prev={}
 for f,D in records:
  r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];sc.frame_set(int(f),subframe=float(f%1));r.animation_data.action=None;T=D['B_Pelvis'];initial=[]
  for j,z in enumerate(levels):
   for c in range(N):
    a=c*math.tau/N;n=f'Skirt_{j}_{c}';rest=rb[n].head_local;w=(math.cos(a)+1)/2
    DL=D['B_L_Thigh'if j==1 else'B_L_Calf'];DR=D['B_R_Thigh'if j==1 else'B_R_Calf']
    if j==0:DL=DR=T
    q=DR.to_quaternion().slerp(DL.to_quaternion(),w);target=(DR@rest).lerp(DL@rest,w)
    # Front/back cloth follows the leading limb envelope, never the mean gap between the two limbs.
    normal=q@Vector((math.cos(a),math.sin(a),0));spread=max((DL@rest-target).dot(normal),(DR@rest-target).dot(normal),0);target+=normal*spread*.95
    mat=(q.to_matrix()@rb[n].matrix_local.to_3x3()).to_4x4();mat.translation=target;r.pose.bones[n].matrix=mat;bpy.context.view_layer.update();initial.append(mat.copy())
  shift=np.zeros((len(names),3))
  for iteration in range(10):
   pos=evaluate();tree=BVHTree.FromPolygons(pos.tolist(),skfaces);cor=np.zeros_like(shift);den=np.zeros(len(names));depth=0.
   for point in pos[legids]:
    loc,no,fi,d=tree.find_nearest(Vector(point),.12)
    if loc is None or (Vector(point)-loc).dot(no)<.7*d or d<.0005:continue
    face=skfaces[fi];vertices=pos[list(face)];nearest=min(np.linalg.norm(vertices-np.array(loc),axis=1))
    # An open hem has no interior below its boundary; do not close it around the feet.
    on_boundary=False
    for e in boundary:
     if e[0]not in face or e[1]not in face:continue
     A=pos[e[0]];B=pos[e[1]];v=B-A;u=np.clip((np.array(loc)-A)@v/(v@v),0,1)
     if np.linalg.norm(np.array(loc)-(A+u*v))<1e-5:on_boundary=True;break
    if on_boundary:continue
    depth=max(depth,d);ww=CW[list(face)].mean(0);active=ww>.01;delta=np.array(no)*(d+.0015)
    for k in np.flatnonzero(active):cor[k]+=delta*ww[k];den[k]+=ww[k]
   worst=max(worst,depth if iteration==9 else 0)
   if depth<.001:break
   for k,n in enumerate(names):
    if den[k]>0:
     shift[k]+=cor[k]/den[k]*.60
     if np.linalg.norm(shift[k])>.06:shift[k]*=.06/np.linalg.norm(shift[k])
    mat=initial[k].copy();mat.translation+=Vector(shift[k]);r.pose.bones[n].matrix=mat;bpy.context.view_layer.update()
  maxshift=max(maxshift,float(np.linalg.norm(shift,axis=1).max()))
  r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
  for n in names:
   pb=r.pose.bones[n];pb.rotation_mode='QUATERNION';q=pb.rotation_quaternion.copy()
   if n in prev and q.dot(prev[n])<0:pb.rotation_quaternion=-q
   prev[n]=pb.rotation_quaternion.copy();pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  r.animation_data.action=None
 report[act.name]={'worst_unresolved_m':worst,'max_local_correction_m':maxshift,'samples':len(records)};print('CLOTH',act.name,report[act.name],flush=True)
for act in bpy.data.actions:
 for lay in act.layers:
  for st in lay.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/'review/cloth_fit.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
