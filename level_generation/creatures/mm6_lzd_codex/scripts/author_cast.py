"""Author a one-handed palm cast over the existing relaxed stance; preserve the eight delivered actions."""
import bpy,sys,math,json
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_round1.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30
standing=bpy.data.actions['Standing'];rig.animation_data.action=standing;rig.animation_data.action_slot=standing.slots[0];scene.frame_set(0)
base={b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy()) for b in rig.pose.bones}
feet={s:(rig.pose.bones[f'B_{s}_Foot'].head.copy(),rig.pose.bones[f'B_{s}_Foot'].matrix.to_quaternion()) for s in 'LR'}
knees={s:rig.pose.bones[f'B_{s}_Calf'].head.copy() for s in 'LR'}
hips={s:rig.pose.bones[f'B_{s}_Thigh'].head.copy() for s in 'LR'}
foot_forward={s:(rig.pose.bones[f'B_{s}_Toe0'].head-feet[s][0]).normalized() for s in 'LR'}
ua,fa,ha=[rig.pose.bones['B_R_'+n] for n in ['UpperArm','Forearm','Hand']]
u=fa.head-ua.head;v=ha.head-fa.head;hinge_world=u.cross(v).normalized();hinge_local=fa.matrix.to_3x3().inverted()@hinge_world
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
hand=rig.data.bones['B_R_Hand'];kn=[rig.data.bones[f'B_R_Finger{i}'].head_local for i in [1,2,4]]
forward=(kn[1]-hand.head_local).normalized();width=(kn[0]-kn[2]).normalized();normal=width.cross(forward).normalized()
# Resolve palm sign from the actual fitted fingers curling, not the knuckle cross-product sign.
for i in [1,2,4]:rig.pose.bones[f'B_R_Finger{i}'].rotation_quaternion=base[f'B_R_Finger{i}'][0]
bpy.context.view_layer.update();curl=sum((rig.pose.bones[f'B_R_Finger{i}2'].head-rig.data.bones[f'B_R_Finger{i}2'].head_local for i in [1,2,4]),Vector())
if normal.dot(curl)<0:normal=-normal
print('PALM_CURL',list(curl),'NORMAL',list(normal))
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
centre=hand.head_local.lerp(sum(kn,Vector())/3,.65)
pieces=[a.value for a in body.data.attributes['piece'].data];faces=[list(f.vertices) for f in body.data.polygons if all(pieces[i]==4 for i in f.vertices)]
tree=BVHTree.FromPolygons([v.co for v in body.data.vertices],faces);hit,n,_,_=tree.ray_cast(centre+normal*.15,-normal,.3);assert hit is not None
socket=hit+normal*.002
palm_local=hand.matrix_local.to_3x3().inverted()@normal
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');bone=rig.data.edit_bones.new('Socket_Palm_R');bone.head=socket;bone.tail=socket+normal*.06;bone.parent=rig.data.edit_bones['B_R_Hand'];bone.use_deform=False;bpy.ops.object.mode_set(mode='OBJECT')
rig.pose.bones['Socket_Palm_R'].rotation_mode='QUATERNION';base['Socket_Palm_R']=(Quaternion(),Vector(),Vector((1,1,1)))
def ease(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def set_rotation(name,rotation):
 pb=rig.pose.bones[name];m=pb.matrix.copy();m=rotation.to_matrix().to_4x4()@m;m.translation=pb.head.copy();pb.matrix=m;bpy.context.view_layer.update()
def aim(name,child,target):
 pb=rig.pose.bones[name];set_rotation(name,(rig.pose.bones[child].head-pb.head).rotation_difference(target-pb.head))
def plant(side,target,rotation):
 th,ca,ft=[f'B_{side}_{x}' for x in ['Thigh','Calf','Foot']];H=rig.pose.bones[th].head.copy();K=rig.pose.bones[ca].head.copy();A=rig.pose.bones[ft].head.copy();a=(K-H).length;b=(A-K).length;u=(target-H).normalized();d=min((target-H).length,(a+b)*.9999);home_u=(feet[side][0]-hips[side]).normalized();home_pole=knees[side]-hips[side];home_pole=(home_pole-home_u*home_pole.dot(home_u)).normalized();pole=home_pole.lerp(foot_forward[side],amount);pole=(pole-u*pole.dot(u)).normalized();c=np.clip((a*a+d*d-b*b)/(2*a*d),-1,1)
 aim(th,ca,H+a*(u*c+pole*math.sqrt(1-c*c)));aim(ca,ft,target);m=rotation.to_matrix().to_4x4();m.translation=rig.pose.bones[ft].head;rig.pose.bones[ft].matrix=m;bpy.context.view_layer.update()
poses=[];intent=[]
for f in range(43):
 for name,(q,l,s) in base.items():
  pb=rig.pose.bones[name];pb.rotation_quaternion=q;pb.location=l;pb.scale=s
 bpy.context.view_layer.update();rise=ease((f-3)/12);thrust=ease((f-18)/6);recover=ease((f-28)/14);amount=rise*(1-recover)
 pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation+=Vector((-.006,-.030,-.008))*amount;pb.matrix=m;bpy.context.view_layer.update()
 step=ease((f-6)/6)*(1-ease((f-30)/8));lift=0
 if 6<f<12:lift=.025*math.sin(math.pi*(f-6)/6)**2
 if 30<f<38:lift=.025*math.sin(math.pi*(f-30)/8)**2
 if f not in [0,42]:
  for side,(target,q) in feet.items():plant(side,target+(Vector((0,-.08*step,lift)) if side=='L' else Vector()),q)
 set_rotation('B_Spine',Quaternion((1,0,0),math.radians(3)*amount));set_rotation('B_Spine2',Quaternion((0,0,1),math.radians(-6)*amount))
 set_rotation('B_R_UpperArm',Quaternion((0,0,1),math.radians(-25+15*thrust)*amount)@Quaternion((1,0,0),math.radians(-45-30*thrust)*amount))
 pb=rig.pose.bones['B_R_Forearm'];axis=pb.matrix.to_3x3()@hinge_local;set_rotation(pb.name,Quaternion(axis,math.radians(55-40*thrust)*amount))
 pb=rig.pose.bones['B_R_Hand'];current=(pb.matrix.to_3x3()@palm_local).normalized();correction=current.rotation_difference(Vector((0,-1,0)));angle=min(correction.angle,math.radians(55));set_rotation(pb.name,Quaternion(correction.axis,angle*amount))
 for pb in rig.pose.bones:
  if pb.name.startswith('B_R_Finger'):pb.rotation_quaternion=base[pb.name][0].slerp(Quaternion(),amount*.8)
 bpy.context.view_layer.update()
 poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy()) for b in rig.pose.bones})
 intent.append({'frame':f,'right_wrist':list(rig.pose.bones['B_R_Hand'].head),'right_elbow':list(rig.pose.bones['B_R_Forearm'].head),'palm':list(rig.pose.bones['Socket_Palm_R'].head),'palm_target_dot':float((rig.pose.bones['B_R_Hand'].matrix.to_3x3()@palm_local).normalized().dot(Vector((0,-1,0)))),'left_foot_target':list(feet['L'][0]+Vector((0,-.08*step,lift)))})
act=bpy.data.actions.new('Cast');act.use_fake_user=True;rig.animation_data.action=act
for f,pose in enumerate(poses):
 for name,(q,l,s) in pose.items():
  pb=rig.pose.bones[name];pb.rotation_quaternion=q;pb.location=l;pb.scale=s
  for channel in ['rotation_quaternion','location','scale']:pb.keyframe_insert(channel,frame=f)
act.use_frame_range=True;act.frame_start=0;act.frame_end=42
# Split each side's continuous wrist/upper-arm roll onto its existing twist bones, exactly as the other clips.
for side in 'LR':
 fa=rig.data.bones[f'B_{side}_Forearm'];ha=rig.data.bones[f'B_{side}_Hand'];ua=rig.data.bones[f'B_{side}_UpperArm'];axes=[(fa.matrix_local.inverted()@ha.head_local).normalized(),(ua.matrix_local.inverted()@fa.head_local).normalized()];angles=[]
 for f in range(43):
  scene.frame_set(f);rel=(rig.pose.bones[fa.name].matrix.inverted()@rig.pose.bones[ha.name].matrix).to_quaternion();rest=(fa.matrix_local.inverted()@ha.matrix_local).to_quaternion();qs=[rel@rest.inverted(),rig.pose.bones[ua.name].matrix_basis.to_quaternion()];angles.append([2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w) for q,axis in zip(qs,axes)])
 for f,values in enumerate(np.unwrap(np.array(angles),axis=0)):
  for kind,axis,value,factor in zip(['ForearmTwist','UpperArmTwist'],axes,values,[.5,-.5]):
   pb=rig.pose.bones[f'B_{side}_{kind}'];pb.rotation_quaternion=Quaternion(axis,float(value*factor));pb.keyframe_insert('rotation_quaternion',frame=f)
for layer in act.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.frame_set(0);rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master.blend'))
(P/'work/cast_intent.json').write_text(json.dumps({'duration':1.4,'frames':intent,'palm_normal_hand_local':list(palm_local),'socket_surface_rest':list(hit),'socket_offset_m':.002,'hinge_axis_forearm_local':list(hinge_local),'authoring':'Raised right claw then forward palm push; low carried bow; 20% scale pelvic transfer, single 8 cm step, return to Standing.'},indent=2))
rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];common.workbench_clay(scene,textured=True)
for f in [0,9,15,20,24,33,42]:
 scene.frame_set(f);common.render_views(str(P/f'review/cast_key_{f}'),.87,2.45,views=('front','left','three_quarter'),resolution=(560,650))
print('CAST_AUTHORED',len(poses),'frames',len(rig.data.bones),'bones',intent[21])
