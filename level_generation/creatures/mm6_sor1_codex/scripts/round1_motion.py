"""Review 1: relaxed free arm, library-led staff cast and full-body secondary actions.
Resume the packed master; preserve the fitted mesh, grip and validated death drape.
"""
import bpy, sys, math, json
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/round1_mixamo.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=120
import arm_solver as sol
right=sol.Side('B_R_');left=sol.Side('B_L_');G=sol.G
names=[b.name for b in rig.data.bones];robe=[n for n in names if n.startswith('Robe_')]
def attach(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 attach(None)
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 attach(a);scene.frame_set(int(f),subframe=float(f-int(f)))
 return {n:rig.pose.bones[n].matrix_basis.copy() for n in names}
def setpose(d):
 attach(None)
 for n,m in d.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def key(a,f):
 d={n:rig.pose.bones[n].matrix_basis.copy() for n in names};attach(a)
 for n,m in d.items():
  pb=rig.pose.bones[n];pb.matrix_basis=m;pb.rotation_mode='QUATERNION'
  pb.keyframe_insert('rotation_quaternion',frame=f)
  if n=='B_Pelvis' or n in robe:pb.keyframe_insert('location',frame=f)
 attach(None)
def smooth(x):
 x=max(0.,min(1.,x));return x*x*(3-2*x)
def curve(keys,t):
 if t<=keys[0][0]:return Vector(keys[0][1])
 for (a,x),(b,y) in zip(keys,keys[1:]):
  if a<=t<=b:return Vector(x).lerp(Vector(y),smooth((t-a)/(b-a)))
 return Vector(keys[-1][1])
def blendmat(a,b,w):
 q=a.to_quaternion().slerp(b.to_quaternion(),w);m=q.to_matrix().to_4x4();m.translation=a.translation.lerp(b.translation,w);return m

def free_arm(side,W,pole,Rh=None):
 S=rig.pose.bones[side.s+'UpperArm'].head.copy();Rsh=rig.pose.bones[side.s+'Clavicle'].matrix.to_3x3()
 E,W2=side.ik(S,W,pole)
 Ra=Rsh@side.rel['UpperArm'];Ra=(Ra@side.uA).rotation_difference((E-S).normalized()).to_matrix()@Ra
 Rf=Ra@side.rel['Forearm'];Rf=(Rf@side.uF).rotation_difference((W2-E).normalized()).to_matrix()@Rf
 if Rh is None:Rh=Rf@side.rel['Hand']
 side.apply(dict(Ra=Ra,Rf=Rf,Rh=Rh,S=S,E=E,W=W2))
 return (W-W2).length

def leg_ik(sd,target):
 up,lo,foot=[rig.pose.bones[f'B_{sd}_{n}'] for n in ['Thigh','Calf','Foot']]
 A=up.head.copy();W=target.translation;L1=(rig.data.bones[lo.name].head_local-rig.data.bones[up.name].head_local).length;L2=(rig.data.bones[foot.name].head_local-rig.data.bones[lo.name].head_local).length
 d=W-A;dist=min(d.length,(L1+L2)*.999);u=d.normalized();q=(L1*L1+dist*dist-L2*L2)/(2*dist)
 pole=Vector((0,-1,0));pole=(pole-u*pole.dot(u)).normalized();E=A+u*q+pole*math.sqrt(max(0,L1*L1-q*q));W2=A+u*dist
 for pb,dst,child in [(up,E,lo),(lo,W2,foot)]:
  R=pb.matrix.to_3x3();old=(child.head-pb.head).normalized();R=old.rotation_difference((dst-pb.head).normalized()).to_matrix()@R
  M=R.to_4x4();M.translation=pb.head;pb.matrix=M;bpy.context.view_layer.update()
 M=target.copy();M.translation=W2;foot.matrix=M;bpy.context.view_layer.update()
 return (W2-W).length


# The head-only mesh includes a painted robe-shaped neck apron. Bury that apron inside the true collar.
changed=[]
for v,a in zip(body.data.vertices,body.data.attributes['piece'].data):
 if a.value!=2 or v.co.z>=1.475:continue
 old=v.co.copy();w=smooth((1.475-v.co.z)/.035)
 radius=math.hypot(v.co.x,v.co.y-.005)
 if radius>.050:
  fac=1-w*(1-.050/radius);v.co.x*=fac;v.co.y=.005+(v.co.y-.005)*fac
 if (v.co-old).length>1e-6:changed.append([v.index,list(old),list(v.co)])
(p/'work/round1_collar.json').write_text(json.dumps({'cause':'The head mesh neck apron overlaps the separate robe collar; its texture includes purple robe. Radially tuck the lower apron under the authoritative red/gold body collar.','vertices':changed,'max_tuck_mm':max((Vector(v[1])-Vector(v[2])).length for v in changed)*1000},indent=2))
old={r:bpy.data.actions[r] for r in ['Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget']}
stand=sample(old['Standing'],0);setpose(stand)
feet={sd:rig.pose.bones[f'B_{sd}_Foot'].matrix.copy() for sd in 'LR'}
standpel=rig.pose.bones['B_Pelvis'].head.copy()
standgrip=rig.pose.bones['B_R_Hand'].matrix@Vector(G['handle_centre_hand_local'])
mx=bpy.data.actions['MX_2H'];mx0=sample(mx,20)
# Retargeted body source: the forward two-hand cast, trimmed past its low-guard opening.
N={'Standing':240,'Walking':96,'Attack':144,'Cast':246,'Hit':90,'Death':int(old['Death'].frame_range[1]),'Dead':120,'Fidget':288}
base={r:[sample(a,min(f,float(a.frame_range[1]))) for f in range(N[r]+1)] for r,a in old.items()}
mxdata=[sample(mx,min(81,20+f/4)) for f in range(N['Cast']+1)]
for r,a in old.items():a.name='Old_'+r;a.use_fake_user=False
# Relaxed hand by the thigh: near-full reach, elbow bends forward instead of flaring sideways.
idle=Vector((.307,-.040,.956));axis0=Vector((-.035,-.10,1)).normalized();grip0=standgrip.copy()
report={}
for role in N:
 out=bpy.data.actions.new(role);out.use_fake_user=True;out.use_frame_range=True;out.frame_start=0;out.frame_end=N[role]
 pending=[];phis=[];prevphi=None;miss=0.;legmiss=0.
 for f in range(N[role]+1):
  t=f/120;u=f/N[role];d=base[role][f]
  setpose(d)
  rawrobe={n:rig.pose.bones[n].matrix.copy() for n in robe}
  before={n:rig.pose.bones[n].head.copy() for n in ['B_Pelvis',*[f'B_{s}_{b}' for s in 'LR' for b in ['Calf','Foot']]]}
  oldleft={n:rig.pose.bones[n].matrix.copy() for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']}
  if role=='Cast':
   # Retain 20% of source rotation changes. Plant feet separately: source knees cannot steer the IK.
   setpose(stand);w=smooth(t/.15)*smooth((2.05-t)/.30)
   for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
    dq=mx0[n].to_quaternion().inverted()@mxdata[f][n].to_quaternion()
    rig.pose.bones[n].rotation_quaternion=stand[n].to_quaternion()@Quaternion().slerp(dq,.20*w)
   bpy.context.view_layer.update()
   M=rig.pose.bones['B_Pelvis'].matrix.copy()
   motion=curve([(0,(0,0,0)),(.28,(0,.015,-.01)),(.70,(0,-.065,-.045)),(1.10,(0,-.055,-.030)),(1.8,(0,0,0)),(2.05,(0,0,0))],t)
   M.translation+=motion;rig.pose.bones['B_Pelvis'].matrix=M;bpy.context.view_layer.update()
   step=curve([(0,(0,0,0)),(.22,(0,0,0)),(.36,(0,-.075,.045)),(.50,(0,-.15,0)),(1.30,(0,-.15,0)),(1.47,(0,-.075,.045)),(1.64,(0,0,0)),(2.05,(0,0,0))],t)
   for sd in 'LR':
    target=feet[sd].copy()
    if sd=='L':target.translation+=step
    legmiss=max(legmiss,leg_ik(sd,target))
  elif role in ['Hit','Fidget']:
   if role=='Hit':
    a=curve([(0,(0,0,0)),(.14,(0,.034,-.058)),(.25,(0,.028,-.045)),(.43,(0,-.01,-.025)),(.75,(0,0,0))],t)
    bend=curve([(0,(0,0,0)),(.14,(-9,0,3)),(.30,(-4,0,2)),(.48,(4,0,-1)),(.75,(0,0,0))],t)
   else:
    a=curve([(0,(0,0,0)),(.55,(-.014,.008,-.018)),(1.15,(-.01,0,-.014)),(1.65,(.008,0,-.008)),(2.4,(0,0,0))],t)
    bend=curve([(0,(0,0,0)),(.6,(2,-2,-4)),(1.35,(0,2,3)),(2.4,(0,0,0))],t)
   M=rig.pose.bones['B_Pelvis'].matrix.copy();M.translation+=a;rig.pose.bones['B_Pelvis'].matrix=M;bpy.context.view_layer.update()
   for bn in ['B_Spine','B_Spine1','B_Spine2']:
    pb=rig.pose.bones[bn];M=pb.matrix.copy();R=Quaternion((1,0,0),math.radians(bend.x/3)).to_matrix()@Quaternion((0,1,0),math.radians(bend.y/3)).to_matrix()@Quaternion((0,0,1),math.radians(bend.z/3)).to_matrix();M2=(R@M.to_3x3()).to_4x4();M2.translation=M.translation;pb.matrix=M2;bpy.context.view_layer.update()
   for sd in 'LR':legmiss=max(legmiss,leg_ik(sd,feet[sd]))
  delta=rig.pose.bones['B_Pelvis'].head-standpel
  # All action returns share the relaxed hand. Existing Death poses remain after the initial quarter second.
  if role not in ['Dead']:
   if role=='Cast':
    W=curve([(0,idle),(.28,(.27,-.18,1.23)),(.62,(.28,-.33,1.36)),(.84,(.28,-.42,1.32)),(1.13,(.29,-.38,1.29)),(1.8,idle),(2.05,idle)],t)
   elif role=='Hit':
    W=curve([(0,idle),(.16,(.33,-.14,1.13)),(.28,(.32,-.17,1.16)),(.48,(.31,-.08,1.04)),(.75,idle)],t)
   elif role in ['Attack','Fidget']:
    a=smooth(t/.23)*smooth((N[role]/120-t)/.28)
    W=idle.copy()
   else:
    W=idle.copy()
    if role=='Walking':W.y+=.020*math.sin(2*math.pi*u);W.x+=.025
   free_arm(left,W+delta,Vector((.12,-1,-.05)))
   if role in ['Attack','Fidget']:
    for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']:
     pb=rig.pose.bones[n];pb.matrix_basis=blendmat(pb.matrix_basis,d[n],a);bpy.context.view_layer.update()
   if role=='Death':
    w=smooth(t/.30)
    for n,M in oldleft.items():
     pb=rig.pose.bones[n];pb.matrix=blendmat(pb.matrix,M,w);bpy.context.view_layer.update()
   for n in names:
    if n.startswith('B_L_Finger'):rig.pose.bones[n].matrix_basis=Matrix()
  if role in ['Cast','Hit','Fidget']:
   if role=='Cast':
    grip=curve([(0,grip0),(.28,(-.40,-.20,1.20)),(.48,(-.43,-.17,1.23)),(.78,(-.455,-.13,1.22)),(1.08,(-.455,-.13,1.22)),(1.50,(-.40,-.19,1.20)),(1.9,grip0),(2.05,grip0)],t)
    ax=curve([(0,axis0),(.28,(.12,-.08,.99)),(.48,(.16,-.15,.98)),(.78,(.20,-1,.10)),(1.08,(.20,-1,.10)),(1.5,(.10,-.4,.916)),(1.9,axis0),(2.05,axis0)],t).normalized()
   elif role=='Hit':
    grip=grip0+curve([(0,(0,0,0)),(.14,(-.035,.095,.025)),(.25,(-.030,.070,.025)),(.48,(0,-.015,.018)),(.75,(0,0,0))],t)
    ax=curve([(0,axis0),(.14,(-.12,.22,.97)),(.28,(-.10,.16,.98)),(.50,(-.02,-.16,.98)),(.75,axis0)],t).normalized()
   else:
    grip=grip0+curve([(0,(0,0,0)),(.55,(-.035,-.015,.055)),(1.15,(-.02,.018,.032)),(1.65,(.015,-.008,.020)),(2.10,(0,0,0)),(2.4,(0,0,0))],t)
    ax=curve([(0,axis0),(.60,(.10,-.25,.96)),(1.15,(.10,-.02,.99)),(1.65,(-.015,-.16,.99)),(2.1,axis0),(2.4,axis0)],t).normalized()
   grip+=delta*.45;grip.z=max(grip.z,1.05*ax.z+.018)
   r=right.solve(grip,ax,Vector((-.45,-.15,-1)),prevphi,steps=144);prevphi=r['phi'];phis.append(r['phi'])
   right.apply(r);miss=max(miss,r['miss'])
  else:grip=ax=None;phis.append(0.)
  for n,q in G['finger_local'].items():rig.pose.bones[n].rotation_quaternion=q
  bpy.context.view_layer.update()
  if role in ['Cast','Hit','Fidget']:
   # Carry the existing smooth robe around the new hip/knee/foot paths, preserving its broad closed envelope.
   after={n:rig.pose.bones[n].head.copy() for n in before}
   for n in robe:
    M=rawrobe[n].copy();z=rig.data.bones[n].head_local.z;x=rig.data.bones[n].head_local.x
    mix=max(0,min(1,.5+x/.40));dp=after['B_Pelvis']-before['B_Pelvis']
    dk=(after['B_R_Calf']-before['B_R_Calf']).lerp(after['B_L_Calf']-before['B_L_Calf'],mix)
    df=(after['B_R_Foot']-before['B_R_Foot']).lerp(after['B_L_Foot']-before['B_L_Foot'],mix)
    shift=df.lerp(dk,max(0,min(1,(z-.10)/.48))) if z<.58 else dk.lerp(dp,max(0,min(1,(z-.58)/.46)))
    M.translation+=shift;rig.pose.bones[n].matrix=M;bpy.context.view_layer.update()
  pending.append(({n:rig.pose.bones[n].matrix_basis.copy() for n in names},grip,ax))
 # Smooth the optimal staff roll, then solve with that continuous hand orientation (no discrete roll jumps).
 angles=np.unwrap(phis);kernel=np.exp(-np.arange(-8,9,dtype=float)**2/(2*3.0**2));kernel/=kernel.sum();angles=np.convolve(np.pad(angles,(8,8),mode='edge'),kernel,mode='valid')
 for f,(pose,grip,ax) in enumerate(pending):
  setpose(pose)
  if grip is not None:
   q0=(right.rest['Hand']@right.axis_hand).rotation_difference(ax).to_matrix();Rh=Quaternion(ax,float(angles[f])).to_matrix()@q0@right.rest['Hand']
   r=right.pose_for(grip,Rh,Vector((-.45,-.15,-1)));right.apply(r);miss=max(miss,r['miss'])
  if role=='Walking':
   # The original walk let the long staff butt cross the floor at its lowest hip position.
   ev=bpy.data.objects['Staff'].evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();low=min(v.co.z for v in mesh.vertices);ev.to_mesh_clear()
   gap=.012-low;lift=.5*(gap+math.sqrt(gap*gap+.003*.003))
   H=rig.pose.bones['B_R_Hand'].matrix.copy();point=H@Vector(G['handle_centre_hand_local'])+Vector((-.055,-.020,lift))
   pole=rig.pose.bones['B_R_Forearm'].head-rig.pose.bones['B_R_UpperArm'].head
   right.apply(right.pose_for(point,H.to_3x3(),pole))
  # Bake the rig's existing twist helpers from the new arm transforms, without redistributing weights.
  for sd in 'LR':
   fb,hb=[rig.data.bones[f'B_{sd}_{b}'] for b in ['Forearm','Hand']];axis=(fb.matrix_local.inverted()@hb.head_local).normalized()
   dq=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion()@(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion().inverted()
   def twist(q,axis):return (2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi
   rig.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.5*twist(dq,axis))
   ub=rig.data.bones[f'B_{sd}_UpperArm'];axis=(ub.matrix_local.inverted()@fb.head_local).normalized()
   rig.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*twist(rig.pose.bones[ub.name].matrix_basis.to_quaternion(),axis))
  bpy.context.view_layer.update();key(out,f)
 report[role]={'frames':N[role]+1,'staff_ik_miss_mm':miss*1000,'leg_ik_miss_mm':legmiss*1000}
 print('ROUND1',role,report[role],flush=True)
attach(None)
for a in list(bpy.data.actions):
 if a.name.startswith(('Old_','MX_')):bpy.data.actions.remove(a)
for pb in rig.pose.bones:pb.matrix_basis.identity()
(p/'work/round1_motion.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round1_motion.blend'))
