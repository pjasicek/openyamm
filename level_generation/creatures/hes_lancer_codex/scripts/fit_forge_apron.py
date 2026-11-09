"""Articulate the rigid forge apron from its belt anchors and keep its plates outside the body."""
import bpy,sys,os,math,json,runpy
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
src=P/'work/forge_hinged.blend';out=P/'work/forge_apron.blend';bpy.ops.wm.open_mainfile(filepath=str(src));r=bpy.data.objects['Rig'];r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
# The apron replaces these belly panels; the greaves already cover the shins below its hem.
for n in ('Apron_Waist','Apron_Shin_L','Apron_Shin_R'):bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
spec=json.loads((S/'armour_lancer.json').read_text());spec['plates']=[p for p in spec['plates'] if not p['name'].startswith('shoulder_lame')];
for plate in spec['plates']:
 if plate['name']=='abdomen_upper':plate['bone']='B_Spine2';plate['shell']['bones']=['B_Spine2'];bpy.data.objects['Arm_'+plate['name']]['bone']='B_Spine2'
(S/'armour_forge.json').write_text(json.dumps(spec,indent=2)+'\n')
for v in bpy.data.objects['Arm_abdomen_upper'].data.vertices:v.co.y-=.025;v.co.z+=.04
for v in bpy.data.objects['Apron_Chest'].data.vertices:v.co.z=1.4275+(v.co.z-1.4275)*.78
anchors={}
for side,sign in [('L',1),('R',-1)]:
 ob=bpy.data.objects['Apron_Hip_'+side]
 for v in ob.data.vertices:v.co.x*=.85;v.co.y-=.035;v.co.z=.797+(v.co.z-.797)*(.188/.215)
 for v in ob.data.vertices:
  v.co.x*=1-.35*min(1,max(0,(v.co.z-.90)/.085));v.co.x+=sign*.012*min(1,max(0,(.86-v.co.z)/.06))
 for v in bpy.data.objects['Apron_Thigh_'+side].data.vertices:v.co.x*=.85;v.co.z=.57+(v.co.z-.57)*.86
 anchors[side]=Vector((sign*.08925,-.468,.985))
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for side in 'LR':
 name='B_ApronHip_'+side;eb=r.data.edit_bones
 if name in eb:eb.remove(eb[name])
 b=eb.new(name);b.head=anchors[side];b.tail=anchors[side]+Vector((0,.08,0));b.parent=eb['B_Pelvis'];b.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
for side in 'LR':
 ob=bpy.data.objects['Apron_Hip_'+side];ob.vertex_groups.clear();ob.vertex_groups.new(name='B_ApronHip_'+side).add(list(range(len(ob.data.vertices))),1,'REPLACE')
clips=['Forge_'+x for x in ('Standing','Walking','Running','Attack','Hit','Fidget','Cast','Death','Dead')]
for clip in clips:
 a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];keys=[]
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.5):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));pelvis=r.pose.bones['B_Pelvis'].matrix@r.data.bones['B_Pelvis'].matrix_local.inverted()
  for side in 'LR':
   leg=pelvis.to_3x3().inverted()@(r.pose.bones[f'B_{side}_Calf'].matrix.translation-r.pose.bones[f'B_{side}_Thigh'].matrix.translation);rest=r.data.bones[f'B_{side}_Calf'].head_local-r.data.bones[f'B_{side}_Thigh'].head_local
   angle=math.atan2(-leg.y,-leg.z)-math.atan2(-rest.y,-rest.z);angle=max(0,min(math.radians(110),angle));world=pelvis@Matrix.Translation(anchors[side])@Matrix.Rotation(-angle,4,'X');armik.set_world(r,'B_ApronHip_'+side,world);keys.append((float(f),'B_ApronHip_'+side,r.pose.bones['B_ApronHip_'+side].matrix_basis.copy()))
 previous={}
 for f,n,m in keys:
  b=r.pose.bones[n];q=m.to_quaternion()
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
# Lift the one-handed carry slightly forward of the apron while the other hand casts.
a=bpy.data.actions['Forge_Cast'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];keys=[]
for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.5):
 bpy.context.scene.frame_set(int(f),subframe=float(f%1));h=armik.W(r,'B_R_Hand');target=h.translation+Vector((0,0,.065));pole=armik.W(r,'B_R_Forearm').translation
 reach=armik.solve(r,'R',target,pole,h.to_3x3());assert reach<.999
 fore,hand,upper=[r.data.bones['B_R_'+n] for n in ('Forearm','Hand','UpperArm')]
 axis=(upper.matrix_local.inverted()@fore.head_local).normalized();_,tw=armik.split_swing_twist(r.pose.bones[upper.name].matrix_basis.to_quaternion(),axis);r.pose.bones['B_R_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*tw)
 axis=(fore.matrix_local.inverted()@hand.head_local).normalized();rel=(r.pose.bones[fore.name].matrix.inverted()@r.pose.bones[hand.name].matrix).to_quaternion();rr=(fore.matrix_local.inverted()@hand.matrix_local).to_quaternion();_,tw=armik.split_swing_twist(rel@rr.inverted(),axis);r.pose.bones['B_R_ForearmTwist'].rotation_quaternion=Quaternion(axis,.5*tw)
 for part in ('UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist'):keys.append((float(f),'B_R_'+part,r.pose.bones['B_R_'+part].matrix_basis.copy()))
previous={}
for f,n,m in keys:
 b=r.pose.bones[n];q=m.to_quaternion()
 if n in previous and q.dot(previous[n])<0:q=-q
 previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(out));sys.argv=['skin_shell.py','--',str(out),str(S/'armour_forge.json'),str(out)];runpy.run_path(str(S/'skin_shell.py'),run_name='__main__')
sys.argv=['armour_gate.py','--',str(out),'forge_apron',str(S/'armour_forge.json'),*clips];runpy.run_path(str(S/'armour_gate.py'),run_name='__main__')
sys.stdout.flush();os._exit(0)
