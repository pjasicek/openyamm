"""Add restrained weight transfer and footwork to the accepted, retimed RPG downward attack."""
from pathlib import Path
import bpy, json, math, sys, runpy
import numpy as np
from mathutils import Vector, Matrix
P=Path(__file__).resolve().parents[1];OUT=P/'review/attack_body';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(P/'scripts'))
CLIP='AttackRPG6';RATE=120
UPDATED=['B_Pelvis','B_Spine']+[f'B_{s}_{n}' for s in 'LR' for n in ('Thigh','Calf','Foot','Toe0')]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_attack_windup.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];W=rig.matrix_world
base=bpy.data.actions[CLIP];duration=base.frame_end/30

def action(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]

def pose():return {b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
def apply(row):
 action(None)
 for n,(q,l) in row.items():
  b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l;b.scale=(1,1,1)
 bpy.context.view_layer.update()
def point(n):return W@rig.pose.bones[n].head
def turn(n,R):
 b=rig.pose.bones[n];M=W@b.matrix;h=M.translation.copy()
 b.matrix=W.inverted()@Matrix.Translation(h)@R.to_4x4()@Matrix.Translation(-h)@M
 bpy.context.view_layer.update()
def aim(n,child,direction):turn(n,(point(child)-point(n)).rotation_difference(direction).to_matrix())
def curve(keys,t):
 for (a,x),(b,y) in zip(keys,keys[1:]):
  if t<=b:
   u=max(0,min(1,(t-a)/(b-a)));u=u*u*(3-2*u)
   return x+(y-x)*u
 return keys[-1][1]
def rotation(axis,degrees):return Matrix.Rotation(math.radians(degrees),3,axis)

# Read every source pose before adding keys, retaining the accepted upper-body curves.
times=np.linspace(0,duration,round(duration*RATE)+1);samples=[]
for t in times:
 action(base);f=t*30;scene.frame_set(int(f),subframe=float(f%1));samples.append(pose())
apply(samples[0]);feet={};legs={};poles={};pivots={}
for side in 'LR':
 thigh,calf,foot=[f'B_{side}_{n}' for n in ('Thigh','Calf','Foot')]
 H,K,A=[point(n) for n in (thigh,calf,foot)]
 feet[side]=(W@rig.pose.bones[foot].matrix).copy()
 legs[side]=((K-H).length,(A-K).length)
 u=(A-H).normalized();poles[side]=(K-H-u*(K-H).dot(u)).normalized()
 groups={g.index for g in body.vertex_groups if g.name in (foot,f'B_{side}_Toe0')}
 ids=[v.index for v in body.data.vertices if sum(w.weight for w in v.groups if w.group in groups)>.7]
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 co=[body.matrix_world@me.vertices[i].co for i in ids]
 pivots[side]=Vector((A.x,min(v.y for v in co),min(v.z for v in co)));ev.to_mesh_clear()

ankle_error=0;floor_min=0;foot_range={'L':[],'R':[]};hip_range=[];tips=[];rows=[]
def solve_leg(side,target):
 global ankle_error
 thigh,calf,foot=[f'B_{side}_{n}' for n in ('Thigh','Calf','Foot')]
 H=point(thigh);A=target.translation;v=A-H;d=v.length;l1,l2=legs[side]
 assert abs(l1-l2)+1e-5<d<l1+l2-1e-5,(side,d,l1+l2)
 u=v/d;a=(l1*l1-l2*l2+d*d)/(2*d);height=math.sqrt(max(0,l1*l1-a*a))
 pole=(poles[side]-u*poles[side].dot(u)).normalized();K=H+u*a+pole*height
 aim(thigh,calf,K-H);aim(calf,foot,A-point(calf))
 b=rig.pose.bones[foot];M=target.copy();M.translation=point(foot);b.matrix=W.inverted()@M
 bpy.context.view_layer.update();ankle_error=max(ankle_error,(point(foot)-A).length)

for t,row in zip(times,samples):
 apply(row)
 if 0<t<duration:
  # Transfer the existing chest coil into the pelvis without adding extra yaw to the mace swing.
  yaw=curve([(0,0),(.33,-12),(.59,14),(.82,9),(duration,0)],t)
  delta=Vector((curve([(0,0),(.32,-.018),(.59,.026),(.83,.018),(duration,0)],t),
                curve([(0,0),(.32,.025),(.59,-.055),(.83,-.040),(duration,0)],t),
                -curve([(0,0),(.30,.022),(.58,.014),(.83,.012),(duration,0)],t)))
  spine=(W@rig.pose.bones['B_Spine'].matrix).to_3x3()
  turn('B_Pelvis',rotation('Z',yaw))
  b=rig.pose.bones['B_Pelvis'];M=W@b.matrix;M.translation+=delta;b.matrix=W.inverted()@M
  bpy.context.view_layer.update()
  lean=curve([(0,0),(.32,-1.5),(.60,3),(.85,1.5),(duration,0)],t)
  b=rig.pose.bones['B_Spine'];M=(rotation('X',lean)@spine).to_4x4();M.translation=point(b.name);b.matrix=W.inverted()@M
  bpy.context.view_layer.update()
  step=curve([(0,0),(.12,0),(.38,.10),(.84,.10),(1.22,0),(duration,0)],t)
  lift=curve([(0,0),(.12,0),(.245,.030),(.38,0),(.84,0),(1.01,.026),(1.22,0),(duration,0)],t)
  for side in 'LR':
   yaw_foot=curve([(0,0),(.33,-3),(.59,12),(.84,10),(duration,0)],t) if side=='R' else 4*step/.10
   heel=curve([(0,0),(.36,0),(.60,8),(.83,6),(1.12,0),(duration,0)],t) if side=='R' else 0
   pivot=pivots[side];R=rotation('Z',yaw_foot)@rotation('X',heel)
   target=Matrix.Translation(pivot)@R.to_4x4()@Matrix.Translation(-pivot)@feet[side]
   if side=='L':target.translation+=Vector((0,-step,lift))
   solve_leg(side,target)
 rows.append(pose());hip_range.append(tuple(point('B_Pelvis')))
 for side in 'LR':foot_range[side].append(tuple(point(f'B_{side}_Foot')))
 tips.append(tuple(point('Mace')+rig.pose.bones['Mace'].y_axis*.385))
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 floor_min=min(floor_min,min((body.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
assert ankle_error<2e-5,ankle_error
assert floor_min>-.002,('foot penetration',floor_min)
new=base.copy();action(None);bpy.data.actions.remove(base);new.name=CLIP;new.use_fake_user=True
for layer in new.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in list(bag.fcurves):
    if any(fc.data_path.startswith(f'pose.bones["{n}"]') for n in UPDATED):bag.fcurves.remove(fc)
previous={}
for t,row in zip(times,rows):
 apply(row);action(new)
 for n in UPDATED:
  b=rig.pose.bones[n];q=b.rotation_quaternion.copy()
  if n in previous and q.dot(previous[n])<0:q.negate()
  previous[n]=q.copy();b.rotation_quaternion=q
  b.keyframe_insert('rotation_quaternion',frame=float(t*30))
  if n=='B_Pelvis':b.keyframe_insert('location',frame=float(t*30))
for layer in new.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.interpolation='LINEAR'
new.use_frame_range=True;new.frame_start=0;new.frame_end=duration*30
action(new);scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_attack_body.blend'))
speed=np.linalg.norm(np.diff(np.array(tips),axis=0),axis=1)*RATE
metadata={CLIP:{'clip':'SwordAttackR6 with fitted stance and authored weight transfer','duration':duration,
 'changed_bones':UPDATED,'sample_hz':RATE,'max_ankle_target_error_m':ankle_error,'floor_min_m':floor_min,
 'peak_tip_time':(int(np.argmax(speed))+.5)/RATE,'hip_range_m':np.ptp(np.array(hip_range),axis=0).tolist(),
 'ankle_range_m':{s:np.ptp(np.array(v),axis=0).tolist() for s,v in foot_range.items()}}}
(OUT/'motion_sources.json').write_text(json.dumps(metadata,indent=2)+'\n');print('BODY_MOTION',metadata,flush=True)
# Export at 120 Hz so the accepted 1.291667-second endpoint remains exact.
for act in list(bpy.data.actions):
 if act!=new:bpy.data.actions.remove(act)
for layer in new.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for key in fc.keyframe_points:key.co.x*=4
    fc.update()
new.frame_end*=4;scene.render.fps=RATE
for obj in bpy.data.objects:obj.select_set(obj in (rig,body,bpy.data.objects['Mace']))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(OUT/'motion.glb'),use_selection=True,export_format='GLB',export_yup=True,
 export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
 export_skins=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
runpy.run_path(str(P/'scripts/motion_preview_checks.py'),run_name='__main__',
 init_globals={'REVIEW_OUT':OUT,'REVIEW_BLEND':P/'work/rig_attack_body.blend'})
for view in ('front','three_quarter','right'):
 sys.argv=[str(P/'scripts/clip_sheet.py'),'--',str(P/'work/rig_attack_body.blend'),str(OUT/view),view,'9',CLIP]
 runpy.run_path(sys.argv[0],run_name='__main__')
