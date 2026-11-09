"""Bake the fitted two-hand constraint at 120 Hz so exported interpolation keeps the shaft inside both fists."""
import bpy,numpy as np,json,math
from mathutils import Vector,Matrix,Quaternion
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_anatomy.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;G=json.loads((P/'work/grip_pose_L.json').read_text());localC=Vector(G['handle_centre_hand_local']);localA=Vector(G['handle_axis_hand_local']);names=list(r.pose.bones.keys())
def update():bpy.context.view_layer.update()
def M(n):return r.pose.bones[n].matrix.copy()
def setmat(n,m):r.pose.bones[n].matrix=m;r.pose.bones[n].scale=(1,1,1);update()
def aim(n,c,d):
 m=M(n);q=(M(c).translation-m.translation).normalized().rotation_difference(d.normalized());setmat(n,Matrix.LocRotScale(m.translation,q@m.to_quaternion(),Vector((1,1,1))))
def ik(target,rot):
 a,b,c=['B_L_'+n for n in ['UpperArm','Forearm','Hand']];h,k,e=[M(n).translation for n in [a,b,c]];la=(k-h).length;lb=(e-k).length;u=(target-h).normalized();d=min((target-h).length,(la+lb)*.999);pol=k-h;pol-=u*pol.dot(u);pol.normalize();cosine=max(-1,min(1,(la*la+d*d-lb*lb)/(2*la*d)));kn=h+la*(u*cosine+pol*math.sqrt(1-cosine*cosine));aim(a,b,kn-h);aim(b,c,target-M(b).translation);setmat(c,Matrix.LocRotScale(M(c).translation,rot.to_quaternion(),Vector((1,1,1))))
poses={}
for a in list(bpy.data.actions):
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
 for i in range(int(a.frame_range[1]*4)+1):
  f=i/4;sc.frame_set(int(f),subframe=f%1)
  if a.name!='Dead' and not(a.name=='Death' and f>=5):
   am=M('Axe')@r.data.bones['Axe'].matrix_local.inverted();origin=am.translation;axis=(am.to_3x3()@Vector((0,0,1))).normalized();hand=M('B_L_Hand');c=hand@localC;c=origin+axis*((c-origin).dot(axis));rot=(hand.to_3x3()@localA).normalized().rotation_difference(axis).to_matrix()@hand.to_3x3();ik(c-rot@localC,rot)
  for s in 'RL':
   un,fn,hn=['B_'+s+'_'+n for n in ['UpperArm','Forearm','Hand']];U,F,H=[M(n).translation for n in [un,fn,hn]];up=(F-U).normalized();fo=(H-F).normalized();ru=(r.data.bones[fn].head_local-r.data.bones[un].head_local).normalized();bend=Vector((0,-1,0));bend=(bend-ru*bend.dot(ru)).normalized();normal=(M(un).to_3x3()@r.data.bones[un].matrix_local.to_3x3().inverted()@ru.cross(bend)).normalized();want=up.cross(fo).normalized();angle=math.atan2(up.dot(normal.cross(want)),normal.dot(want));fore=M(fn);upper=M(un);setmat(un,Matrix.LocRotScale(U,(Matrix.Rotation(angle,3,up)@upper.to_3x3()).to_quaternion(),Vector((1,1,1))));setmat(fn,fore)
   ax=(r.data.bones[un].matrix_local.inverted()@r.data.bones[fn].head_local).normalized();q=r.pose.bones[un].rotation_quaternion;tw=(2*math.atan2(Vector(q[1:]).dot(ax),q.w)+math.pi)%(2*math.pi)-math.pi;r.pose.bones['B_'+s+'_UpperArmTwist'].rotation_quaternion=Quaternion(ax,-.5*tw);update()
  rows.append({n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy()) for n in names})
 poses[a.name]=rows
sc.render.fps=120;sc.render.fps_base=1
for name,rows in poses.items():
 bpy.data.actions.remove(bpy.data.actions[name]);a=bpy.data.actions.new(name);a.use_fake_user=True;r.animation_data.action=a;a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1;prev={}
 for f,row in enumerate(rows):
  for n,(q,l) in row.items():
   q=q.copy()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_motion.blend'))
