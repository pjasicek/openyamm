"""Five-ring garment cage fitted to the actual posed legs; baked at 48 Hz."""
import bpy,math,json,sys,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent));from cloth_volume import capped_tree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;me=b.data
KEEP=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
for a in list(bpy.data.actions):
 if a.name not in KEEP:bpy.data.actions.remove(a)
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();co=np.array([v.co[:]for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);skids=np.flatnonzero(pv==1);legids=np.flatnonzero((pv==0)&(co[:,2]<.90));skfaces=[f.vertices[:]for f in me.polygons if pv[f.vertices[0]]==1]
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in list(bag.fcurves):
     if 'Skirt_'in fc.data_path:bag.fcurves.remove(fc)
for g in list(b.vertex_groups):
 if g.name.startswith('Skirt_'):b.vertex_groups.remove(g)
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for bo in list(r.data.edit_bones):
 if bo.name.startswith('Skirt_'):r.data.edit_bones.remove(bo)
levels=[.995,.820,.645,.470,.295];N=12;names=[]
for j,z in enumerate(levels):
 for c in range(N):
  a=c*math.tau/N;n=f'Skirt_{j}_{c}';names.append(n);bo=r.data.edit_bones.new(n);bo.head=(.19*math.cos(a),-.03+.145*math.sin(a),z);bo.tail=bo.head+Vector((0,0,-.06));bo.parent=r.data.edit_bones['B_Pelvis']
bpy.ops.object.mode_set(mode='OBJECT');assert len(r.data.bones)<=128,len(r.data.bones)
for n in names:b.vertex_groups.new(name=n)
for i in skids:
 v=me.vertices[i];x=(math.atan2(v.co.y+.03,v.co.x)%math.tau)/math.tau*N;c=int(x);m=x-c;u=np.clip((levels[0]-v.co.z)/.175,0,4);j=min(3,int(u));t=u-j
 for g in b.vertex_groups:g.remove([int(i)])
 for jj,w in [(j,1-t),(j+1,t)]:
  for cc,ww in [(c,1-m),((c+1)%N,m)]:
   if w*ww>1e-6:b.vertex_groups[f'Skirt_{jj}_{cc}'].add([int(i)],float(w*ww),'REPLACE')
rb=r.data.bones;restHip=sum((rb[f'B_{sd}_Thigh'].head_local for sd in 'LR'),Vector())/2;restKnee=sum((rb[f'B_{sd}_Calf'].head_local for sd in 'LR'),Vector())/2;restAnkle=sum((rb[f'B_{sd}_Foot'].head_local for sd in 'LR'),Vector())/2
idx={b.vertex_groups[n].index:k for k,n in enumerate(names)};CW=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:
  if g.group in idx:CW[v.index,idx[g.group]]=g.weight
boundary={}
for face in skfaces:
 for i,j in zip(face,list(face[1:])+[face[0]]):e=tuple(sorted((i,j)));boundary[e]=boundary.get(e,0)+1
boundary=[e for e,n in boundary.items()if n==1]
def posed():
 ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();pos=np.array([v.co[:]for v in mm.vertices]);ev.to_mesh_clear();return pos
reports={}
for act in bpy.data.actions:
 if act.name=='Dead':continue
 r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];nf=float(act.frame_range[1]);samples=[]
 for f in np.linspace(0,nf,math.ceil(nf*48/30)+1):
  sc.frame_set(int(f),subframe=float(f%1));T=r.pose.bones['B_Pelvis'].matrix@rb['B_Pelvis'].matrix_local.inverted();J=[sum((r.pose.bones[f'B_{sd}_{part}'].head for sd in 'LR'),Vector())/2 for part in ['Thigh','Calf','Foot']];samples.append((f,T.copy(),J,posed()[legids]))
 r.animation_data.action=None;worst=0.;maxcorr=0.;prev={}
 for f,T,J,skin in samples:
  r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];sc.frame_set(int(f),subframe=float(f%1));r.animation_data.action=None;initial=[]
  for j,z in enumerate(levels):
   R=T.to_3x3();C=T@Vector((0,-.03,z));rx,ry=.19,.145
   if act.name in ['Walking','Running','Death']and j>0:
    if z>=restKnee.z:a0,a1=restHip,restKnee;b0,b1=J[0],J[1]
    else:a0,a1=restKnee,restAnkle;b0,b1=J[1],J[2]
    t=(a0.z-z)/(a0.z-a1.z);restCentre=a0.lerp(a1,t);centre=b0.lerp(b1,t);axis=(a1-a0).normalized();R=(R@axis).rotation_difference((b1-b0).normalized()).to_matrix()@R;C=centre+R@(Vector((0,-.03,z))-restCentre)
    blend=max(0,min(1,(.955-z)/.10));C=(T@Vector((0,-.03,z))).lerp(C,blend);R=T.to_quaternion().slerp(R.to_quaternion(),blend).to_matrix()
    band=np.abs(co[legids,2]-z)<.095
    if band.any():
     local=(skin[band]-np.array(C))@np.array(R);rx=max(rx,float(abs(local[:,0]).max())+.014);ry=max(ry,float(abs(local[:,1]).max())+.014)
   for c in range(N):
    a=c*math.tau/N;n=f'Skirt_{j}_{c}';target=C+R@Vector((rx*math.cos(a),ry*math.sin(a),0))
    if act.name=='Death':target.z=max(.0003,target.z)
    M=(R@rb[n].matrix_local.to_3x3()).to_4x4();M.translation=target;r.pose.bones[n].matrix=M;bpy.context.view_layer.update();initial.append(M.copy())
  shifts=np.zeros((len(names),3))
  for iteration in range(8):
   pos=posed();tree=capped_tree(pos,skfaces,boundary);cor=np.zeros_like(shifts);den=np.zeros(len(names));depth=0.
   for point in pos[legids]:
    loc,no,fi,d=tree.find_nearest(Vector(point),.10)
    if loc is None or fi>=len(skfaces) or (Vector(point)-loc).dot(no)<.7*d or d<.0005:continue
    face=skfaces[fi];edgehit=False
    for e in boundary:
     if e[0]not in face or e[1]not in face:continue
     A=pos[e[0]];B=pos[e[1]];v=B-A;u=np.clip((np.array(loc)-A)@v/(v@v),0,1)
     if np.linalg.norm(np.array(loc)-A-u*v)<1e-5:edgehit=True;break
    if edgehit:continue
    depth=max(depth,d);ww=CW[list(face)].mean(0)
    for k in np.flatnonzero(ww>.01):cor[k]+=np.array(no)*(d+.0015)*ww[k];den[k]+=ww[k]
   if depth<.001:break
   for k,n in enumerate(names):
    if den[k]>0:shifts[k]+=cor[k]/den[k]*.75
    M=initial[k].copy();M.translation+=Vector(shifts[k]);r.pose.bones[n].matrix=M;bpy.context.view_layer.update()
  worst=max(worst,depth);maxcorr=max(maxcorr,float(np.linalg.norm(shifts,axis=1).max()));r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
  for n in names:
   pb=r.pose.bones[n];pb.rotation_mode='QUATERNION'
   if n in prev and pb.rotation_quaternion.dot(prev[n])<0:pb.rotation_quaternion=-pb.rotation_quaternion
   prev[n]=pb.rotation_quaternion.copy();pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  r.animation_data.action=None
 reports[act.name]={'worst_residual_m':worst,'max_control_correction_m':maxcorr,'samples':len(samples)};print('FITTED_SKIRT',act.name,reports[act.name],flush=True)
# The corpse owns the exact final fall pose, including its garment.
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));held={n:(pb.rotation_quaternion.copy(),pb.location.copy(),pb.scale.copy())for n,pb in r.pose.bones.items()};r.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=30;r.animation_data.action=a
for f in [0,30]:
 for n,(q,l,s)in held.items():pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f);pb.keyframe_insert('scale',frame=f)
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/'review/final_skirt_fit.json').write_text(json.dumps(reports,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
