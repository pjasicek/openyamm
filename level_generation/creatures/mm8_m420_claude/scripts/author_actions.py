"""Native staff fidget and charge lead; source casting/recoil/fall retain their motion rates."""
import bpy,sys,math,json
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot_carry.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
names=[b.name for b in rig.pose.bones]
def select(a):
 rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 select(a);sc.frame_set(int(f),subframe=float(f%1))
 return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def apply(p):
 select(None)
 for n,(q,l) in p.items():
  b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l
 bpy.context.view_layer.update()
def ease(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def blend(a,b,u):return {n:(a[n][0].slerp(b[n][0],u),a[n][1].lerp(b[n][1],u)) for n in names}
def write(name,poses):
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 a=bpy.data.actions.new(name);a.use_fake_user=True;select(a);prev={}
 for i,p in enumerate(poses):
  sc.frame_set(i)
  for n,(q,l) in p.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l
   b.keyframe_insert('rotation_quaternion',frame=i)
   if n=='B_Pelvis':b.keyframe_insert('location',frame=i)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
 return a
st=sample(bpy.data.actions['Standing'],0)
# Forward presentation starts at source frame 6; preserve that gesture's velocity.
atk=bpy.data.actions['AttackSource'];source=[sample(atk,f) for f in range(31)];lead=31
poses=[blend(st,source[0],ease(f/lead)) for f in range(lead)]+source
for i in range(len(poses)-9,len(poses)):poses[i]=blend(poses[i],st,ease((i-(len(poses)-10))/9))
# The long coat needs the playbook's soft torso-twist limit; retain the source's head direction.
spine=['B_Spine','B_Spine1','B_Spine2'];child={'B_Spine':'B_Spine1','B_Spine1':'B_Spine2','B_Spine2':'B_Neck','B_Neck':'B_Head'}
axes={n:(rig.data.bones[n].matrix_local.to_3x3().inverted()@(rig.data.bones[c].head_local-rig.data.bones[n].head_local)).normalized() for n,c in child.items()}
def split(q,axis):
 t=(2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi
 return q@Quaternion(axis,t).inverted(),t
limits=[]
for pose in poses:
 parts={n:split(pose[n][0],axes[n]) for n in child};total=sum(parts[n][1] for n in spine);free,cap=map(math.radians,[30,45]);limited=total
 if abs(total)>free:
  limited=math.copysign(free+(cap-free)*math.tanh((abs(total)-free)/(cap-free)),total)
  for n in spine:pose[n]=(parts[n][0]@Quaternion(axes[n],parts[n][1]*limited/total),pose[n][1])
  pose['B_Neck']=(parts['B_Neck'][0]@Quaternion(axes['B_Neck'],parts['B_Neck'][1]+total-limited),pose['B_Neck'][1])
 limits.append([math.degrees(total),math.degrees(limited)])
(P/'work/attack_spine_limit.json').write_text(json.dumps(limits))
write('Attack',poses)
# Hit is the source's change from its initial guard, carried by this mage's standing pose.
hit=bpy.data.actions['HitSource'];h0=sample(hit,0);poses=[]
for i in range(20):
 s=sample(hit,min(15,i));p=dict(st);u=ease(i/3)*ease((19-i)/5)
 for n in names:
  if any(t in n for t in ['Spine','Neck','Head','Clavicle','UpperArm','Forearm','Hand']):
   q=st[n][0]@(h0[n][0].inverted()@s[n][0]);p[n]=(st[n][0].slerp(q,u),st[n][1])
 poses.append(p)
write('Hit',poses)
# Smooth entry into the existing backward/side fall; keep the corpse pose.
death=bpy.data.actions['Death'];poses=[sample(death,f) for f in range(40)]
for i in range(8):poses[i]=blend(st,poses[i],ease(i/8))
write('Death',poses)
# Fidget: turn the cobra across the waist and return, as in native fa..fe.
G=json.loads((P/'work/grip_pose.json').read_text());axis=Vector(G['handle_axis_hand_local']);apply(st)
base={b.name:b.matrix_basis.copy() for b in rig.pose.bones};wrist=armik.W(rig,'B_R_Hand').translation.copy();d0=armik.W(rig,'B_R_Hand').to_3x3()@axis
frames=[]
for i in range(43):
 u=math.sin(math.pi*i/42)**2
 direction=d0.lerp(Vector((1,-.18,.10)).normalized(),u).normalized()
 target=wrist+Vector((.015,-.08,-.18))*u
 frames.append({'snap':base,'wrist':target,'dir':direction})
select(None);choices=armik.arm_dp(rig,'R',frames,axis,phis=range(-140,141,10),k_twist=.6)
poses=[]
for i,(fr,c) in enumerate(zip(frames,choices)):
 armik.apply_arm(rig,'R',fr['snap'],fr['wrist'],axis,fr['dir'],c['phi'],c['psi'])
 p={n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
 # Preserve the exact idle endpoint, blending only the short entry/exit.
 u=min(ease(i/6),ease((42-i)/6));poses.append(blend(st,p,u))
write('Fidget',poses)
for a in list(bpy.data.actions):
 if a.name in ['GripRef','AttackSource','HitSource']:bpy.data.actions.remove(a)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
select(None)
for b in rig.pose.bones:b.matrix_basis=Matrix()
(P/'work/clip_timing.json').write_text(json.dumps({'attack_impact_s':1.25,'source_forward_frame':6,'lead_seconds':lead/30,'native_attack_seconds':1.25,'hit_seconds':19/30,'fidget_seconds':1.4},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/actions.blend'))
