"""Secondary rigid prop drop during StaffDeath1; the library supplies the character fall."""
import bpy,math,json
import numpy as np
from mathutils import Vector,Matrix,Quaternion

def bake_staff_drop(rig,body,P):
 sc=bpy.context.scene;fps=sc.render.fps;pb=rig.pose.bones['Staff'];pb.rotation_mode='QUATERNION';bone=rig.data.bones['Staff'];group=body.vertex_groups['Staff'].index;inv=(rig.matrix_world@bone.matrix_local).inverted();co=[inv@body.matrix_world@v.co for v in body.data.vertices if any(g.group==group and g.weight>.5 for g in v.groups)]
 def action(a):
  rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 def at(f):sc.frame_set(int(f),subframe=float(f-int(f)))
 for a in bpy.data.actions:
  action(a)
  for f in [0,int(a.frame_range[1])]:
   at(f);pb.matrix_basis.identity();pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 death=bpy.data.actions['Death'];action(death)
 # Open before the shaft separates; a closed fist traps the lower grip collar.
 grip=json.loads((P/'work/grip_pose.json').read_text())['finger_local'];thumb_open=Quaternion(json.loads((P/'work/thumb_release.json').read_text())['target_quaternion'])
 for f in range(int(death.frame_range[1])+1):
  at(f);u=max(0,min(1,(f/fps-.12)/.13));u=u*u*(3-2*u)
  for name,value in grip.items():
   finger=rig.pose.bones[name];q=Quaternion(value);final=Quaternion().slerp(q,.45)
   if name.startswith('B_R_Finger0'):
    opened=q.slerp(thumb_open,u) if name=='B_R_Finger0' else q
    v=max(0,min(1,(f/fps-.35)/.15));v=v*v*(3-2*v);finger.rotation_quaternion=opened.slerp(final,v)
   else:finger.rotation_quaternion=q.slerp(final,u)
   finger.keyframe_insert('rotation_quaternion',frame=f)
 release=.25;rf=round(release*fps);at(rf-12);prior=(rig.matrix_world@pb.matrix).copy();at(rf);start=(rig.matrix_world@pb.matrix).copy();velocity=(start.translation-prior.translation)/(12/fps);correction=json.loads((P/'work/staff_release_velocity.json').read_text())['velocity_xy_mps'] if (P/'work/staff_release_velocity.json').exists() else [0,0];velocity.x+=correction[0];velocity.y+=correction[1];at(death.frame_range[1]);pel=(rig.matrix_world@rig.pose.bones['B_Pelvis'].matrix).translation;endrot=Matrix(((1,0,0),(0,0,-1),(0,1,0))).transposed();end=Vector((pel.x-.80,pel.y-.10,0));z0=start.to_3x3().col[2].normalized();zend=Vector((0,1,0));endbase=z0.rotation_difference(zend).to_matrix()@start.to_3x3();v=endbase.col[0];wanted=endrot.col[0];roll=math.atan2(v.cross(wanted).dot(zend),v.dot(wanted));duration=.60;first_contact=None;poses=[]
 for f in range(int(death.frame_range[1])+1):
  at(f)
  if f<=rf:pb.matrix_basis.identity()
  else:
   t=f/fps-release;u=min(1,t/duration);ease=u*u*(3-2*u);axis=z0.lerp(zend,ease).normalized();rot=Quaternion(axis,roll*ease).to_matrix()@z0.rotation_difference(axis).to_matrix()@start.to_3x3();ground=.003-min((rot@v).z for v in co);position=(2*u**3-3*u*u+1)*start.translation+(u**3-2*u*u+u)*duration*velocity+(-2*u**3+3*u*u)*end;fall=start.translation.z+velocity.z*t-4.905*t*t
   if fall<=ground and first_contact is None:first_contact=f/fps
   position.x+=.06*math.sin(math.pi*min(1,t/.20));position.z=max(ground,fall) if u<1 else ground;matrix=rot.to_4x4();matrix.translation=position;pb.matrix=rig.matrix_world.inverted()@matrix
  poses.append((pb.rotation_quaternion.copy(),pb.location.copy()))
 for f,(q,l) in enumerate(poses):pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 action(bpy.data.actions['Dead']);q,l=poses[-1]
 for f in range(int(bpy.data.actions['Dead'].frame_range[1])+1):pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
 # Parent hand and torso are identical at the Death/Dead boundary.
 for a in bpy.data.actions:
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for curve in bag.fcurves:
      if '"Staff"' in curve.data_path:
       for k in curve.keyframe_points:k.interpolation='LINEAR'
 rig.animation_data.action=None
 (P/'work/staff_drop.json').write_text(json.dumps({'release_seconds':release,'first_floor_contact_seconds':first_contact,'settled_seconds':release+duration,'library_body_clip':'StaffDeath1','method':'Rigid prop gravity fall with inherited release velocity, eased orientation and floor contact; hand releases while the library body falls.'},indent=2))
