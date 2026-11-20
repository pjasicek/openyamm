"""Amplify the accepted two-hand chop through a diagonal, body-led swing."""
from pathlib import Path
import bpy, json, math, sys
import numpy as np
from mathutils import Matrix, Vector
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import armik,common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/attack_revision_1/textured_uv.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=30
source=bpy.data.actions['Attack'];END=35/30
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'LR'}
GC={s:Vector(G[s]['handle_centre_hand_local']) for s in 'LR'}
GA={s:Vector(G[s]['handle_axis_hand_local']) for s in 'LR'}
def action(a):
 r.animation_data.action=a
 if a and a.slots:r.animation_data.action_slot=a.slots[0]
def smooth(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def curve(keys,t):
 for (ta,va),(tb,vb) in zip(keys,keys[1:]):
  if t<=tb:
   w=smooth((t-ta)/(tb-ta));return np.array(va)*(1-w)+np.array(vb)*w
 return np.array(keys[-1][1])
def transform_at(pivot,rotation):
 return Matrix.Translation(pivot)@rotation.to_4x4()@Matrix.Translation(-pivot)
poses=[];probe=[]
for frame in np.arange(0,35.01,.5):
 t=float(frame/30)
 sf=float(curve([(0,[0]),(.32,[10.4]),(.62,[18.72]),(.70,[18.72]),(26/30,[26]),(.98,[29]),(END,[35])],t)[0])
 action(source);sc.frame_set(int(sf),subframe=sf-int(sf))
 basis={b.name:b.matrix_basis.copy() for b in r.pose.bones}
 action(None)
 for n,m in basis.items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
 worlds={b.name:armik.W(r,b.name).copy() for b in r.pose.bones}
 pitch,yaw,roll=curve([(0,[0,0,0]),(.62,[-15,-32,-16]),(.70,[-15,-32,-16]),(26/30,[18,38,6]),(.98,[22,55,10]),(END,[0,0,0])],t)
 shift=Vector(curve([(0,[0,0,0]),(.62,[0,.07,.025]),(.70,[0,.07,.025]),(.98,[.025,-.12,-.035]),(END,[0,0,0])],t))
 pelvis=worlds['B_Pelvis'].translation
 # Pelvis starts the weight transfer; chest and shoulders lead the diagonal cut.
 base=Matrix.Translation(shift)@transform_at(pelvis,Matrix.Rotation(math.radians(pitch*.45),3,'X')@Matrix.Rotation(math.radians(yaw*.45),3,'Z'))
 chestpivot=base@worlds['B_Spine'].translation
 upper=transform_at(chestpivot,Matrix.Rotation(math.radians(pitch*.55),3,'X')@Matrix.Rotation(math.radians(yaw*.55),3,'Z')@Matrix.Rotation(math.radians(roll),3,'Y'))@base
 for b in r.pose.bones:
  upper_body=b.name=='Polearm' or b.name=='B_Spine' or any(p.name=='B_Spine' for p in b.parent_recursive)
  armik.set_world(r,b.name,(upper if upper_body else base)@worlds[b.name])
 # Sweep feathers behind the torso as the shoulders twist past the hips.
 sweep=float(curve([(0,[0]),(.5,[22]),(.98,[22]),(END,[0])],t)[0])
 for side,sign in (('L',1),('R',-1)):
  n=f'Wing_{side}_Root';m=armik.W(r,n)
  armik.set_world(r,n,armik.rot_world(m,Matrix.Rotation(math.radians(sign*sweep),3,'Z')@m.to_3x3()))
 # Keep the gaze on the target while the shoulders turn.
 for n,fraction in (('B_Neck',.35),('B_Head',.45)):
  m=armik.W(r,n);rot=Matrix.Rotation(math.radians(-yaw*fraction),3,'Z')@m.to_3x3()
  armik.set_world(r,n,armik.rot_world(m,rot))
 H=armik.W(r,'B_R_Hand');C=H@GC['R'];A=(H.to_3x3()@GA['R']).normalized()
 # Resampling the source requires the same subframe grip correction as production.
 W=armik.W(r,'Polearm');N=W.to_3x3()@Vector((0,0,1));N=(N-A*N.dot(A)).normalized()
 W=Matrix((A.cross(N),A,N)).transposed().to_4x4();W.translation=C;armik.set_world(r,'Polearm',W)
 H=armik.W(r,'B_L_Hand');R=(H.to_3x3()@GA['L']).rotation_difference(A).to_matrix()@H.to_3x3()
 armik.solve(r,'L',C-A*.24-R@GC['L'],hand_rot=R)
 errs={s:(armik.W(r,f'B_{s}_Hand')@GC[s]-(C-A*(.24 if s=='L' else 0))).length for s in 'LR'}
 assert max(errs.values())<.003,(t,errs)
 poses.append((float(frame),{b.name:b.matrix_basis.copy() for b in r.pose.bones}))
 probe.append({'time':t,'source_frame':sf,'grip':list(C),'axis':list(A),'tip':list(C+A*1.03),'pitch':float(pitch),'yaw':float(yaw),'grip_error':errs})
bpy.data.actions.remove(source);a=bpy.data.actions.new('Attack');a.use_fake_user=True;action(a);previous={}
for frame,pose in poses:
 for n,m in pose.items():
  loc,q,_=m.decompose();pb=r.pose.bones[n];pb.rotation_mode='QUATERNION'
  if n in previous and previous[n].dot(q)<0:q=-q
  previous[n]=q.copy();pb.rotation_quaternion=q;pb.location=loc;pb.scale=(1,1,1)
  pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame)
a.use_frame_range=True;a.frame_start=0;a.frame_end=35
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/attack_revision_1/candidate.blend'))
(P/'work/attack_revision_1/fit.json').write_text(json.dumps({'probe':probe},indent=2)+'\n')
common.workbench_clay(sc);folder=P/'review/attack_revision_1';folder.mkdir(exist_ok=True)
for t in (0,.65,.80,26/30,.98,END):
 f=t*30;sc.frame_set(int(f),subframe=f-int(f))
 common.render_views(str(folder/f'pose_{t:.3f}'),1.5,4.5,views=('front','left','three_quarter'),resolution=(900,700))
