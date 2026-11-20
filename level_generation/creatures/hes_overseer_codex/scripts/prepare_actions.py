"""Local library arms over native flight, with independent rod/pistol motion and smooth ready transitions."""
import bpy,json,sys,os,math
from pathlib import Path
from mathutils import Matrix,Quaternion
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/armour_skinned.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data_create();grips=json.loads((P/'work/grip_pose.json').read_text())
assert all(g['candidate_pass'] for g in grips.values())
print('GRIP_CANDIDATES', {s:g['candidate_pass'] for s,g in grips.items()},flush=True)
TURN=Matrix.Rotation(math.pi,4,'Z')
arm_names=[f'B_{sd}_{part}' for sd in 'LR' for part in ['UpperArm','Forearm','Hand']]
body_names=['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head','B_L_Clavicle','B_R_Clavicle']
source_names=body_names+arm_names
order=[b.name for b in rig.data.bones]
def active(obj,act):
 obj.animation_data.action=act
 if act.slots:obj.animation_data.action_slot=act.slots[0]
def frame(value):scene.frame_set(math.floor(value),subframe=value%1)
source={};sources={}
for file,names in [('1Hand',['PistolAttackL1','MaceAttackR1']),('Armed',['ArmedIdle','ArmedIdlePistolL','ArmedCastRAttack1','ArmedGetHitF1'])]:
 old_objects=set(bpy.data.objects);old_actions=set(bpy.data.actions)
 bpy.ops.import_scene.gltf(filepath=str(ROOT/'anim_library/humanoid_set'/f'{file}.glb'))
 added=set(bpy.data.objects)-old_objects;added_actions=set(bpy.data.actions)-old_actions
 src=next(o for o in added if o.type=='ARMATURE');src.animation_data_create()
 for track in src.animation_data.nla_tracks:track.mute=True
 for name in names:
  act=next(a for a in added_actions if a.name.split('@')[-1].split('|')[-1]==name);active(src,act)
  start,end=act.frame_range;fps=scene.render.fps/scene.render.fps_base;duration=(end-start)/fps
  samples=[]
  for k in range(math.ceil(duration*48)+1):
   t=min(k/48,duration);frame(start+t*fps)
   samples.append({n:(TURN@src.matrix_world@src.pose.bones[n].matrix).to_3x3().normalized().to_quaternion() for n in source_names})
  if name in ('MaceAttackR1','ArmedCastRAttack1','ArmedGetHitF1'):
   # Smooth the short source impact over three source frames, retaining its overhead path and endpoints.
   for _ in range(4):
    prev=samples
    samples=[prev[0]]+[{n:prev[k][n].slerp(prev[k-1][n].slerp(prev[k+1][n],.5),.5) for n in source_names} for k in range(1,len(prev)-1)]+[prev[-1]]
  source[name]=(duration,samples);sources[name]={'file':f'anim_library/humanoid_set/{file}.glb','duration_s':duration}
 for obj in added:bpy.data.objects.remove(obj,do_unlink=True)
 for act in added_actions:bpy.data.actions.remove(act)
def sample(name,t,n):
 duration,values=source[name];u=max(0,min(t,duration))*48;i=min(int(u),len(values)-1);j=min(i+1,len(values)-1)
 return values[i][n].slerp(values[j][n],u-int(u))
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
clips=[('Flight','Flight',3,None),('AttackRanged','Flight',1.2,'PistolAttackL1'),('AttackMelee','Flight',2.4,'MaceAttackR1'),('Cast','Cast',1.4,'ArmedCastRAttack1'),('Hit','Hit',.75,'ArmedGetHitF1'),('Death','Death',1.25,None),('Dead','Dead',1,None)]
report={}
for name,native,seconds,motion in clips:
 base=bpy.data.actions['Winged_'+native];active(rig,base)
 times=sorted(set([k/48 for k in range(math.floor(seconds*48)+1)]+[seconds]));poses=[]
 for t in times:
  native_duration={'Cast':31/24,'Hit':.75,'Death':1.25,'Dead':1}.get(native,3)
  frame((t%3 if native=='Flight' else min(t,native_duration))*48)
  poses.append({n:rig.pose.bones[n].matrix_basis.copy() for n in order})
 action=bpy.data.actions.new('Overseer_'+name);action.use_fake_user=True;active(rig,action);previous={}
 for t,bases in zip(times,poses):
  for n,M in bases.items():rig.pose.bones[n].matrix_basis=M
  bpy.context.view_layer.update()
  if motion:
   duration=source[motion][0];speed=.5 if name=='AttackMelee' else .8 if name=='Cast' else 1;lead=.3 if name=='AttackMelee' else .2 if name!='Hit' else .1;trail=seconds-lead-duration/speed
   phase=max(0,min((t-lead)*speed,duration));weight=smooth(t/lead)*smooth((seconds-t)/max(trail,.1))
  if name=='AttackMelee':
   raw=max(0,(t-lead)*speed);phase=min(raw,.30)+.06*(2*smooth(min(1,max(0,(raw-.30)/.12)))-smooth(min(1,max(0,(raw-.30)/.12)))**2) if raw>.30 else raw
   weight=smooth(t/lead)*(1-smooth((t-1.14)/(seconds-1.14)))
  if name in ('AttackMelee','Cast','Hit'):
   # Carry the source trunk, head and clavicles with its strike, retaining native wing/leg motion underneath.
   for n in body_names:
    pb=rig.pose.bones[n];q=pb.matrix.to_quaternion().slerp(sample(motion,phase,n),weight);M=q.to_matrix().to_4x4();M.translation=pb.head;pb.matrix=M;bpy.context.view_layer.update()
  for n in arm_names:
   side=n[2];q=sample('ArmedIdle',0,n)
   chosen=motion and (name=='Hit' or side==('L' if name=='AttackRanged' else 'R'))
   if chosen:q=q.slerp(sample(motion,phase,n),weight)
   clav=f'B_{side}_Clavicle';reference=sample('ArmedIdle',0,clav)
   if chosen:reference=reference.slerp(sample(motion,phase,clav),weight)
   q=rig.pose.bones[clav].matrix.to_quaternion() @ reference.inverted() @ q
   if n=='B_L_Hand':
    H=rig.data.bones[n].matrix_local.to_3x3();ref=Matrix.Rotation(math.pi/2,3,'X');fitted=Matrix(grips[side]['rotation_bind']);q=q @ (H.inverted() @ ref @ fitted.inverted() @ H).to_quaternion()
   pb=rig.pose.bones[n];M=q.to_matrix().to_4x4();M.translation=pb.head;pb.matrix=M;bpy.context.view_layer.update()
  for sd,g in grips.items():
   for n,q in g['finger_local'].items():rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=Quaternion(q)
  for n in order:
   pb=rig.pose.bones[n];loc,q,scale=pb.matrix_basis.decompose()
   if n in previous and q.dot(previous[n])<0:q.negate()
   previous[n]=q.copy();pb.rotation_mode='QUATERNION';pb.location=loc;pb.rotation_quaternion=q;pb.scale=scale
   for path in ['location','rotation_quaternion','scale']:pb.keyframe_insert(path,frame=t*48)
  bpy.context.view_layer.update()
 action.use_frame_range=True;action.frame_start=0;action.frame_end=seconds*48
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 report[action.name]={'duration_s':seconds,'arm_source':('PistolAttackL1 fitted aim, 10 degree muzzle recoil, eased from/to ArmedIdle' if name=='AttackRanged' else motion or 'ArmedIdle (pistol lowered)'),'body_source':('MaceAttackR1 upper body over mm6_wdm flight wings/legs' if name=='AttackMelee' else 'mm6_wdm:'+native),'release_s':.45 if name=='AttackRanged' else None,'recoil_sample_s':.53 if name=='AttackRanged' else None,'impact_candidate_s':41.5/48 if name=='AttackMelee' else None,'source_time_scale':2.0 if name=='AttackMelee' else 1.0}
 print('ACTION',action.name,flush=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
scene.render.fps=48
(P/'work/action_sources.json').write_text(json.dumps({'clips':report,'library':sources},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/overseer_actions.blend'))
print('ACTIONS_DONE',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
