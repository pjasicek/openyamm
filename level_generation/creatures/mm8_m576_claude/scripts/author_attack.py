"""Native reverse-grip lift and downward stab with a continuous shoulder arc and a fixed fitted wrist."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=src);rig=bpy.data.objects['Rig'];sc=bpy.context.scene
A=bpy.data.actions['Standing'];rig.animation_data.action=A;rig.animation_data.action_slot=A.slots[0];sc.frame_set(0);rest={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
G=json.loads((P/'work/grip_pose.json').read_text());axis=-Vector(G['handle_axis_hand_local']).normalized()
keys=[(0,0),(24,-100),(25.5,-100),(34.5,-18),(37,-18),(48,0)]
def angle(f):
 for (fa,a),(fb,b) in zip(keys,keys[1:]):
  if f<=fb:
   t=(f-fa)/(fb-fa);t=t*t*(3-2*t);return a+(b-a)*t
 return 0
poses=[];probes=[]
for i in range(193):
 f=i/4;rig.animation_data.action=None
 for n,m in rest.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();w=math.sin(math.pi*f/48)**2
 # Follow the native forward shoulder lift; the fist keeps the same anatomical wrist pose throughout.
 for name,deg,axisworld in [('B_Spine',6*w,(1,0,0)),('B_L_UpperArm',angle(f),(1,0,0)),('B_R_UpperArm',-12*w,(1,0,0))]:
  M=armik.W(rig,name);pivot=M.translation.copy();M=Matrix.Rotation(math.radians(deg),4,Vector(axisworld))@M;M.translation=pivot;armik.set_world(rig,name,M)
 poses.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
 if i%12==0:probes.append({'time':f/30,'wrist':list(armik.W(rig,'B_L_Hand').translation),'tip_direction':list(armik.W(rig,'B_L_Hand').to_3x3()@axis)})
a=bpy.data.actions.get('Attack')
if a:bpy.data.actions.remove(a)
a=bpy.data.actions.new('Attack');a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=48;rig.animation_data.action=a;prev={}
for i,pose in enumerate(poses):
 for n,m in pose.items():
  pb=rig.pose.bones[n];q=m.to_quaternion()
  if n in prev and q.dot(prev[n])<0:q=-q
  prev[n]=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=i/4)
  if n=='B_Pelvis':pb.location=m.translation;pb.keyframe_insert('location',frame=i/4)
(P/'work/attack_fit.json').write_text(json.dumps({'impact_seconds':1.0,'duration_seconds':1.6,'shoulder_keys_degrees':keys,'fixed_local_wrist':True,'probes':probes},indent=2)+'\n')
print('ATTACK ARC',probes,flush=True);bpy.ops.wm.save_as_mainfile(filepath=out)
