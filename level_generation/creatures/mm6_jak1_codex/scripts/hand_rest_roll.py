"""Match the model's bound palms to the humanoid source frame before retargeting."""
import bpy,json,math
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1]
ANGLES={'R':137.,'L':-140.}
def restore(body,rig):
 attr=body.data.attributes.get('round2_handroll_rest')
 if attr:
  for v,a in zip(body.data.vertices,attr.data):v.co=a.vector
 if 'round2_finger_rest' in rig:
  rows=json.loads(rig['round2_finger_rest']);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
  for name,row in rows.items():
   b=rig.data.edit_bones[name];b.use_connect=False;b.matrix=Matrix(row['matrix']);b.length=row['length']
  bpy.ops.object.mode_set(mode='OBJECT')
 body.data.update()
def apply(body,rig):
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();me=body.data
 if not me.attributes.get('round2_handroll_rest'):
  a=me.attributes.new('round2_handroll_rest','FLOAT_VECTOR','POINT')
  for v,d in zip(me.vertices,a.data):d.vector=v.co
 bones={n:{'matrix':[list(r)for r in b.matrix_local],'length':b.length}for n,b in rig.data.bones.items()if '_Finger'in n}
 if 'round2_finger_rest'not in rig:rig['round2_finger_rest']=json.dumps(bones)
 names={g.index:g.name for g in body.vertex_groups};transforms={};report={}
 for side,degrees in ANGLES.items():
  hand=rig.data.bones[f'B_{side}_Hand'];elbow=rig.data.bones[f'B_{side}_Forearm'].head_local;wrist=hand.head_local
  knuckles=sum((rig.data.bones[f'B_{side}_Finger{i}'].head_local for i in range(5)),Vector())/5;axis=(knuckles-wrist).normalized();rotation=Matrix.Rotation(math.radians(degrees),4,axis);C=Matrix.Translation(wrist)@rotation@Matrix.Translation(-wrist);transforms[side]=C
  arm_axis=wrist-elbow
  for v in me.vertices:
   weight=sum(g.weight for g in v.groups if names[g.group].startswith((f'B_{side}_Hand',f'B_{side}_Finger',f'B_{side}_Forearm')))
   if weight<.05:continue
   h=sum(g.weight for g in v.groups if names[g.group].startswith((f'B_{side}_Hand',f'B_{side}_Finger')))
   t=max(0,min(1,(v.co-elbow).dot(arm_axis)/arm_axis.length_squared));u=max(0,min(1,(t-.15)/.75));u=u*u*(3-2*u)
   if h>.15:u=1
   center=wrist if h>.15 else elbow+arm_axis*t;v.co=center+Matrix.Rotation(math.radians(degrees)*u,3,axis)@(v.co-center)
  local=hand.matrix_local.inverted()@C@hand.matrix_local;normal=hand.matrix_local.to_3x3().inverted()@(rotation.to_3x3()@Vector((0,1,0)))
  report[side]={'degrees':degrees,'palm_local':list(normal),'hand_transform':[list(r)for r in local]}
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 for name,row in bones.items():
  side=name.split('_')[1];b=rig.data.edit_bones[name];b.use_connect=False;b.matrix=transforms[side]@Matrix(row['matrix']);b.length=row['length']
 bpy.ops.object.mode_set(mode='OBJECT');me.update();bpy.context.view_layer.update()
 # Grip coordinates change with the corrected palm; the solved finger-local curls remain the same.
 for side,suffix in [('R',''),('L','_left')]:
  path=P/f'work/grip_pose{suffix}.json';original=P/f'work/grip_pose{suffix}_unrolled.json'
  if not original.exists():original.write_text(path.read_text())
  data=json.loads(original.read_text());C=Matrix(report[side]['hand_transform']);data['handle_centre_hand_local']=list(C@Vector(data['handle_centre_hand_local']));data['handle_axis_hand_local']=list(C.to_3x3()@Vector(data['handle_axis_hand_local']));path.write_text(json.dumps(data,indent=2))
 (P/'work/hand_rest_roll.json').write_text(json.dumps(report,indent=2));print('HAND REST ROLL',ANGLES,flush=True)
