import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;r=s.objects['Goblin_Combat_Rig'];rest={b.name:b.matrix_local.copy() for b in r.data.bones};grip=json.loads((OUT/'grip_pose.json').read_text());bindhand=rest['mixamorig:RightHand'];griplocal=Vector((.041,.100,0));qidentity=Quaternion();previous={};reports={};polehistory={}
# Six native frames at 0.125-second intervals, plus recovery to the armed stance.
KEYS=[
 (0,dict(twist=0,lean=1,r=(-.24,-.26,1.06),l=(.28,-.12,.91),d=(.82,-.24,.52),lift=0)),
 (.125,dict(twist=24,lean=-3,r=(.14,-.32,1.28),l=(.28,-.23,1.10),d=(.54,-.12,.83),lift=.025)),
 (.25,dict(twist=12,lean=0,r=(.13,-.37,1.29),l=(.20,-.31,1.16),d=(.51,-.18,.84),lift=.025)),
 (.375,dict(twist=-8,lean=7,r=(-.28,-.43,1.11),l=(.04,-.36,1.04),d=(.28,-.94,-.20),lift=.008)),
 (.50,dict(twist=-24,lean=13,r=(-.40,-.31,1.01),l=(.00,-.32,.92),d=(-.96,-.23,-.14),lift=0)),
 (.625,dict(twist=-6,lean=4,r=(-.29,-.27,1.03),l=(.26,-.16,.90),d=(.08,-.94,-.33),lift=0)),
 (.75,dict(twist=0,lean=1,r=(-.24,-.26,1.06),l=(.28,-.12,.91),d=(.82,-.24,.52),lift=0))]
for (_,params),pole in zip(KEYS,[(-.40,-.22,1.15),(-.30,-.36,1.32),(-.30,-.36,1.32),(-.46,-.30,1.27),(-.48,-.12,1.18),(-.43,-.18,1.16),(-.40,-.22,1.15)]):params['pole']=pole
def interpolate(t):
 for (ta,a),(tb,b) in zip(KEYS,KEYS[1:]):
  if t<=tb:
   f=max(0,(t-ta)/(tb-ta));f=f*f*(3-2*f);return {k:tuple(x+(y-x)*f for x,y in zip(a[k],b[k])) if isinstance(a[k],tuple) else a[k]+(b[k]-a[k])*f for k in a}
 return KEYS[-1][1]
def frame_from(y,x):
 y=y.normalized();x=x-y*x.dot(y)
 if x.length<.00001:x=Vector((1,0,0))-y*y.x
 x.normalize();z=x.cross(y).normalized();return Matrix((x,y,z)).transposed()
def solve(A,W,L1,L2,pole,blade=None,side='Right'):
 delta=W-A;dist=min(max(delta.length,.03),L1+L2-.002);axis=delta.normalized();W=A+axis*dist;along=(L1*L1-L2*L2+dist*dist)/(2*dist);height=math.sqrt(max(.000001,L1*L1-along*along));C=A+axis*along;u=Vector(pole)-C;u-=axis*u.dot(axis);u.normalize();v=axis.cross(u);E=C+height*u
 if False and blade is not None:
  D=blade.normalized();aa=u.dot(D);bb=v.dot(D);amp=math.hypot(aa,bb);target=(W-C).dot(D)/height
  if amp>.00001:
   phase=math.atan2(bb,aa);alpha=math.acos(max(-1,min(1,target/amp)));options=[C+height*(u*math.cos(phase+sgn*alpha)+v*math.sin(phase+sgn*alpha)) for sgn in [-1,1]]
   ref=polehistory.get(side,E);E=min(options,key=lambda p:(p-(C+height*u)).length_squared+.6*(p-ref).length_squared)
 polehistory[side]=E.copy();return E,W

def inherited(name,poses):
 b=r.data.bones[name];return poses[b.parent.name]@rest[b.parent.name].inverted()@rest[name] if b.parent else rest[name].copy()
def aim(name,A,B,poses):
 old=rest[name];q=(r.data.bones[name].tail_local-r.data.bones[name].head_local).rotation_difference(B-A)@old.to_quaternion();poses[name]=Matrix.Translation(A)@q.to_matrix().to_4x4()
def arm_pose(side,handle,blade,poses,left_wrist=None,pole_override=None):
 pre='mixamorig:'+side;upper,lower,hand=pre+'Arm',pre+'ForeArm',pre+'Hand';A=inherited(upper,poses).translation;L1=(rest[lower].translation-rest[upper].translation).length;L2=(rest[hand].translation-rest[lower].translation).length;sign=-1 if side=='Right' else 1;pole=Vector(pole_override) if pole_override is not None else Vector((sign*.41,-.22,1.13))
 if side=='Right':
  D=Vector(blade).normalized();W=Vector(handle)-Vector((0,0,-.07));handq=rest[hand].to_quaternion()
  for iteration in range(4):
   E,W=solve(A,W,L1,L2,pole,D,side);F=(W-E).normalized();Y=F-D*F.dot(D)
   if Y.length<.001:Y=Vector((0,0,-1))
   Y.normalize()
   if F.angle(Y)>math.radians(25):Y=Quaternion().slerp(F.rotation_difference(Y),math.radians(25)/F.angle(Y))@F
   Z=-(D-Y*D.dot(Y)).normalized();X=Y.cross(Z).normalized();handq=Matrix((X,Y,Z)).transposed().to_quaternion();W=Vector(handle)-handq@griplocal
  E,W=solve(A,W,L1,L2,pole,D,side);F=(W-E).normalized();Y=F-D*F.dot(D)
  if Y.length<.001:Y=Vector((0,0,-1))
  Y.normalize();bend_angle=F.angle(Y)
  if bend_angle>math.radians(25):Y=Quaternion().slerp(F.rotation_difference(Y),math.radians(25)/bend_angle)@F
  Z=-(D-Y*D.dot(Y)).normalized();X=Y.cross(Z).normalized();handq=Matrix((X,Y,Z)).transposed().to_quaternion();foreq=frame_from(F,X).to_quaternion()
  # Local bind axes of forearm and hand need not have equal roll. Match the transformed hand basis.
  rel=rest[lower].to_quaternion().inverted()@rest[hand].to_quaternion();foreX=handq@(rel.inverted()@Vector((1,0,0)));foreq=frame_from(F,foreX).to_quaternion()
  poses[hand]=Matrix.Translation(W)@handq.to_matrix().to_4x4();poses[lower]=Matrix.Translation(E)@foreq.to_matrix().to_4x4();bend=math.degrees(F.angle(Y))
 else:
  W=Vector(left_wrist);E,W=solve(A,W,L1,L2,pole,None,side);aim(lower,E,W,poses);q=poses[lower].to_quaternion()@rest[lower].to_quaternion().inverted()@rest[hand].to_quaternion();poses[hand]=Matrix.Translation(W)@q.to_matrix().to_4x4();bend=0
 # Upper-arm roll follows a stable elbow plane instead of an arbitrary shortest-arc twist.
 U=(E-A).normalized();F=(W-E).normalized();normal=U.cross(F)
 if normal.length<.001:normal=Vector((0,-1,0))
 normal.normalize();oldU=(rest[lower].translation-rest[upper].translation).normalized();oldF=(rest[hand].translation-rest[lower].translation).normalized();oldN=oldU.cross(oldF)
 if oldN.length<.001:oldN=Vector((0,-1,0))
 oldN.normalize();rot=frame_from(U,normal)@frame_from(oldU,oldN).transposed();poses[upper]=Matrix.Translation(A)@rot.to_4x4()@rest[upper].to_quaternion().to_matrix().to_4x4();return bend

def apply(poses):
 for b in r.data.bones:
  if b.name.startswith('Finger.R.'):
   p=r.pose.bones[b.name];p.location=grip[b.name]['location'];p.rotation_quaternion=grip[b.name]['rotation'];p.scale=(1,1,1);poses[b.name]=poses[b.parent.name]@rest[b.parent.name].inverted()@rest[b.name]@p.matrix_basis;continue
  if b.name not in poses:poses[b.name]=inherited(b.name,poses)
  kwargs={'parent_matrix':poses[b.parent.name],'parent_matrix_local':rest[b.parent.name]} if b.parent else {}
  r.pose.bones[b.name].matrix_basis=b.convert_local_to_pose(poses[b.name],rest[b.name],invert=True,**kwargs)
 bpy.context.view_layer.update()
def attack_pose(t):
 p=interpolate(t);poses={}
 for name,frac in [('Hips',.18),('Spine',.45),('Spine1',.75),('Spine2',1),('Neck',.75),('Head',.60)]:
  name='mixamorig:'+name;M=inherited(name,poses);q=Quaternion((0,0,1),math.radians(p['twist']*frac))@Quaternion((1,0,0),math.radians(p['lean']*frac));poses[name]=Matrix.Translation(M.translation)@q.to_matrix().to_4x4()@rest[name].to_quaternion().to_matrix().to_4x4()
  if name=='mixamorig:Hips':poses[name].translation+=Vector((0,-.008,-.023))
 for side,sign in [('Right',-1),('Left',1)]:
  pre='mixamorig:'+side;up,lo,foot=pre+'UpLeg',pre+'Leg',pre+'Foot';A=inherited(up,poses).translation;W=rest[foot].translation.copy();W.x+=sign*.015
  if side=='Left':W.z+=p['lift']
  E,W=solve(A,W,(rest[lo].translation-rest[up].translation).length,(rest[foot].translation-rest[lo].translation).length,(sign*.25,-1,.5),side=side+'Leg');aim(up,A,E,poses);aim(lo,E,W,poses);poses[foot]=rest[foot].copy();poses[foot].translation=W
  shoulder=pre+'Shoulder';poses[shoulder]=inherited(shoulder,poses)
 bend=arm_pose('Right',p['r'],p['d'],poses,pole_override=p['pole']);arm_pose('Left',None,None,poses,p['l']);apply(poses);return bend

def bake(name,source=None,attack=False):
 polehistory.clear();old=bpy.data.actions.get(name)
 if old:old.name=name+'_study'
 action=bpy.data.actions.new(name);action.use_fake_user=True;prev={};samples=[]
 if attack:frames=[1+i*.5 for i in range(37)]
 else:frames=list(range(math.floor(source.frame_range[0]),math.ceil(source.frame_range[1])+1))
 for f in frames:
  if source:
   r.animation_data.action=source;r.animation_data.action_slot=source.slots[0];s.frame_set(int(f),subframe=f-int(f));poses={p.name:p.matrix.copy() for p in r.pose.bones if not p.name.startswith('Finger.') and p.name!='Weapon.R'};chest=poses['mixamorig:Spine2']@rest['mixamorig:Spine2'].inverted();hip=poses['mixamorig:Hips']@rest['mixamorig:Hips'].inverted();center=hip@Vector((-.24,-.26,1.06));D=chest.to_quaternion()@Vector((.82,-.24,.52));r.animation_data.action=None;bend=arm_pose('Right',center,D,poses);apply(poses)
  else:
   r.animation_data.action=None;bend=attack_pose((f-1)/24)
  r.animation_data.action=action
  for pb in r.pose.bones:
   pb.rotation_mode='QUATERNION'
   if pb.name in prev:pb.rotation_quaternion.make_compatible(prev[pb.name])
   prev[pb.name]=pb.rotation_quaternion.copy()
   for attr in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=attr,frame=f,group=pb.name)
  samples.append({'frame':f,'right_wrist_bend_deg':bend})
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for kp in fc.keyframe_points:kp.interpolation='LINEAR'
 reports[name]=samples;return action
for tr in list(r.animation_data.nla_tracks):r.animation_data.nla_tracks.remove(tr)
for p in r.pose.bones:p.rotation_mode='QUATERNION'
jobs=[('MM6_Goblin_Idle','Idle_3'),('MM6_Goblin_Walk','Walking'),('MM6_Goblin_Run','Running'),('MM6_Goblin_GripRest','restpose'),('MM6_Goblin_Attack',None)];actions=[]
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   for a in actions:
    tr=r.animation_data.nla_tracks.new();tr.name=a.name;st=tr.strips.new(a.name,int(a.frame_range[0]),a);st.action_slot=a.slots[0];tr.mute=True
   a=actions[-1];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_start=1;s.frame_end=19;s.frame_set(4);(OUT/'attack_keys.json').write_text(json.dumps(KEYS,indent=2));(OUT/'wrist_bend_report.json').write_text(json.dumps(reports,indent=2));(OUT/'motion_done.txt').write_text('complete');return None
  name,key=jobs.pop(0);actions.append(bake(name,bpy.data.actions['Goblin_Skirt_'+key] if key else None,attack=key is None));(OUT/'motion_progress.txt').write_text(name);return .1
 except Exception:(OUT/'motion_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print('Baking armed locomotion and native 0.75-second attack')
