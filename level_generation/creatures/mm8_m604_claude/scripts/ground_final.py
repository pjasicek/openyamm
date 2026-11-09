"""Clear fast-strike subframes and level the two running support phases without removing flight."""
from pathlib import Path
import bpy,numpy as np,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/ready_motion.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
names=[g.name for g in body.vertex_groups];support=np.array([sum(e.weight for e in v.groups if names[e.group].startswith('B_R_') and any(t in names[e.group] for t in ('Forearm','Hand','Finger')))<.25 for v in body.data.vertices]);feet={s:np.array([sum(e.weight for e in v.groups if names[e.group] in (f'B_{s}_Foot',f'B_{s}_Toe0'))>.5 for v in body.data.vertices]) for s in 'LR'}
def curves(a):return [fc for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
for a in bpy.data.actions:
 for fc in curves(a):
  for k in fc.keyframe_points:k.interpolation='LINEAR'
report={}
for name in ['Walking','Running','Attack','Hit','Death','Fidget']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];end=int(a.frame_range[1]);rows=[]
 for f in np.arange(0,end+.001,.25):
  sc.frame_set(int(f),subframe=f-int(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=np.array([v.co.z for v in m.vertices]);ev.to_mesh_clear()
  rows.append([f,z[feet['L']].min(),z[feet['R']].min(),z[support].min()])
 rows=np.array(rows);dz=np.maximum(-rows[:,1:3].min(1)-.001,0)
 if name=='Death':dz=np.maximum(-rows[:,3]-.001,0)
 if name=='Running':
  ml,mr=rows[:,1].min(),rows[:,2].min();w=.5+.5*np.tanh((rows[:,2]-rows[:,1])/.08);dz=-(w*ml+(1-w)*mr)
 # Keep dense support keys in the master; export samples them at 120 Hz without changing clip speed.
 if name in ('Walking','Attack','Hit','Fidget'):dz=-rows[:,1:3].min(1)
 if name=='Death':dz=-rows[:,3]
 loc=[]
 for f in rows[:,0]:
  sc.frame_set(int(f),subframe=float(f-int(f)));loc.append(rig.pose.bones['B_Pelvis'].location.copy())
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if fc.data_path=='pose.bones["B_Pelvis"].location':bag.fcurves.remove(fc)
 pb=rig.pose.bones['B_Pelvis'];inv=pb.bone.matrix_local.to_3x3().inverted();corrections=dz.tolist()
 for i,(f,d) in enumerate(zip(rows[:,0],dz)):
  sc.frame_set(int(f),subframe=float(f-int(f)));pb.location=loc[i]+inv@Vector((0,0,float(d)));pb.keyframe_insert('location',frame=float(f))
 for fc in curves(a):
  for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[name]={'maximum_correction_cm':max(corrections)*100,'minimum_correction_cm':min(corrections)*100}
# Blade clearance is solved after foot levelling and root contact correction, so later floor changes cannot undo it.
import sys,math
from mathutils import Matrix,Quaternion
sys.path.insert(0,str(p/'scripts'));import armik
G=json.load(open(p/'work/grip_pose.json'));A=Vector(G['handle_axis_hand_local']).normalized();C=Vector(G['handle_centre_hand_local'])
a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];impact=json.load(open(p/'work/clip_timing.json'))['attack_impact_s']*30;tips=[]
for f in (impact-.25,impact+.25):
 sc.frame_set(int(f),subframe=f-int(f));H=rig.pose.bones['B_R_Hand'].matrix;tips.append(H@(C+A*.84))
sc.frame_set(int(impact),subframe=impact-int(impact));H=rig.pose.bones['B_R_Hand'].matrix;axis=(H.to_3x3()@A).normalized();v=tips[1]-tips[0];X=H.to_3x3().inverted()@(v-axis*v.dot(axis)).normalized();X=(X-A*X.dot(A)).normalized();Z=X.cross(A);M=Matrix((X,A,Z)).transposed().to_4x4();M.translation=C
with bpy.data.libraries.load(str(p/'work/props.blend'),link=False) as (src,dst):dst.meshes=['SwordMesh']
points=[M@v.co for v in dst.meshes[0].vertices]
old=bpy.data.actions['Death'];rig.animation_data.action=old;rig.animation_data.action_slot=old.slots[0];end=float(old.frame_range[1]);poses=[];fs=np.arange(0,end+.001,.25)
for f in fs:
 sc.frame_set(int(f),subframe=float(f-int(f)));poses.append({b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones})
rig.animation_data.action=None;bpy.data.actions.remove(old);out=bpy.data.actions.new('Death');out.use_fake_user=True;prev=None;adjust=[];previous_q={}
def twist(q,axis):
 t=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);return (t+math.pi)%(2*math.pi)-math.pi
for f,pose in zip(fs,poses):
 rig.animation_data.action=None
 for n,(q,l) in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update();ref={b.name:b.matrix_basis.copy() for b in rig.pose.bones};amount=0
 for _ in range(4):
  H=rig.pose.bones['B_R_Hand'].matrix.copy();low=min((H@v).z for v in points);lift=max(0,.008-low)
  if lift<.0005:break
  amount+=lift;axis=(H.to_3x3()@A).normalized()
  prev=armik.solve_aimed(rig,'R',H.translation+Vector((0,0,lift)),A,axis,ref,prev=prev,phis=range(-20,21,5),devs=((0,0),))
  # Keep the source hand's full orientation; axis-only IK allowed a sudden 180-degree blade roll.
  hand=rig.pose.bones['B_R_Hand'];fixed=H.copy();fixed.translation=hand.matrix.translation;hand.matrix=fixed;bpy.context.view_layer.update()
 fb,hb=rig.data.bones['B_R_Forearm'],rig.data.bones['B_R_Hand'];axis=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion()
 rig.pose.bones['B_R_ForearmTwist'].rotation_quaternion=Quaternion(axis,.6*twist(rel@rest.inverted(),axis));ub=rig.data.bones['B_R_UpperArm'];axis=(ub.matrix_local.inverted()@fb.head_local).normalized();rig.pose.bones['B_R_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*twist(rig.pose.bones[ub.name].rotation_quaternion,axis))
 rig.animation_data.action=out
 for pb in rig.pose.bones:
  q=pb.rotation_quaternion.copy()
  if pb.name in previous_q and q.dot(previous_q[pb.name])<0:q=-q
  previous_q[pb.name]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))
  if pb.name=='B_Pelvis':pb.keyframe_insert('location',frame=float(f))
 adjust.append(amount)
out.use_frame_range=True;out.frame_start=0;out.frame_end=end
for fc in curves(out):
 for k in fc.keyframe_points:k.interpolation='LINEAR'
report['Death_sword']={'maximum_wrist_lift_cm':max(adjust)*100,'sample_rate_hz':120};print('SWORD CLEARANCE',report['Death_sword'])
rig.animation_data.action=None
(p/'work/final_floor_adjustment.json').write_text(json.dumps(report,indent=2));print('GROUND FINAL',report)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/ready_final.blend'))
