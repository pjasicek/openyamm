"""Final anatomical hinge and flat-sole fit; retain UVs and measured shaft targets."""
import bpy,json,math
import numpy as np
from mathutils import Vector,Matrix,Quaternion
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
names=[x.name for x in r.pose.bones];rest=np.array([tuple(v.co) for v in b.data.vertices]);feet={}
for s,sign in [('R',-1),('L',1)]:
 ids=np.where((rest[:,2]<.14)&(rest[:,0]*sign>0))[0];mid=np.median(rest[ids,1]);feet[s]=[ids[rest[ids,1]>=mid],ids[rest[ids,1]<mid]]
def update():bpy.context.view_layer.update()
def M(n):return r.pose.bones[n].matrix.copy()
def setmat(n,m):r.pose.bones[n].matrix=m;r.pose.bones[n].scale=(1,1,1);update()
def aim(n,c,d):
 m=M(n);delta=(M(c).translation-m.translation).normalized().rotation_difference(d.normalized()).to_matrix();rot=delta@m.to_3x3();setmat(n,Matrix.LocRotScale(m.translation,rot.to_quaternion(),Vector((1,1,1))))
def ik(s,target,rot):
 a,c,d=['B_'+s+'_'+n for n in ['Thigh','Calf','Foot']];h,k,e=[M(n).translation for n in [a,c,d]];la=(k-h).length;lb=(e-k).length;u=(target-h).normalized();distance=min((target-h).length,(la+lb)*.999);pole=k-h;pole-=u*pole.dot(u);pole.normalize();cosine=max(-1,min(1,(la*la+distance*distance-lb*lb)/(2*la*distance)));k=h+la*(u*cosine+pole*math.sqrt(1-cosine*cosine));aim(a,c,k-h);aim(c,d,target-M(c).translation);setmat(d,Matrix.LocRotScale(M(d).translation,rot.to_quaternion(),Vector((1,1,1))))
def co():
 e=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();x=np.array([tuple(v.co) for v in m.vertices]);e.to_mesh_clear();return x
corrected={};report={}
for a in list(bpy.data.actions):
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[];rolls=[]
 for f in range(int(a.frame_range[0]),int(a.frame_range[1])+1):
  sc.frame_set(f)
  for s in 'RL':
   un,fn,hn=['B_'+s+'_'+n for n in ['UpperArm','Forearm','Hand']];U,F,H=[M(n).translation for n in [un,fn,hn]];up=(F-U).normalized();fo=(H-F).normalized();ru=(r.data.bones[fn].head_local-r.data.bones[un].head_local).normalized();bend=Vector((0,-1,0));bend=(bend-ru*bend.dot(ru)).normalized();rot=M(un).to_3x3()@r.data.bones[un].matrix_local.to_3x3().inverted();normal=(rot@ru.cross(bend)).normalized();want=up.cross(fo).normalized();angle=math.atan2(up.dot(normal.cross(want)),normal.dot(want));fore=M(fn);upper=M(un);upperRot=Matrix.Rotation(angle,3,up)@upper.to_3x3();setmat(un,Matrix.LocRotScale(U,upperRot.to_quaternion(),Vector((1,1,1))));setmat(fn,fore);rolls.append(math.degrees(angle))
   ax=(r.data.bones[un].matrix_local.inverted()@r.data.bones[fn].head_local).normalized();q=r.pose.bones[un].rotation_quaternion;tw=(2*math.atan2(Vector(q[1:]).dot(ax),q.w)+math.pi)%(2*math.pi)-math.pi;r.pose.bones['B_'+s+'_UpperArmTwist'].rotation_quaternion=Quaternion(ax,-.5*tw);update()
  if a.name in ['Standing','Fidget']:
   for s in 'RL':
    fn='B_'+s+'_Foot'
    for _ in range(5):
     p=co();heel,toe=[Vector(p[g[np.argmin(p[g,2])]]) for g in feet[s]];line=toe-heel;flat=Vector((line.x,line.y,0));delta=line.normalized().rotation_difference(flat.normalized()).to_matrix();old=M(fn);new=delta@old.to_3x3();ik(s,old.translation,new);p=co();z=min(float(p[g,2].min()) for g in feet[s]);old=M(fn);target=old.translation.copy();target.z-=z;ik(s,target,old.to_3x3())
  rows.append({n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy()) for n in names})
 corrected[a.name]=rows;report[a.name]={'upperarm_hinge_roll_correction_degrees':[min(rolls),max(rolls)]}
# The spell gesture pauses in its raised chamber before the forward release; it is a distinct action from Attack.
old=corrected['Cast'];corrected['Cast']=old[:14]+[old[13]]*8+old[14:]
for name,rows in corrected.items():
 old=bpy.data.actions[name];bpy.data.actions.remove(old);a=bpy.data.actions.new(name);a.use_fake_user=True;r.animation_data.action=a;a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1;prev={}
 for f,row in enumerate(rows):
  for n,(q,l) in row.items():
   q=q.copy()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();pb=r.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.scale=(1,1,1);pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_anatomy.blend'));(P/'review/anatomy_corrections.json').write_text(json.dumps(report,indent=2))
