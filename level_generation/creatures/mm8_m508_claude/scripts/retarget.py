"""Sample the accepted Djinn, then fit its world rotations to the MM8 effect torso.
Arms copy physical directions with a minimal rest-frame swing; torso copies rotation deltas.
No Djinn geometry, clothing, palette or death remains enter this model.
"""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];FPS=30
MAPPING={'Hips':'B_Pelvis','Spine':'B_Spine','Spine1':'B_Spine1','Spine2':'B_Spine2','Neck':'B_Neck','Head':'B_Head'}
for side,short in [('Left','L'),('Right','R')]:
 for ours,theirs in [('Shoulder','Clavicle'),('Arm','UpperArm'),('ForeArm','Forearm'),('Hand','Hand')]:MAPPING[side+ours]='B_'+short+'_'+theirs
ROLES=['Standing','Walking','Running','Attack','Cast','Hit','Fidget']
source=P.parent/'mm6_djn_claude/export/mm6_djn.glb'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source))
src=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene
rest={n:(src.matrix_world@src.data.bones[s].matrix_local).to_quaternion().copy() for n,s in MAPPING.items()}
fps=sc.render.fps/sc.render.fps_base
sampled={}
for role in ROLES:
 actions=[a for a in bpy.data.actions if a.name==role or a.name.startswith(role+'_') or a.name.startswith(role+'.')]
 assert len(actions)==1,(role,[a.name for a in bpy.data.actions])
 act=actions[0];src.animation_data_create();src.animation_data.action=act
 if act.slots:src.animation_data.action_slot=act.slots[0]
 f0,f1=act.frame_range;duration=(f1-f0)/fps;count=round(duration*FPS);keys=[]
 for f in range(count+1):
  sf=f0+f/count*(f1-f0);sc.frame_set(math.floor(sf),subframe=sf%1);bpy.context.view_layer.update()
  keys.append({n:list((src.matrix_world@src.pose.bones[s].matrix).to_quaternion()) for n,s in MAPPING.items()})
 sampled[role]={'duration':duration,'keys':keys}
print('SOURCE',[(k,v['duration']) for k,v in sampled.items()])
(P/'work/djinn_motion.json').write_text(json.dumps({'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rest':{n:list(q) for n,q in rest.items()},'clips':sampled}))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/figure.blend'));rig=bpy.data.objects['AirElemental_Rig'];sc=bpy.context.scene;sc.render.fps=FPS
our_rest={n:rig.data.bones[n].matrix_local.to_quaternion() for n in MAPPING}
arms=[s+part for s in ['Left','Right'] for part in ['Arm','ForeArm','Hand']]
align={n:(our_rest[n]@Vector((0,1,0))).rotation_difference(rest[n]@Vector((0,1,0))) if n in arms else Quaternion() for n in MAPPING}
order=[b.name for b in rig.data.bones if b.name in MAPPING]
# Sorting by hierarchy prevents applying the forearm before its shoulder.
order.sort(key=lambda n:len(rig.data.bones[n].parent_recursive))

def split_twist(q,axis):
 axis=axis.normalized();v=Vector((q.x,q.y,q.z));twist=Quaternion((q.w,*(axis*v.dot(axis))))
 if twist.magnitude<1e-6:twist=Quaternion()
 else:twist.normalize()
 return q@twist.inverted(),twist

def limit_relative(q,axis,twist_limit,swing_limit=math.pi):
 swing,twist=split_twist(q,axis);a=2*math.atan2(Vector((twist.x,twist.y,twist.z)).dot(axis),twist.w);a=(a+math.pi)%(2*math.pi)-math.pi
 if swing.w<0:swing.negate()
 if swing.angle>swing_limit:swing=Quaternion().slerp(swing,swing_limit/swing.angle)
 return swing@Quaternion(axis,max(-twist_limit,min(twist_limit,a)))

def smooth_source(data):
 # The selected Djinn has a fast axial change at 0.667 s. Spread it over nearby keys before fitting.
 result=[]
 for i in range(len(data)):
  row={}
  for n in MAPPING:
   base=Quaternion(data[i][n]);values=Vector((0.,0.,0.,0.));total=0.
   for k in range(max(0,i-6),min(len(data),i+7)):
    q=Quaternion(data[k][n]);weight=math.exp(-.5*((k-i)/2.2)**2)
    if base.dot(q)<0:q.negate()
    values+=Vector(q)*weight;total+=weight
   q=Quaternion(values/total);q.normalize();row[n]=list(q)
  result.append(row)
 return result

for role,data in sampled.items():
 rig.animation_data_clear()
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 act=bpy.data.actions.new(role);act.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=act
 previous={}
 fitted=smooth_source(data['keys']) if role in ['Attack','Cast'] else data['keys']
 for f,key in enumerate(fitted):
  sc.frame_set(f+1)
  for n in order:
   pb=rig.pose.bones[n];q=Quaternion(key[n])@rest[n].inverted()@align[n]@our_rest[n]
   if role in ['Attack','Cast'] and n in arms:
    side='Left' if n.startswith('Left') else 'Right';un=side+'Arm';fn=side+'ForeArm';hn=side+'Hand'
    if n==un:
     parent=pb.parent;neutral=parent.matrix.to_quaternion()@parent.bone.matrix_local.to_quaternion().inverted()@our_rest[n]
     q=neutral@limit_relative(neutral.inverted()@q,Vector((0,1,0)),math.radians(55))
    elif n==fn:
     uq=rig.pose.bones[un].matrix.to_quaternion();ur=(rig.data.bones[fn].head_local-rig.data.bones[un].head_local).normalized();fr=(rig.data.bones[hn].head_local-rig.data.bones[fn].head_local).normalized();hinge=ur.cross(fr).normalized();delta=uq@our_rest[un].inverted();h=delta@hinge;u=delta@ur;fdir=q@Vector((0,1,0));flex=math.atan2(h.dot(u.cross(fdir)),u.dot(fdir));flex=max(math.radians(8),min(math.radians(130),flex));rest_flex=ur.angle(fr)
     q=Quaternion(h,flex-rest_flex)@delta@our_rest[fn]
    else:
     neutral=rig.pose.bones[fn].matrix.to_quaternion()@our_rest[fn].inverted()@our_rest[hn]
     q=neutral@limit_relative(neutral.inverted()@q,Vector((0,1,0)),math.radians(34),math.radians(65))
   m=q.to_matrix().to_4x4();m.translation=pb.head.copy();pb.matrix=m;bpy.context.view_layer.update()
   qq=pb.rotation_quaternion.copy()
   if n in previous and qq.dot(previous[n])<0:qq.negate()
   pb.rotation_quaternion=qq;previous[n]=qq.copy();pb.keyframe_insert('rotation_quaternion',frame=f+1)
  # Keep native open, softly curled hands through the release.
  for pb in rig.pose.bones:
   if 'Hand' in pb.name and pb.name[-1:].isdigit():
    pb.rotation_quaternion=Quaternion((1,0,0),.04 if pb.name.endswith('1') else .09)
    pb.keyframe_insert('rotation_quaternion',frame=f+1)
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 print('RETARGET',role,len(data['keys']))
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anim.blend'))
