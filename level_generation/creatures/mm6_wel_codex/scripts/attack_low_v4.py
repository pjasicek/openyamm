"""Low-grip diagonal thrust, with right-side wind-up and left-arm counterbalance."""
import bpy, json, math, sys, hashlib
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
P=Path(__file__).resolve().parents[1];OUT=P/'review/attack_low_v4'
sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'review/revisions/water_v3/work/textured_master.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=60
R={b.name:b.matrix_local.copy() for b in r.data.bones}
r.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.context.view_layer.update()
base={b.name:b.matrix_basis.copy() for b in r.pose.bones};M0={b.name:b.matrix.copy() for b in r.pose.bones}
G=json.loads((P/'work/grip_pose.json').read_text());ah=Vector(G['handle_axis_hand_local'])

def ss(x):x=max(0,min(1,x));return x*x*(3-2*x)
def path(t,keys):
 for (a,p),(b,q) in zip(keys,keys[1:]):
  if t<=b:return Vector(p).lerp(Vector(q),ss((t-a)/(b-a)))
 return Vector(keys[-1][1])
def set_rotation(n,rot):
 pb=r.pose.bones[n];m=pb.matrix.copy();m=rot.to_4x4();m.translation=pb.matrix.translation;pb.matrix=m;bpy.context.view_layer.update()
def curves(act):return [f for l in act.layers for s in l.strips for cb in s.channelbags for f in cb.fcurves]
def action_hash(act):return hashlib.sha256(json.dumps([(f.data_path,f.array_index,[(list(k.co),k.interpolation) for k in f.keyframe_points]) for f in curves(act)],sort_keys=True).encode()).hexdigest()
unchanged={a.name:action_hash(a) for a in bpy.data.actions if a.name!='Attack'}
r.animation_data.action=None
keys=[];raw=[]
for i in range(97):
 t=i/60
 for n,p in base.items():r.pose.bones[n].matrix_basis=p.copy()
 bpy.context.view_layer.update()
 # Negative yaw/bank turns and leans to the creature's right; positive is its left.
 angles=path(t,[(0,(0,0,0)),(.55,(-.16,-.13,-.20)),(.66,(-.16,-.13,-.20)),(1.04,(.19,.09,.16)),(1.14,(.17,.08,.14)),(1.6,(0,0,0))])
 for n in ['B_Spine','B_Spine1','B_Spine2']:
  delta=Quaternion((0,0,1),angles.z/3)@Quaternion((0,1,0),angles.y/3)@Quaternion((1,0,0),angles.x/3)
  set_rotation(n,delta.to_matrix()@r.pose.bones[n].matrix.to_3x3())
 head=Quaternion((0,0,1),angles.z*.18)@Quaternion((0,1,0),angles.y*.15)
 set_rotation('B_Head',head.to_matrix()@r.pose.bones['B_Head'].matrix.to_3x3())
 X=r.pose.bones['B_Spine2'].matrix@M0['B_Spine2'].inverted();cr=X.to_3x3()
 for side in ['R','L']:
  U,F,H=[f'B_{side}_{n}' for n in ['UpperArm','Forearm','Hand']]
  S=r.pose.bones[U].matrix.translation;wu=M0[F].translation-M0[U].translation;wf=M0[H].translation-M0[F].translation;a,b=wu.length,wf.length
  if side=='R':
   offset=path(t,[(0,(0,0,0)),(.55,(-.10,.16,-.055)),(.66,(-.10,.16,-.055)),(1.02,(-.035,-.17,.14)),(1.12,(-.035,-.16,.13)),(1.6,(0,0,0))])
   pole_shift=path(t,[(0,(0,0,0)),(.55,(-.035,.10,-.025)),(.66,(-.035,.10,-.025)),(1.02,(.015,-.12,.08)),(1.12,(.015,-.12,.08)),(1.6,(0,0,0))])
  else:
   offset=path(t,[(0,(0,0,0)),(.55,(-.395,-.21,.22)),(.68,(-.395,-.21,.22)),(1.04,(.035,.06,.10)),(1.15,(.035,.06,.10)),(1.6,(0,0,0))])
   pole_shift=path(t,[(0,(0,0,0)),(.55,(-.025,-.10,.02)),(.68,(-.025,-.10,.02)),(1.04,(.025,-.03,.025)),(1.6,(0,0,0))])
  W=X@(M0[H].translation+offset);pole=X@(M0[F].translation+pole_shift)
  v=W-S;distance=min(max(v.length,abs(a-b)+.002),a+b-.002);v.normalize();W=S+v*distance
  pp=pole-S;pp=(pp-v*v.dot(pp)).normalized();along=(a*a-b*b+distance*distance)/(2*distance)
  elbow=S+v*along+pp*math.sqrt(max(0,a*a-along*along))
  # Transport the ready frames by the smallest rotation, avoiding arbitrary elbow-plane axial twists.
  upper=(cr@wu).rotation_difference(elbow-S).to_matrix()@cr@M0[U].to_3x3()
  fore=(cr@wf).rotation_difference(W-elbow).to_matrix()@cr@M0[F].to_3x3()
  roll=0.;wrist=0.
  hand=fore@M0[F].to_3x3().transposed()@M0[H].to_3x3()
  if side=='R':
   # Small bounded corrections aim the points; the grasp and fingers remain rigidly attached.
   aimed=path(t,[(0,(0,-.829,.559)),(.55,(.13,-.85,.50)),(.66,(.13,-.85,.50)),(1.02,(.13,-.85,.50)),(1.12,(.13,-.85,.50)),(1.6,(0,-.829,.559))]).normalized()
   axis=hand@ah;fy=(W-elbow).normalized();source=(axis-fy*axis.dot(fy)).normalized();target=(aimed-fy*aimed.dot(fy)).normalized()
   active=ss(t/.3)*ss((1.6-t)/.35)
   roll=max(-math.radians(15),min(math.radians(15),math.atan2(fy.dot(source.cross(target)),source.dot(target))))*active
   fore=Quaternion(fy,roll).to_matrix()@fore;hand=fore@M0[F].to_3x3().transposed()@M0[H].to_3x3()
   delta=(hand@ah).rotation_difference(aimed);wrist=min(math.radians(18),delta.angle)*active
   hand=Quaternion().slerp(delta,wrist/max(delta.angle,1e-7)).to_matrix()@hand
  for n,rot in [(U,upper),(F,fore),(H,hand)]:set_rotation(n,rot)
  if side=='R':raw.append({'time':t,'forearm_roll_deg':math.degrees(roll),'wrist_correction_deg':math.degrees(wrist)})
 keys.append({n:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy()) for n,p in r.pose.bones.items()})
a=bpy.data.actions['Attack'];bpy.data.actions.remove(a);a=bpy.data.actions.new('Attack');a.use_fake_user=True;r.animation_data.action=a
for i,values in enumerate(keys):
 for n,(loc,q,scale) in values.items():
  if i and q.dot(keys[i-1][n][1])<0:q.negate()
  pb=r.pose.bones[n];pb.location=loc;pb.rotation_quaternion=q;pb.scale=scale
  for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(prop,frame=i+1,group=n)
for fc in curves(a):
 for k in fc.keyframe_points:k.interpolation='LINEAR'
assert unchanged=={a.name:action_hash(a) for a in bpy.data.actions if a.name!='Attack'}
(OUT/'authored_motion.json').write_text(json.dumps({'unchanged_actions':unchanged,'right_arm':raw},indent=2))
r.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
r.animation_data.action=a;common.workbench_clay(sc)
for f in [0,20,33,40,50,61,70,82,96]:
 sc.frame_set(f+1);common.render_views(str(OUT/f'clay_{f:02}'),1.1,3.6,views=('front','right'),resolution=(600,640),target=(0,-.45))
print('Low-grip Attack baked; eight other clips preserved.')
