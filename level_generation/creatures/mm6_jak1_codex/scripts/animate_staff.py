"""Library motions with anatomical arm frames, measured palms, two-hand grip and sole-plane IK."""
import bpy,math,json,sys,os,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_grip.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30
from hand_weights import repair_hand_weights
repair_hand_weights(body,rig)
from hand_rest_roll import restore,apply as roll_palms
restore(body,rig)
from thumb_cmc import repair_thumbs
repair_thumbs(body,rig)
roll_palms(body,rig)
with bpy.data.libraries.load(str(P/'work/round2_sources.blend')) as (src,dst):dst.actions=['Staff2','Cast1','Cast2','Cast3','Summon','DeathMixamo','StaffFall']
from staff_ik import Side,swing_twist_deg
R=Side('R');L=Side('L');names=[b.name for b in rig.pose.bones]
G=json.loads((P/'work/grip_pose.json').read_text());GL=json.loads((P/'work/grip_pose_left.json').read_text())
L.grip_hand=Vector(GL['handle_centre_hand_local']);L.axis_hand=Vector(GL['handle_axis_hand_local'])
def setact(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 setact(a);scene.frame_set(int(f),subframe=float(f-int(f)))
 return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names}
def apply(p):
 setact(None)
 for n,(q,l)in p.items():
  pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.scale=(1,1,1)
 bpy.context.view_layer.update()
def pose():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names}
def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
def softmax(a,b,width=.015):return max(a,b)+width*math.log1p(math.exp(-abs(a-b)/width))
def mix(a,b,u):return {n:(a[n][0].slerp(b[n][0],u),a[n][1].lerp(b[n][1],u))for n in names}
def world(n):return rig.matrix_world@rig.pose.bones[n].matrix
def put(n,R3):
 pb=rig.pose.bones[n];m=R3.to_4x4();m.translation=world(n).translation;pb.matrix=rig.matrix_world.inverted()@m;bpy.context.view_layer.update()
def aim(n,child,target):
 m=world(n);cur=world(child).translation-m.translation;q=cur.rotation_difference(target-m.translation);put(n,q.to_matrix()@m.to_3x3())
def leg_target(side,T,rot,pole):
 th,ca,ft=f'B_{side}_Thigh',f'B_{side}_Calf',f'B_{side}_Foot';H=world(th).translation;K=world(ca).translation;A=world(ft).translation;a=(K-H).length;b=(A-K).length;d=min((T-H).length,(a+b)*.999);u=(T-H).normalized();v=(pole-u*pole.dot(u)).normalized();co=(a*a+d*d-b*b)/(2*a*d);N=H+a*(u*co+v*math.sqrt(max(0,1-co*co)));aim(th,ca,N);aim(ca,ft,T);put(ft,rot)
def frame(axis,normal):
 a=axis.normalized();n=(normal-a*normal.dot(a)).normalized();return Matrix((a,n,a.cross(n))).transposed()
# Palm normals are the direction of finger flexion on this mesh, not an unsigned knuckle cross product.
PALM={s:Vector(json.loads((P/'work/hand_rest_roll.json').read_text())[s]['palm_local'])for s in 'LR'}
SOURCE_PALM={s:rig.data.bones[f'B_{s}_Hand'].matrix_local.to_3x3().inverted()@Vector((0,1,0))for s in 'LR'}
SOURCE_GRIP={s:json.loads((P/f'work/grip_pose{suffix}_unrolled.json').read_text())for s,suffix in [('R',''),('L','_left')]}
LONG={s:(rig.data.bones[f'B_{s}_Hand'].matrix_local.inverted()@rig.data.bones[f'B_{s}_Finger2'].head_local).normalized() for s in 'LR'}
def hand_rot(side,axis,normal,grip=True):
 local=(R if side=='R' else L).axis_hand if grip else LONG[side]
 return frame(axis,normal)@frame(local,PALM[side]).inverted()
source={a.name:[sample(a,f)for f in range(int(a.frame_range[1])+1)]for a in bpy.data.actions if a.name in ['Standing','Walking','Hit','Death','Fidget','Staff2','Cast1','Cast2','Cast3','Summon','DeathMixamo','StaffFall']}
# Smooth the source key corners before fitting; duration and the library's full-body motion are retained.
for clip in ['Staff2','Cast1','StaffFall']:
 raw=source[clip];filtered=[];sigma=3 if clip=='StaffFall' else 2;kernel=np.exp(-.5*(np.arange(-9,10)/sigma)**2);kernel/=kernel.sum()
 for i,center in enumerate(raw):
  row={}
  for n in names:
   quats=[];locations=[]
   for j in range(-9,10):
    q,l=raw[max(0,min(len(raw)-1,i+j))][n];q=q.copy()
    if q.dot(center[n][0])<0:q=-q
    quats.append(tuple(q));locations.append(tuple(l))
   row[n]=(Quaternion(tuple(kernel@np.array(quats))).normalized(),Vector(kernel@np.array(locations)))
  filtered.append(row)
 source[clip]=filtered
source['Staff2']=source['Staff2'][6:31]
source['Cast1']=source['Cast1'][5:26]
(P/'work/source_smoothing.json').write_text(json.dumps({'clips':['StaffAttack2','StaffCastLAttack1','StaffDeath1'],'sigma_seconds':{'StaffAttack2':2/30,'StaffCastLAttack1':2/30,'StaffDeath1':3/30},'kernel_frames':19,'filter_preserves_duration':True,'subsequent_crop_frames':{'StaffAttack2':[6,30],'StaffCastLAttack1':[5,25]},'final_timing':'work/action_timing.json'},indent=2))
ST=source['Standing'][0]
# Measure the full support patch, including its transverse slope. A heel/toe test alone misses cant.
with bpy.data.libraries.load(str(P/'work/production_body.blend')) as (src,dst):dst.objects=['Body']
sole_body=dst.objects[0];scene.collection.objects.link(sole_body);sole_body.parent=rig;sole_body.matrix_world=body.matrix_world
for mod in sole_body.modifiers:
 if mod.type=='ARMATURE':mod.object=rig
sole_ids={};foot_ids={}
for sd in 'LR':
 ids=[v.index for v in sole_body.data.vertices if sum(g.weight for g in v.groups if sole_body.vertex_groups[g.group].name.startswith((f'B_{sd}_Foot',f'B_{sd}_Toe')))>.5];z=min(sole_body.data.vertices[i].co.z for i in ids);sole_ids[sd]=[i for i in ids if sole_body.data.vertices[i].co.z<z+.006]
 foot_ids[sd]=ids
 assert len(sole_ids[sd])>=8

def soles(sd,full=False):
 ev=sole_body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out=np.array([tuple(sole_body.matrix_world@me.vertices[i].co)for i in (foot_ids[sd] if full else sole_ids[sd])]);ev.to_mesh_clear();return out

def flat_feet():
 for sd in 'LR':
  for _ in range(2):
   pts=soles(sd);n=Vector(np.linalg.svd(pts-pts.mean(0))[2][-1]);n*=1 if n.z>0 else -1;m=world(f'B_{sd}_Foot');put(f'B_{sd}_Foot',n.rotation_difference(Vector((0,0,1))).to_matrix()@m.to_3x3())
  pts=soles(sd);ids=sole_ids[sd];ys=[sole_body.data.vertices[i].co.y for i in ids];lo,hi=min(ys),max(ys)
  heel=Vector(min([v for v,y in zip(pts,ys) if y>hi-(hi-lo)*.25],key=lambda v:v[2]));toe=Vector(min([v for v,y in zip(pts,ys) if y<lo+(hi-lo)*.25],key=lambda v:v[2]));d=toe-heel;put(f'B_{sd}_Foot',d.rotation_difference(Vector((d.x,d.y,0))).to_matrix()@world(f'B_{sd}_Foot').to_3x3())
  pts=soles(sd);m=world(f'B_{sd}_Foot');target=m.translation.copy();target.z+=.002-pts[:,2].min();leg_target(sd,target,m.to_3x3(),Vector((0,-1,0)))
apply(ST);flat_feet();ST=pose();HOME={sd:world(f'B_{sd}_Foot').copy() for sd in 'LR'};PEL=world('B_Pelvis').copy()
WALK_HOME={}
for sd in 'LR':
 m=HOME[sd].copy();d=world(f'B_{sd}_Toe0').translation-m.translation;d.z=0;goal=Vector((math.sin(math.radians(5))*(1 if sd=='L' else -1),-math.cos(math.radians(5)),0));WALK_HOME[sd]=d.rotation_difference(goal).to_matrix()@m.to_3x3()
walk_peaks={sd:0.0 for sd in 'LR'}
for p in source['Walking']:
 apply(p);low={sd:soles(sd)[:,2].min() for sd in 'LR'}
 for sd in 'LR':walk_peaks[sd]=max(walk_peaks[sd],low[sd]-min(low.values()))
with bpy.data.libraries.load(str(P/'work/staff_clay.blend')) as (src,dst):dst.objects=['Staff']
prop=dst.objects[0];propco=[v.co-Vector((0,0,1.12)) for v in prop.data.vertices];bpy.data.objects.remove(prop,do_unlink=True)
hrest=rig.data.bones['B_R_Hand'].matrix_local.to_3x3();arest=(hrest@R.axis_hand).normalized();prop_hand=hrest.inverted()@arest.to_track_quat('Z','Y').to_matrix()@Matrix.Rotation(math.radians(245),3,'Z')
def staff_floor(rot):return .005-min((rot@prop_hand@v).z for v in propco)
def floor_feet():
 for sd in 'LR':
  m=world(f'B_{sd}_Foot');dz=max(0,.003-soles(sd,True)[:,2].min());T=m.translation.copy();T.z+=dz
  if dz:leg_target(sd,T,m.to_3x3(),Vector((0,-1,0)))
baseG=Vector((-.36,-.24,1.14));Z=Vector((0,0,1));holdRh=hand_rot('R',Z,Vector((1,0,0)))
# Free-hand relaxed curl retains the fitted knuckle spread correction without making a fist.
left_relax={n:Quaternion().slerp(Quaternion(q),.65 if n in [f'B_L_Finger{i}'for i in range(5)] else .35) for n,q in GL['finger_local'].items()}

def arm(side,target,Rh,pole):
 obj=R if side=='R' else L
 # The elbow remains on the anatomical side; choose the nearby pole with the least upper-arm roll.
 S=world(f'B_{side}_UpperArm').translation;W=target-Rh@obj.grip_hand;axis=(W-S).normalized();candidates=[]
 if getattr(obj,'previous_elbow',None) is not None:
  previous=obj.previous_elbow-S;previous-=axis*previous.dot(axis);desired=pole-axis*pole.dot(axis)
  if previous.length>.001:
   previous.normalize();desired.normalize();turn=math.atan2(previous.cross(desired).dot(axis),previous.dot(desired));pole=Quaternion(axis,max(-.035,min(.035,turn)))@previous
  angles=range(-2,3)
 else:angles=range(-100,101,5)
 for deg in angles:
  result=obj.pose_anatomical(target,Rh,Quaternion(axis,math.radians(deg))@pole)
  parent=world(f'B_{side}_Clavicle').to_3x3()@obj.rel['Arm'];q=(parent.inverted()@result['Ra']).to_quaternion();roll=abs(swing_twist_deg(q,obj.uA)[1]);cost=max(0,roll-45)*5+roll*.15+abs(deg)*.15
  if getattr(obj,'previous_Ra',None) is not None:cost+=2.0*math.degrees(obj.previous_Ra.to_quaternion().rotation_difference(result['Ra'].to_quaternion()).angle)
  if role=='Death':cost+=10000*max(0,.055-result['E'].z,.055-result['W'].z)
  if (side=='R' and (role!='Death' or f/30<.25)) or role=='Attack':
   ax=(Rh@obj.axis_hand).normalized();depth=0
   for u in [.15,.3,.5,.7,.9,1]:
    d=result['E'].lerp(result['W'],u)-target;rad=(d-ax*d.dot(ax)).length;depth=max(depth,.060-.020*u-rad)
   cost+=max(0,depth)*10000
  candidates.append((cost,result,roll))
 _,result,roll=min(candidates,key=lambda x:x[0]);obj.apply(result);return result['miss'],roll

def free_hand(Rh=None):
 # Keep the source wrist travel, with a palm toward the thigh and a modest forward elbow bend.
 m=world('B_L_Hand');T=m.translation.copy();T.x=softmax(T.x,.39);T.z+=.02
 if Rh is None:
  normal=world('B_L_Thigh').translation-T;normal.z=0;Rh=hand_rot('L',Vector((0,0,-1)),normal,False)
 grip=T+Rh@L.grip_hand
 return arm('L',grip,Rh,Vector((.3,1,-.2)))

def key_actions(allposes):
 scene.render.fps=240
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 for role,frames in allposes.items():
  act=bpy.data.actions.new(role);act.use_fake_user=True;setact(act);prev={}
  for f,p in enumerate(frames):
   for n,(q,l)in p.items():
    if n in prev and q.dot(prev[n])<0:q=-q
    prev[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f)
    if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
  act.use_frame_range=True;act.frame_start=0;act.frame_end=len(frames)-1
  for layer in act.layers:
   for strip in layer.strips:
    for cb in strip.channelbags:
     for fc in cb.fcurves:
      for k in fc.keyframe_points:k.interpolation='LINEAR'
 setact(None)

# Average the library's two-hand roll once; both grip frames remain rigid throughout the strike.
grip_frames=[]
for row in source['Staff2']:
 apply(row);hr,hl=world('B_R_Hand'),world('B_L_Hand');cr=hr@Vector(SOURCE_GRIP['R']['handle_centre_hand_local']);cl=hl@Vector(SOURCE_GRIP['L']['handle_centre_hand_local']);axis=(cl-cr).normalized();rr=hand_rot('R',axis,hr.to_3x3()@SOURCE_PALM['R']);rl=hand_rot('L',axis,hl.to_3x3()@SOURCE_PALM['L']);grip_frames.append(tuple((rr.inverted()@rl).to_quaternion()))
_,vectors=np.linalg.eigh(np.array(grip_frames).T@np.array(grip_frames));fixed_grip=Quaternion(tuple(vectors[:,-1])).to_matrix()
allposes={};ikreport={};provenance={}
roles=os.environ.get('ROUND2_ROLES','Standing,Walking,Attack,Cast,Hit,Death,Fidget').split(',')
for role in roles:
 for obj in [L,R]:obj.previous_Ra=None;obj.previous_Rf=None;obj.previous_elbow=None
 srcrole={'Attack':'Staff2','Cast':'Cast1','Death':'StaffFall'}.get(role,role);src=source[srcrole];lead=12 if role=='Attack' else 9 if role=='Cast' else 0;outro=lead;count=len(src)+lead+outro;frames=[];errors=[];rolls=[]
 apply(src[0]);srcPel=world('B_Pelvis').copy();source_grip0=world('B_R_Hand')@R.grip_hand
 for fi in range((count-1)*8+1):
  prior_R={n:getattr(R,n,None).copy() if getattr(R,n,None) is not None else None for n in ['previous_elbow','previous_Ra','previous_Rf']}
  f=fi/8;j=max(0,min(len(src)-1,f-lead));t=f/max(1,count-1)
  if role in ('Attack','Cast'):
   if j<6:u=j/6;j=6*(-u**3+2*u*u)
   elif j>len(src)-1-6:u=(len(src)-1-j)/6;j=len(src)-1-6*(-u**3+2*u*u)
  k=int(j);p=mix(src[k],src[min(k+1,len(src)-1)],j-k)
  weight=min(smooth(f/lead),smooth((count-1-f)/outro)) if lead else 1.0
  if role=='Hit':p=mix(ST,p,.35*min(smooth(f/4),smooth((count-1-f)/4)))
  if role=='Fidget':p=mix(ST,p,min(smooth(f/6),smooth((count-1-f)/6)))
  if role=='Death':p=mix(ST,p,smooth(f/9))
  apply(p)
  for sd in 'LR':rig.pose.bones[f'B_{sd}_Toe0'].rotation_quaternion=ST[f'B_{sd}_Toe0'][0]
  bpy.context.view_layer.update()
  if role=='Walking':
   m=world('B_Pelvis');m.translation.z=PEL.translation.z+.012*math.sin(t*math.tau*2)**2;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
  if role in ['Attack','Cast']:
   # Preserve library trunk/shoulder motion; only the stance is constrained for the native footprint.
   m=world('B_Pelvis');q0=PEL.to_quaternion();qs=srcPel.to_quaternion();qd=m.to_quaternion();m.translation=PEL.translation+(m.translation-srcPel.translation)*.2
   m=(q0.slerp(qd,.2)).to_matrix().to_4x4();m.translation=PEL.translation+(world('B_Pelvis').translation-srcPel.translation)*.2;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
   for sd in 'LR':
    foot=HOME[sd].copy();u=0;back=False
    if sd=='L':
     if j<2:u=0
     elif j<8:u=(j-2)/6
     elif j<len(src)-7:u=1
     else:u=(j-(len(src)-7))/6;back=True
     foot.translation.y-=.10*(1-smooth(u) if back else smooth(u));foot.translation.z+=.07*math.sin(math.pi*u) if 0<u<1 else 0
    leg_target(sd,foot.translation,foot.to_3x3(),Vector((0,-1,0)))
  if role=='Walking':
   low={sd:soles(sd)[:,2].min() for sd in 'LR'};ground=min(low.values())
   for sd in 'LR':
    m=world(f'B_{sd}_Foot');rot=WALK_HOME[sd];put(f'B_{sd}_Foot',rot);target=m.translation.copy();target.z+=.003+.083*max(0,low[sd]-ground)/walk_peaks[sd]-soles(sd)[:,2].min();leg_target(sd,target,rot,Vector((0,-1,0)))
  if role in ('Standing','Fidget'):
   for sd in 'LR':leg_target(sd,HOME[sd].translation,HOME[sd].to_3x3(),Vector((0,-1,0)))
   floor_feet()
  if role=='Death':
   # Relax pointed toes into the prone landing instead of retaining the upright ankle angle.
   for sd in 'LR':
    m=world(f'B_{sd}_Foot');toe=world(f'B_{sd}_Toe0').translation-m.translation;target=toe.copy();target.z=0
    if target.length>1e-6:put(f'B_{sd}_Foot',Quaternion().slerp(toe.rotation_difference(target),.65*smooth((f/30-.8)/.65)).to_matrix()@m.to_3x3())
   # Solve the core body's floor first, then constrain the arms/prop onto that grounded fall.
   ev=sole_body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
   ids=[v.index for v in sole_body.data.vertices if sum(g.weight for g in v.groups if any(k in sole_body.vertex_groups[g.group].name for k in ['UpperArm','Forearm','Hand','Finger','Clavicle']))<.2]
   bottom=min((sole_body.matrix_world@me.vertices[i].co).z for i in ids);ev.to_mesh_clear();m=world('B_Pelvis');
   m=world('B_Pelvis');m.translation.z+=.003-bottom;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()

  source_poles={sd:world(f'B_{sd}_Forearm').translation-world(f'B_{sd}_UpperArm').translation for sd in 'LR'}
  for n,q in left_relax.items():rig.pose.bones[n].rotation_quaternion=q
  for n,q in G['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion(q)
  bpy.context.view_layer.update()
  target=baseG.copy();axis=Z.copy();Rh=holdRh.copy()
  if role in ('Standing','Fidget'):
   target+=Vector((0,.004*math.sin(t*math.tau),.006*math.sin(t*math.tau)))
   if role=='Fidget':axis=Quaternion(Vector((1,0,0)),math.radians(4)*math.sin(t*math.tau))@Z
   Rh=Z.rotation_difference(axis).to_matrix()@holdRh
  elif role=='Walking':
   target+=Vector((0,.025*math.sin(t*math.tau),.012*math.sin(t*math.tau*2)));axis=Quaternion(Vector((1,0,0)),math.radians(5))@Z;Rh=Z.rotation_difference(axis).to_matrix()@holdRh
  elif role=='Hit':
   target+=Vector((0,.035*math.sin(math.pi*t),.05*math.sin(math.pi*t)));axis=Quaternion(Vector((1,0,0)),math.radians(-5)*math.sin(math.pi*t))@Z;Rh=Z.rotation_difference(axis).to_matrix()@holdRh
  elif role=='Attack':
   hr,hl=world('B_R_Hand'),world('B_L_Hand');cr=hr@Vector(SOURCE_GRIP['R']['handle_centre_hand_local']);cl=hl@Vector(SOURCE_GRIP['L']['handle_centre_hand_local'])
   axis=(cl-cr).normalized();center=(cr+cl)*.5;center.y=min(center.y,-.30)
   target=center-axis*.145;Rh=hand_rot('R',axis,hr.to_3x3()@SOURCE_PALM['R']);RhL=Rh@fixed_grip
   # Two grip points share a rigid shaft; project into both arms' reachable spheres, preserving the source arc.
   for _ in range(12):
    for sd,obj,rot,offset in [('R',R,Rh,Vector()),('L',L,RhL,axis*.29)]:
     center=world(f'B_{sd}_UpperArm').translation+rot@obj.grip_hand-offset;v=target-center;limit=(obj.l1+obj.l2)*.94
     if v.length>limit:target=center+v.normalized()*limit
  elif role=='Cast':
   hand=world('B_R_Hand');axis=(hand.to_3x3()@Vector(SOURCE_GRIP['R']['handle_axis_hand_local'])).normalized();axis=axis.lerp(Vector((0,-.85,.53)),.65*min(smooth(j/10),smooth((len(src)-1-j)/8))).normalized()
   axis.x=0;axis.normalize();Rh=hand_rot('R',axis,Vector((1,0,0)));target=hand.translation+Rh@R.grip_hand;target.y-=.04;target.x=min(target.x,-.39)
   center=world('B_R_UpperArm').translation+Rh@R.grip_hand;v=target-center;limit=(R.l1+R.l2)*.94
   if v.length>limit:target=center+v.normalized()*limit
  elif role=='Death':
   carry=world('B_Pelvis').to_3x3()@PEL.to_3x3().inverted();axis=(carry@Z).normalized();axis.x=0;axis.normalize();hold=hand_rot('R',axis,carry@Vector((1,0,0)));hand=world('B_R_Hand');source_wrist=hand.translation.copy();source_wrist.x=min(source_wrist.x,world('B_R_UpperArm').translation.x-.10);source_wrist.z=max(source_wrist.z,.105)
   source_wrist.x-=.065*smooth((f/30-.08)/.12)*(1-smooth((f/30-.35)/.25))
   source_wrist.x-=.06*math.sin(math.pi*max(0,min(1,(f/30-.15)/.55)))
   source_wrist.x-=.14*smooth((f/30-.25)/.10)*(1-smooth((f/30-.55)/.45))
   opened=smooth((f/30-.12)/.13);released=smooth((f/30-.20)/.25);free=hand_rot('R',carry@Vector((0,0,-1)),carry@Vector((1,0,0)),False);Rh=hold.to_quaternion().slerp(free.to_quaternion(),released).to_matrix();target=source_wrist+Rh@R.grip_hand
   hold_weight=1-released;floor_weight=1-smooth((f/30-.25)/.20);target.z+=floor_weight*max(0,staff_floor(Rh)-target.z);target.x+=hold_weight*min(0,world('B_Pelvis').translation.x-.38-target.x)
   enter=smooth(f/9);target=baseG.lerp(target,enter);Rh=holdRh.to_quaternion().slerp(Rh.to_quaternion(),enter).to_matrix()
   for n,q in G['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion(q).slerp(Quaternion().slerp(Quaternion(q),.45),smooth((f/30-.35)/.15) if n.startswith('B_R_Finger0') else opened)
  if role=='Death':
   center=world('B_R_UpperArm').translation+Rh@R.grip_hand;v=target-center;d=v.length;limit=.95*(R.l1+R.l2);safe=limit-.025*math.log1p(math.exp(min(40,(limit-d)/.025)))
   if d>1e-8:target=center+v*max(0,safe)/d
  err,roll=arm('R',target,Rh,source_poles['R'] if role=='Death' else Vector((-.35,1,-.4)));errors.append(err);rolls.append(roll)
  if role=='Attack':
   targetL=world('B_R_Hand')@R.grip_hand+axis*.29
   err,roll=arm('L',targetL,RhL,Vector((.5,1,-.4)));errors.append(err);rolls.append(roll)
   for n,q in GL['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion(q)
  elif role=='Cast':
   m=world('B_L_Hand');RhL=m.to_3x3()
   err,roll=free_hand(RhL);errors.append(err);rolls.append(roll)
  else:
   if role=='Death':
    m=world('B_L_Hand');T=m.translation.copy();T.x=max(T.x,.39*(1-smooth((f/30-.15)/.25)));T.z=softmax(T.z,.13);RhL=hand_rot('L',carry@Vector((0,0,-1)),carry@Vector((-1,0,0)),False);err,roll=arm('L',T+RhL@L.grip_hand,RhL,source_poles['L'])
   else:err,roll=free_hand()
   errors.append(err);rolls.append(roll)
  bpy.context.view_layer.update();pp=pose()
  if role in ['Attack','Cast']:
   lh=world('B_L_Hand');blendLW=IDLE_HAND['L'].translation.lerp(lh.translation,weight);blendLRh=IDLE_HAND['L'].to_quaternion().slerp(lh.to_quaternion(),weight).to_matrix()
   blendG=baseG.lerp(world('B_R_Hand')@R.grip_hand,weight);blendRh=holdRh.to_quaternion().slerp(world('B_R_Hand').to_quaternion(),weight).to_matrix();blendG.y-=.20*math.sin(math.pi*weight)
   pp=mix(allposes['Standing'][0],pp,weight)
  apply(pp)
  if role=='Cast' and weight<.999:
   targetL=blendLW+blendLRh@L.grip_hand;targetL.y-=.30*math.sin(math.pi*weight);targetL.x+=.10*math.sin(math.pi*weight)*(1-weight);arm('L',targetL,blendLRh,Vector((.5,1,-.4)))
  if role not in ('Death',):floor_feet()
  if role in ('Attack','Cast'):
   if weight<.999:
    for n,value in prior_R.items():setattr(R,n,value)
    arm('R',blendG,blendRh,Vector((-.35,1,-.4)))
   hr=world('B_R_Hand');rot=hr.to_3x3();g=hr@R.grip_hand;dz=max(0,staff_floor(rot)-g.z)
   if dz:
    g.z+=dz;arm('R',g,rot,Vector((-.35,1,-.4)))
   if role=='Attack':
    # Arrive with open fingers, close on the shaft, then open before withdrawing.
    entry=f/lead;leave=(f-lead-(len(src)-1))/outro
    reach=min(smooth(entry/.72),1-smooth((leave-.28)/.72));curl=min(smooth((entry-.72)/.28),1-smooth(leave/.28))
    hr=world('B_R_Hand');axis=(hr.to_3x3()@R.axis_hand).normalized();heldRh=hr.to_3x3()@fixed_grip;heldG=hr@R.grip_hand+axis*.29
    rh=IDLE_HAND['L'].to_quaternion().slerp(heldRh.to_quaternion(),reach).to_matrix();idleG=IDLE_HAND['L']@L.grip_hand;targetL=idleG.lerp(heldG,reach);targetL.y-=.30*math.sin(math.pi*reach);targetL.x+=.10*math.sin(math.pi*reach)*(1-reach)
    arm('L',targetL,rh,Vector((.5,1,-.4)))
    for n,q in GL['finger_local'].items():
     if n.startswith('B_L_Finger0'):
      opened=Quaternion(json.loads((P/'work/left_thumb_open.json').read_text())['quaternion'])if n=='B_L_Finger0'else Quaternion(q);target=opened.slerp(Quaternion(q),curl);rig.pose.bones[n].rotation_quaternion=left_relax[n].slerp(target,smooth(reach/.5))
     else:
      opened=left_relax[n].slerp(Quaternion(),smooth(reach/.5));rig.pose.bones[n].rotation_quaternion=opened.slerp(Quaternion(q),curl)
  frames.append(pose())
 allposes[role]=frames;ikreport[role]={'wrist_reach_error_max_m':max(errors),'upper_arm_roll_max_deg':max(rolls)};provenance[role]={'source_clip':srcrole,'source_seconds':(len(src)-1)/30,'lead_seconds':lead/30,'outro_seconds':outro/30,'baked_hz':240,'source_frame_window':{'Attack':[6,30],'Cast':[5,25]}.get(role)}
 if role=='Standing':
  apply(frames[0]);IDLE_HAND={sd:world(f'B_{sd}_Hand').copy()for sd in 'LR'}
bpy.data.objects.remove(sole_body,do_unlink=True)
from arm_path import refine_arm_paths
refine_arm_paths(allposes,apply,pose,world,L,R,P)
if 'Death' in allposes:allposes['Dead']=[allposes['Death'][-1] for _ in range(241)]
key_actions(allposes)
from bake_twist import bake_twist
for a in bpy.data.actions:
 if a.name!='Dead':bake_twist(a)
if 'Dead' in bpy.data.actions:
 setact(bpy.data.actions['Death']);scene.frame_set(len(allposes['Death'])-1);endtw={pb.name:pb.rotation_quaternion.copy() for pb in rig.pose.bones if 'Twist' in pb.name};setact(bpy.data.actions['Dead'])
 for f in range(241):
  for n,q in endtw.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
setact(None)
(P/'work/round2_motion_sources.json').write_text(json.dumps(provenance,indent=2))
# Rigid native staff uses a separate exportable bone and keeps its textured geometry.
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();hm=rig.data.bones['B_R_Hand'].matrix_local;C=hm@Vector(G['handle_centre_hand_local']);A=(hm.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();M=A.to_track_quat('Z','Y').to_matrix().to_4x4();M.translation=C
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');eb=rig.data.edit_bones.new('Staff');eb.head=C;eb.tail=C+M.to_3x3().col[1]*.1;eb.align_roll(M.to_3x3().col[2]);eb.parent=rig.data.edit_bones['B_R_Hand'];tip=rig.data.edit_bones.new('StaffTip');tip.head=M@Vector((.055,0,.76));tip.tail=tip.head+M.to_3x3().col[1]*.06;tip.align_roll(M.to_3x3().col[2]);tip.parent=eb;bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(P/'work/staff_clay.blend'))as(src,dst):dst.objects=['Staff']
staff=dst.objects[0];scene.collection.objects.link(staff);staff.name='StaffMesh';staff.data.transform(M@Matrix.Translation((0,0,-1.12)));staff.parent=rig;vg=staff.vertex_groups.new(name='Staff');vg.add(list(range(len(staff.data.vertices))),1,'REPLACE');mod=staff.modifiers.new('Armature','ARMATURE');mod.object=rig
scene['staff_grip_from_foot']=1.12
(P/'work/ik_report.json').write_text(json.dumps(ikreport,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animated_master.blend'))
print('IK',ikreport,flush=True)
