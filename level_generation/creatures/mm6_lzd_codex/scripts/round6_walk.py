import bpy,sys,json,math,ast,shutil
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
W=P/'work/round6';O=P/'review/round6';W.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round5/retimed_master.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=30
# Reuse the existing authored chain solver and prop transforms.
src=ast.parse((P/'scripts/round5_motion.py').read_text())
for node in src.body:
 if isinstance(node,ast.FunctionDef) and node.name in ['action','get','put','sample','rot','aim','ik','strings']:
  exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/'scripts/round5_motion.py'),'exec'))
rb=rig.data.bones;M0={n:b.matrix_local.copy()for n,b in rb.items()}
a=bpy.data.actions['Walking'];ts=np.linspace(0,.8,97)
old=[];world=[]
for t in ts:
 old.append(sample(a,t*30));world.append({n:b.matrix.copy()for n,b in rig.pose.bones.items()})
home=sample(bpy.data.actions['Standing'],0);homeworld={n:b.matrix.copy()for n,b in rig.pose.bones.items()}
# Choose one reachable height envelope for both legs. Never clamp pelvis per frame.
limits=[];knee_constraints=[]
for t,p in zip(ts,world):
 upper=[]
 for side in 'LR':
  U,F,H=[f'B_{side}_{n}'for n in ['Thigh','Calf','Foot']]
  A,E,T=[p[n].translation for n in [U,F,H]]
  a=(E-A).length;b=(T-E).length;xy=Vector((T.x-A.x,T.y-A.y,0)).length;offset=A.z-p['B_Pelvis'].translation.z
  upper.append(T.z+math.sqrt(max(0,((a+b)*.997)**2-xy*xy))-offset)
  peak=.375 if side=='L'else .729166667
  if abs(t-peak)<.005:
   low=T.z+math.sqrt(max(0,a*a+b*b+2*a*b*math.cos(math.radians(57))-xy*xy))-offset
   knee_constraints.append((t,low))
 limits.append(min(upper))
limits=np.array(limits);original=np.array([p['B_Pelvis'].translation.z for p in world]);candidates=[]
for amplitude in np.linspace(.035,.09,56):
 for phase in np.linspace(-.03,.03,61):
  for harmonic in [0,-.08,-.16,-.24]:
   theta=2*math.tau*(ts-phase)/.8;wave=np.cos(theta)+harmonic*np.cos(2*theta);base=float(min(limits-amplitude*wave))-.001
   if all(base+amplitude*(math.cos(2*math.tau*(t-phase)/.8)+harmonic*math.cos(4*math.tau*(t-phase)/.8))>=low for t,low in knee_constraints):
    score=float(np.mean((base+amplitude*wave-original)**2))+.005*amplitude**2
    candidates.append((score,base,float(amplitude),float(phase),harmonic))
assert candidates,'No reachable symmetric bob for the accepted foot paths'
_,base,amplitude,phase,harmonic=min(candidates)
print('BOB_FIT',base,amplitude,phase,harmonic,flush=True)
rows=[];exports={};trace=[]
for i,t in enumerate(ts):
 put(old[i]);p=rig.pose.bones['B_Pelvis'];m=p.matrix.copy();m.translation.z=base+amplitude*(math.cos(2*math.tau*(t-phase)/.8)+harmonic*math.cos(4*math.tau*(t-phase)/.8));p.matrix=m;bpy.context.view_layer.update()
 for side in 'LR':
  names=[f'B_{side}_{n}'for n in ['Thigh','Calf','Foot']]
  target=world[i][names[2]];ik(names,target.translation,Vector((0,-1,0)));rot(names[2],target.to_3x3())
  # Foot and toe local poses remain as originally accepted.
  q,l,sz=old[i][f'B_{side}_Toe0'];b=rig.pose.bones[f'B_{side}_Toe0'];b.rotation_quaternion=q;b.location=l;b.scale=sz
 # Positive shoulder pitch swings back (+Y); match the ipsilateral foot's forward excursion.
 for side in 'LR':
  for n,(q,l,sz) in home.items():
   if n.startswith(f'B_{side}_') and any(x in n for x in ['UpperArm','Forearm','Hand','Finger']):
    b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=sz
  bpy.context.view_layer.update()
  arm_phase=math.tau*t/.8
  angle=math.radians(25)*math.sin(arm_phase)*(-1 if side=='L'else 1)
  U=f'B_{side}_UpperArm'
  rot(U,Matrix.Rotation(angle,3,'X')@homeworld[U].to_3x3())
 # Let the palm follow the thigh slightly through the wider swing, without changing elbow roll.
 h=rig.pose.bones['B_R_Hand'];origin=.5*(h.head+sum((rig.pose.bones[f'B_R_Finger{n}'].head for n in [0,1,2,2,4]),Vector())/5)
 goal=rig.pose.bones['B_R_Thigh'].head-origin;goal.z=0
 normal=h.matrix.to_3x3()@Vector((.000788543373346,.150269255042,.988644838333))
 yaw=math.atan2(normal.x*goal.y-normal.y*goal.x,normal.x*goal.x+normal.y*goal.y)
 rot('B_R_Hand',Matrix.Rotation(.4*yaw,3,'Z')@h.matrix.to_3x3())
 rig.pose.bones['Bow'].matrix_basis.identity();bpy.context.view_layer.update();strings()
 # Keep the existing cloth solution attached to the unchanged feet/pelvis yaw.
 bpy.context.view_layer.update();rows.append(get())
 pose={}
 for n,b in rig.pose.bones.items():
  local=b.parent.matrix.inverted()@b.matrix if b.parent else Matrix.Rotation(-math.pi/2,4,'X')@b.matrix
  l,q,s=local.decompose();pose[n]={'translation':list(l),'rotation':[q.x,q.y,q.z,q.w],'scale':list(s)}
 exports[str(float(t))]=pose
 trace.append({'time':float(t),'old':{n:list(world[i][n].translation)for n in ['B_Pelvis','B_Spine2','B_Head','B_L_Foot','B_R_Foot']},'new':{n:list(rig.pose.bones[n].head)for n in ['B_Pelvis','B_Spine2','B_Head','B_L_Foot','B_R_Foot','B_L_Hand','B_R_Hand']}})
rows[-1]=rows[0];exports[str(float(ts[-1]))]=exports[str(float(ts[0]))]
action(None);bpy.data.actions.remove(bpy.data.actions['Walking']);a=bpy.data.actions.new('Walking');a.use_fake_user=True;action(a);prev={}
for t,row in zip(ts,rows):
 for n,(q,l,s) in row.items():
  if n in prev and prev[n].dot(q)<0:q=-q
  prev[n]=q;b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.scale=s
  for ch in ['rotation_quaternion','location','scale']:b.keyframe_insert(ch,frame=float(t*30))
a.use_frame_range=True;a.frame_start=0;a.frame_end=24
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(W/'master.blend'))
(W/'walking_local.json').write_text(json.dumps(exports))
(O/'authoring_trace.json').write_text(json.dumps({'base':base,'bob_amplitude':amplitude,'bob_phase_s':phase,'bob_harmonic':harmonic,'shoulder_amplitude_deg':25,'samples':trace},indent=2))
print('WALKING',base,'floor target error',max((Vector(r['old'][f'B_{s}_Foot'])-Vector(r['new'][f'B_{s}_Foot'])).length for r in trace for s in 'LR'))
