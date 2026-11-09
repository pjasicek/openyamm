"""Baked braid inertia, final twist distribution, normalized skin and conservative floor envelope."""
import bpy,sys,math,json,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/before_secondary.blend'))
for ob in [body,bpy.data.objects['KnifeAsset']]:
 for v in ob.data.vertices:
  weights=sorted([(g.group,g.weight)for g in v.groups if g.weight>1e-7 and ob.vertex_groups[g.group].name in rig.data.bones],key=lambda x:-x[1])[:8];total=sum(w for _,w in weights);assert total>0
  for g in list(v.groups):ob.vertex_groups[g.group].remove([v.index])
  for g,w in weights:ob.vertex_groups[g].add([v.index],w/total,'REPLACE')
names=[f'Braid_{i}'for i in range(3)];lengths=[rig.data.bones[n].length for n in names]
for act in list(bpy.data.actions):
 if act.name=='Dead':continue
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];nf=float(act.frame_range[1]);fps=60;times=np.linspace(0,nf,math.ceil(nf*fps/30)+1);samples=[]
 for f in times:
  sc.frame_set(int(f),subframe=float(f%1));samples.append({n:rig.pose.bones[n].matrix.copy()for n in ['B_Head','B_Spine2','B_Neck','B_Pelvis']})
 rig.animation_data.action=None;points=None;previous=None;rows=[];cyclic=act.name in ['Standing','Walking','Running','Fidget'];sequence=list(range(len(samples)))*3 if cyclic else [0]*60+list(range(len(samples)))
 for index in sequence:
  M=samples[index];T=M['B_Head']@rig.data.bones['B_Head'].matrix_local.inverted();root=T@rig.data.bones[names[0]].head_local;A=M['B_Pelvis'].translation;B=M['B_Neck'].translation;axis=(B-A).normalized()
  if points is None:
   points=[root]+[T@rig.data.bones[n].tail_local for n in names];previous=[q.copy()for q in points]
  new=[root.copy()]+[points[i]+(points[i]-previous[i])*.90+Vector((0,0,-9.8))/(fps*fps)for i in range(1,4)]
  for iteration in range(12):
   new[0]=root.copy()
   for i,L in enumerate(lengths):
    d=new[i+1]-new[i];cor=d.normalized()*(d.length-L)
    if i==0:new[i+1]-=cor
    else:new[i]+=cor*.5;new[i+1]-=cor*.5
   for i in range(1,4):
    rel=new[i]-A;along=np.clip(rel.dot(axis),0,(B-A).length);center=A+axis*along;radial=new[i]-center;radius=.128
    if radial.length<radius:new[i]=center+radial.normalized()*radius
    back=axis.cross(Vector((1,0,0))).normalized();depth=(new[i]-A).dot(back);new[i]+=back*max(0,.128-depth);new[i].z=max(.025,new[i].z)
  previous,points=points,new
  rows.append([q.copy()for q in new])
 rows=rows[-len(samples):];prev={}
 for f,M,points in zip(times,samples,rows):
  rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(int(f),subframe=float(f%1));rig.animation_data.action=None
  for i,n in enumerate(names):
   pb=rig.pose.bones[n];rb=rig.data.bones[n];T=M['B_Head']@rig.data.bones['B_Head'].matrix_local.inverted();R=T.to_3x3()@rb.matrix_local.to_3x3();R=(R@Vector((0,1,0))).rotation_difference((points[i+1]-points[i]).normalized()).to_matrix()@R;mat=R.to_4x4();mat.translation=points[i];pb.matrix=mat;bpy.context.view_layer.update()
   if n in prev and pb.rotation_quaternion.dot(prev[n])<0:pb.rotation_quaternion=-pb.rotation_quaternion
   prev[n]=pb.rotation_quaternion.copy()
  values={n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names};rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
  for n,(q,l)in values.items():pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  rig.animation_data.action=None
 print('BRAID',act.name,flush=True)
# Helpers already exist; only re-bake their final poses, never distribute the weights twice.
code=(P/'scripts/twist_bones.py').read_text();FA=.6;UA=.5;exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')])
for act in bpy.data.actions:
 if act.name!='Dead':bake_twist(act)
# Envelope samples guard the space between the 30 Hz exported keys.
root=rig.pose.bones['B_Pelvis'];inv=rig.data.bones[root.name].matrix_local.to_3x3().inverted();floor_report={}
for act in bpy.data.actions:
 if act.name=='Dead':continue
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];nf=int(act.frame_range[1]);corr=np.zeros(nf+1);loc=[]
 for f in range(nf+1):sc.frame_set(f);loc.append(root.location.copy())
 for f in np.linspace(0,nf,math.ceil(nf*48/30)+1):
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();dz=max(0,.001-min(v.co.z for v in me.vertices));ev.to_mesh_clear()
  for j in {int(f),min(nf,math.ceil(f))}:corr[j]=max(corr[j],dz)
 for f,l in enumerate(loc):root.location=l+inv@Vector((0,0,float(corr[f])));root.keyframe_insert('location',frame=f)
 floor_report[act.name]=float(corr.max())
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));held={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy(),pb.scale.copy())for pb in rig.pose.bones};rig.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=30;rig.animation_data.action=a
for f in [0,30]:
 for n,(q,l,s)in held.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f);pb.keyframe_insert('scale',frame=f)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
(P/'review/floor_envelope.json').write_text(json.dumps(floor_report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
runpy.run_path(str(P/'scripts/probe_current.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/bind_textures.py'),run_name='__main__')

runpy.run_path(str(P/'scripts/extra_metrics.py'),run_name='__main__')
