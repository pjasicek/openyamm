"""Constrain the library fall to the native paired legs and hands ahead of the body."""
import bpy,sys,math,json,runpy,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;names=[b.name for b in rig.pose.bones]
code=(P/'scripts/motion.py').read_text();exec(code[code.index('def action'):code.index('baseline=')]);a=bpy.data.actions['Death'];frames=[sample(a,f)for f in range(int(a.frame_range[1])+1)];nf=len(frames)-1
for f,p in enumerate(frames):
 put(p)
 # Remove axial roll inherited from the broad source skeleton while retaining its lean and timing.
 Pm=wm('B_Pelvis');pel=Pm.translation.copy();up=(rig.pose.bones['B_Neck'].head-pel).normalized();side=wm('B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((1,0,0));side=(side-up*side.dot(up)).normalized();desired=Vector((1,0,0));desired=(desired-up*desired.dot(up)).normalized();angle=math.atan2(up.dot(side.cross(desired)),side.dot(desired));Pm=Quaternion(up,angle).to_matrix().to_4x4()@Pm;Pm.translation=pel;rig.pose.bones['B_Pelvis'].matrix=Pm;bpy.context.view_layer.update()
 pelvis=rig.pose.bones['B_Pelvis'].head.copy();head=rig.pose.bones['B_Head'].head.copy();neck=rig.pose.bones['B_Neck'].head.copy();up=(neck-pelvis).normalized();lean=math.degrees(up.angle(Vector((0,0,1))));w=smooth((lean-15)/55);back=-up
 for sd,sign in [('L',1),('R',-1)]:
  th,ca,ft=[f'B_{sd}_'+n for n in ['Thigh','Calf','Foot']];H=rig.pose.bones[th].head.copy();K=rig.pose.bones[ca].head.copy();A=rig.pose.bones[ft].head.copy();aa=(K-H).length;bb=(A-K).length;rest=rig.data.bones[ft].head_local.copy();rest.x=sign*.102;rest.z+=.002;end=H+back*(aa+bb)*.991;end.z=max(.060,end.z);target=rest.lerp(end,w)
  # The native paired legs stay under the wrap. Limit the deep source crouch before it becomes a fold.
  dz=H.z-target.z;minimum=(aa+bb)*.84
  if (target-H).length<minimum:
   direction=Vector((-up.x,-up.y,0))
   if direction.length<.01:direction=Vector((0,1,0))
   direction.normalize();target.x=H.x+direction.x*math.sqrt(max(0,minimum*minimum-dz*dz));target.y=H.y+direction.y*math.sqrt(max(0,minimum*minimum-dz*dz))
  u=(target-H).normalized();d=min((target-H).length,(aa+bb)*.999);v=Vector((0,-1,0)).lerp(Vector((0,0,-1)),w);v=(v-u*v.dot(u)).normalized();c=(aa*aa+d*d-bb*bb)/(2*aa*d);E=H+aa*(u*c+v*math.sqrt(max(0,1-c*c)));aim(th,ca,E-H);aim(ca,ft,target-rig.pose.bones[ca].head)
  R=Quaternion(Vector((1,0,0)),math.pi*w).to_matrix()@rig.data.bones[ft].matrix_local.to_3x3();rotation(ft,R)
  # Source arm anticipation is retained, then both hands reach beside and ahead of the face.
  U,F,Hn=[f'B_{sd}_'+n for n in ['UpperArm','Forearm','Hand']];S=rig.pose.bones[U].head.copy();E=rig.pose.bones[F].head.copy();W=rig.pose.bones[Hn].head.copy();sideAxis=(wm('B_Spine2').to_3x3()@rig.data.bones['B_Spine2'].matrix_local.to_3x3().inverted()@Vector((1,0,0))).normalized();target=head+sideAxis*(sign*.31)+up*.08-Vector((0,0,.045));target.z=max(.065,target.z);target=W.lerp(target,smooth(f/6));sidegap=(target-head).dot(sideAxis)*sign;target+=sideAxis*sign*max(0,.26-sidegap);aa=(E-S).length;bb=(W-E).length;u=(target-S).normalized();d=min((target-S).length,(aa+bb)*.995);v=sideAxis*sign+Vector((0,0,.2));v=(v-u*v.dot(u)).normalized();c=(aa*aa+d*d-bb*bb)/(2*aa*d);K=S+aa*(u*c+v*math.sqrt(max(0,1-c*c)));aim(U,F,K-S);aim(F,Hn,target-rig.pose.bones[F].head);anatomical(sd)
 # Ground the fitted body before fitting its garment.
 bpy.context.view_layer.update();ob=bpy.data.objects['Body'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();pieces=ob.data.attributes['piece'].data;floor=min(v.co.z for v in mesh.vertices if pieces[v.index].value not in [1,3]);ev.to_mesh_clear();M=wm('B_Pelvis');M.translation.z+=max(0,.003-floor);rig.pose.bones['B_Pelvis'].matrix=M;bpy.context.view_layer.update()
 # Aim the open fingers past the face, with the palms on the eventual floor.
 for sd,sign in [('L',1),('R',-1)]:
  hand='B_'+sd+'_Hand';B=rig.data.bones;fw=(B[f'B_{sd}_Finger21'].head_local-B[hand].head_local).normalized();ac=(B[f'B_{sd}_Finger11'].head_local-B[f'B_{sd}_Finger41'].head_local).normalized();no=fw.cross(ac).normalized()*sign;ac=no.cross(fw).normalized();basis=Matrix([fw,ac,no]).transposed();df=up.normalized();dn=Vector((0,-1,0)).lerp(Vector((0,0,-1)),smooth(lean/80));dn=(dn-df*dn.dot(df)).normalized();da=dn.cross(df).normalized();R=Matrix([df,da,dn]).transposed()@basis.inverted()@B[hand].matrix_local.to_3x3();R=wm(hand).to_quaternion().slerp(R.to_quaternion(),smooth(f/10)).to_matrix();rotation(hand,R)
 frames[f]=get()
action(None);bpy.data.actions.remove(a);a=bpy.data.actions.new('Death');a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=nf;action(a);prev={} 
for f,p in enumerate(frames):
 for n,(q,l,s)in p.items():
  if True:
   pb=rig.pose.bones[n]
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb.rotation_quaternion=q;pb.location=l;pb.scale=s;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f);pb.keyframe_insert('scale',frame=f)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
runpy.run_path(str(P/'scripts/final_skirt.py'),run_name='__main__')
