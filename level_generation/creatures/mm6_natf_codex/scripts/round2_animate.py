"""Review 2: retain fitted geometry/grips; restore library momentum and native shield participation."""
import bpy,sys,json,math,runpy,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'review/round2/before/work/accepted_master.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;sc.render.fps=60
names=list(rig.pose.bones.keys());roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
def attach(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def snap():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names}
def sample(a,f):
 attach(a);sc.frame_set(int(f),subframe=f%1);return snap()
def apply(p):
 attach(None)
 for n,(q,l)in p.items():
  b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l
 bpy.context.view_layer.update()
def blend(a,b,u):return {n:(a[n][0].slerp(b[n][0],u),a[n][1].lerp(b[n][1],u))for n in names}
def interp(a,f):
 f=max(0,min(len(a)-1,f));i=int(f);return blend(a[i],a[min(i+1,len(a)-1)],f-i)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def bump(t,a,b,c):return smooth((t-a)/(b-a))*(1-smooth((t-b)/(c-b)))
def world(n):return rig.pose.bones[n].matrix.copy()
def put(n,R):
 m=R.to_4x4();m.translation=world(n).translation;rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
def rotate(n,axis,degrees):put(n,Matrix.Rotation(math.radians(degrees),3,axis)@world(n).to_3x3())
def aim(n,child,T):
 m=world(n);put(n,(world(child).translation-m.translation).rotation_difference(T-m.translation).to_matrix()@m.to_3x3())
def leg(sd,T,R):
 th,ca,ft=[f'B_{sd}_{k}'for k in ['Thigh','Calf','Foot']];H=world(th).translation;K=world(ca).translation;A=world(ft).translation;a=(K-H).length;b=(A-K).length;D=T-H;d=min(D.length,(a+b)*.999);u=D.normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);N=H+a*(u*c+v*math.sqrt(max(0,1-c*c)));aim(th,ca,N);aim(ca,ft,T);put(ft,R)
old={r:[sample(bpy.data.actions[r],f)for f in range(int(bpy.data.actions[r].frame_range[1])+1)]for r in roles}
with bpy.data.libraries.load(str(P/'work/round2_sources.blend'))as(s,d):d.actions=['Overhead','Recoil']
src={r:[sample(bpy.data.actions[r],f)for f in range(int(bpy.data.actions[r].frame_range[1])+1)]for r in ['Overhead','Recoil']}
ST=old['Standing'][0];apply(ST);HOME={s:world(f'B_{s}_Foot')for s in 'LR'};PEL=world('B_Pelvis');SP=world('B_Spine2')
# Immutable local grip and joint bends; only their carrying parent frames move.
left=[f'B_L_{n}'for n in ['Clavicle','UpperArm','Forearm','Hand']]
durations={'Standing':3.,'Walking':.8,'Running':.8,'Attack':2.25,'Cast':1.4,'Hit':.7,'Death':1.30,'Dead':1.,'Fidget':3.}
allposes={}
for role in roles:
 if role=='Dead':continue
 poses=[]
 for fi in range(round(durations[role]*60)+1):
  t=fi/60;u=t/durations[role];p=interp(old[role],u*(len(old[role])-1));attack=False
  if role=='Attack':
   sf=max(0,(t-.12)*30);q=interp(src['Overhead'],sf);env=min(smooth(t/.22),smooth((2.25-t)/.35));p=blend(ST,q,env);attack=True
   for n in names:
    if 'Finger'in n or n in ['ForearmBlade','LeafShield','BladeTip'] or 'Twist'in n or n.startswith('Skirt_'):p[n]=ST[n]
  elif role=='Hit':
   q=interp(src['Recoil'],t*30);env=min(smooth(t/.075),smooth((.7-t)/.15));p=blend(ST,q,env)
   for n in names:
    if 'Finger'in n or n in ['ForearmBlade','LeafShield','BladeTip'] or 'Twist'in n or n.startswith('Skirt_'):p[n]=ST[n]
  elif role=='Fidget':p=ST.copy()
  elif role=='Death':
   # Drop the idle opening, accelerate the library fall, retain the floor-settling end.
   sf=np.interp(t,[0,.12,.36,.70,1.30],[0,85,155,215,276]);p=interp(old['Death'],sf)
  for n in left:p[n]=ST[n]
  if role=='Death':
   for n in [f'B_R_{x}'for x in ['Clavicle','UpperArm','Forearm','Hand']]:p[n]=ST[n]
  apply(p)
  if attack:
   wind=bump(t,.12,.62,.92);strike=bump(t,.62,1.00,1.90)
   m=PEL.copy();m.translation=PEL.translation+Vector((.025*wind,-.06*strike,-.09*strike));rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
   rotate('B_Spine','Y',8*wind);rotate('B_Spine','X',-5*wind)
   for sd in 'LR':
    T=HOME[sd].translation.copy()
    if sd=='R':
     step=smooth((t-.28)/.56)*(1-smooth((t-1.55)/.45));T.y-=.18*step
     T.z+=.12*bump(t,.20,.53,.85)+.065*bump(t,1.55,1.75,2.00)
    else:T.y+=.025*strike
    leg(sd,T,HOME[sd].to_3x3())
   # Guard rises with the chest, then opens away from the downward blade.
   rotate('B_L_UpperArm','X',-24*wind+8*strike);rotate('B_L_UpperArm','Z',-12*strike)
  elif role=='Hit':
   recoil=bump(t,0,.27,.7);m=PEL.copy();m.translation=PEL.translation+Vector((.012*recoil,.055*recoil,-.028*recoil));rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
   rotate('B_Spine','X',-15*recoil);rotate('B_Neck','X',-8*recoil)
   for sd in 'LR':leg(sd,HOME[sd].translation,HOME[sd].to_3x3())
   rotate('B_L_UpperArm','X',-24*recoil);rotate('B_L_UpperArm','Y',-12*recoil)
  elif role=='Fidget':
   shift=math.sin(math.pi*u)**2;look=math.sin(math.tau*u)*shift
   m=world('B_Pelvis');m.translation+=Vector((.025*look,0,-.008*shift));rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
   rotate('B_Spine','Z',7*look);rotate('B_Neck','Z',18*look);rotate('B_Head','Y',4*shift)
   rotate('B_R_UpperArm','X',-12*shift);rotate('B_L_UpperArm','X',-15*shift);rotate('B_L_UpperArm','Z',-9*look)
   for sd in 'LR':leg(sd,HOME[sd].translation,HOME[sd].to_3x3())
  elif role in ['Walking','Running','Standing','Cast']:
   amp={'Standing':2.5,'Walking':14,'Running':18,'Cast':24}[role]
   swing=math.sin(math.tau*u)if role!='Cast'else -math.sin(math.pi*u)**2
   rotate('B_L_UpperArm','X',amp*swing)
   if role=='Cast':rotate('B_L_UpperArm','Z',-10*math.sin(math.pi*u)**2)
  elif role=='Death':
   # Preserve the fitted floor pose, but remove the world-fixed board during the reaction.
   react=bump(t,0,.32,.95);rotate('B_L_UpperArm','X',-30*react);rotate('B_L_UpperArm','Y',-16*react)
  poses.append(snap())
 allposes[role]=poses
allposes['Dead']=[allposes['Death'][-1]]*61
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for role,poses in allposes.items():
 a=bpy.data.actions.new(role);a.use_fake_user=True;attach(a);prev={}
 for f,p in enumerate(poses):
  for n,(q,l)in p.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
 for lay in a.layers:
  for strip in lay.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
ns=runpy.run_path(str(P/'scripts/bake_twist.py'))
for a in bpy.data.actions:ns['bake_twist'](a)
attach(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
assert len(rig.data.bones)==119
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2_motion.blend'))
(P/'review/round2/motion_provenance.json').write_text(json.dumps({'durations':durations,'attack':'anim_library/mixamo/Standing Melee Attack Downward.fbx','hit':'anim_library/mixamo/Sword And Shield Impact (1).fbx','death':'Dying Backwards retained, nonuniform time remap removes opening pause','fidget':'Native stance-derived visible weight shift, glance and equipment adjustment; authored gap fill','shield':'Fixed fitted local grip, shoulder/torso participation, no world orientation clamp'},indent=2))
