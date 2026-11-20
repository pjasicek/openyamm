"""Library motion adapted to the native relaxed carry; geometric foot and elbow constraints."""
import bpy,sys,os,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_actions.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
from arm_ik import Side,swing_twist_deg
sides={s:Side(s) for s in 'LR'};names=[b.name for b in rig.data.bones];FPS=48
G=json.loads((P/'work/grip_pose.json').read_text());FJ=json.loads((P/'work/finger_joints.json').read_text())
def setact(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def apply(p):
 setact(None)
 for n,(q,l) in p.items():pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
 bpy.context.view_layer.update()
def capture():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def sample(a,t):
 setact(a);f=max(0,min(float(a.frame_range[1]),t));sc.frame_set(int(f),subframe=f-int(f));return capture()
def wm(n):return rig.pose.bones[n].matrix.copy()
def pos(n):return rig.pose.bones[n].head.copy()
def put(n,R,location=None):
 pb=rig.pose.bones[n];m=R.to_4x4() if len(R)==3 else R.copy();m.translation=pos(n) if location is None else location;pb.matrix=m;bpy.context.view_layer.update()
def shiftpelvis(d):
 m=wm('B_Pelvis');m.translation+=d;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def blend(a,b,t):return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t))for n in names}
def aim(n,child,target):
 R=wm(n).to_3x3();u=(pos(child)-pos(n)).normalized();put(n,u.rotation_difference((target-pos(n)).normalized()).to_matrix()@R)
rest={n:rig.data.bones[n].matrix_local.copy()for n in names}
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
setact(None);bpy.context.view_layer.update()
co=np.array([tuple(v.co)for v in body.data.vertices]);pv=np.array([d.value for d in body.data.attributes['piece'].data]);group={g.index:g.name for g in body.vertex_groups}
ground_ids=[v.index for v in body.data.vertices if pv[v.index]==0 and sum(g.weight for g in v.groups if any(k in group[g.group] for k in ('Arm','Forearm','Hand','Finger')))<.3]
soles={};footR={};anklez={};home={}
for sd in 'LR':
 ids=[v.index for v in body.data.vertices if pv[v.index]==0 and sum(g.weight for g in v.groups if group[g.group].startswith((f'B_{sd}_Foot',f'B_{sd}_Toe')))> .65]
 z=min(co[ids,2]);ids=[i for i in ids if co[i,2]<z+.012];soles[sd]=ids
 foot=f'B_{sd}_Foot';toe=f'B_{sd}_Toe0';d=rest[toe].translation-rest[foot].translation;yaw=math.atan2(d.x,-d.y)
 R=Matrix.Rotation(-yaw,3,'Z')@rest[foot].to_3x3();footR[sd]=R
 points=np.array([tuple(R@rest[foot].to_3x3().inverted()@(Vector(co[i])-rest[foot].translation))for i in ids]);anklez[sd]=-points[:,2].min()+.002
 home[sd]=Vector((.135 if sd=='L' else -.135,-.045,anklez[sd]))
# Actual knuckle direction and flexion side, in each fitted hand frame.
handframe={}
for sd in 'LR':
 inv=rest[f'B_{sd}_Hand'].inverted();w=rest[f'B_{sd}_Hand'].translation
 kn=[Vector(FJ[sd][f'B_{sd}_Finger{i}']) for i in (1,2,3,4)];f=(sum(kn,Vector())/4-w).normalized()
 tip=Vector(FJ[sd][f'B_{sd}_Finger22_tip']);q=tip-kn[1];n=q-f*q.dot(f)
 # Surface/reference confirms the palm is the inward side of the A-pose hand, toward +Y.
 across=kn[0]-kn[3];n=across.cross(f).normalized();distal=sum((Vector(FJ[sd][f'B_{sd}_Finger{i}2']) for i in (1,2,3,4)),Vector())/4-sum(kn,Vector())/4
 if n.dot(distal)<0:n=-n
 fl=(inv.to_3x3()@f).normalized();nl=(inv.to_3x3()@n).normalized();xl=fl.cross(nl).normalized();nl=xl.cross(fl).normalized();local=Matrix([xl,fl,nl]).transposed()
 handframe[sd]=(fl,nl,local)
 print('HAND FRAME',sd,'finger',list(fl),'palm',list(nl),flush=True)
def handrot(sd,palm=Vector((1,0,0)),finger=Vector((0,0,-1))):
 y=finger.normalized();z=(palm-y*palm.dot(y)).normalized();x=y.cross(z).normalized();z=x.cross(y).normalized();return Matrix([x,y,z]).transposed()@handframe[sd][2].inverted()
def leg(sd,T,R=None):
 th,ca,ft=[f'B_{sd}_{n}' for n in ['Thigh','Calf','Foot']];H=pos(th);K=pos(ca);A=pos(ft);a=(K-H).length;b=(A-K).length
 delta=T-H;dist=min(delta.length,(a+b)*.997);u=delta.normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();x=(a*a+dist*dist-b*b)/(2*dist);kn=H+u*x+v*math.sqrt(max(0,a*a-x*x));aim(th,ca,kn);aim(ca,ft,H+u*dist);put(ft,R if R is not None else footR[sd]);rig.pose.bones[f'B_{sd}_Toe0'].rotation_quaternion=Quaternion();bpy.context.view_layer.update()
prev_arm={}
def fitarm(sd,W,R,pole=None,search=False):
 S=pos(f'B_{sd}_UpperArm');E=pos(f'B_{sd}_Forearm')
 if pole is None:pole=E-S-(W-S).normalized()*(E-S).dot((W-S).normalized())
 if pole.length<.02:pole=Vector((0,-1,0))
 obj=sides[sd];G0=W+R@obj.grip_hand
 if search:
  axis=(W-S).normalized();options=[]
  for degrees in range(-150,151,10):
   trial=Quaternion(axis,math.radians(degrees))@pole;r=obj.pose_anatomical(G0,R,trial)
   parent=wm(f'B_{sd}_Clavicle').to_3x3()@obj.rel['Arm'];upper=swing_twist_deg((parent.inverted()@r['Ra']).to_quaternion(),obj.uA)[1]
   wrist=r['sw'];roll=abs(r['tw']);ex=abs(r['E'].x);inside=max(0,.19-ex) if 1.00<r['E'].z<1.43 else 0
   cost=.06*abs(degrees)+.12*abs(upper)+.12*roll+.25*wrist+5*max(0,abs(upper)-95)+3*max(0,roll-110)+3*max(0,wrist-65)+inside*500
   if sd in prev_arm:cost+=.9*math.degrees(prev_arm[sd].rotation_difference(r['Ra'].to_quaternion()).angle)
   options.append((cost,r))
  r=min(options,key=lambda p:p[0])[1]
 else:r=obj.pose_anatomical(G0,R,pole)
 obj.apply(r);prev_arm[sd]=r['Ra'].to_quaternion();return r
# Cache source poses at their own sampling times before replacing any actions.
role_src={'Standing':'Standing','Fidget':'Fidget','Walking':'Walking','Running':'Running','Attack':'Attack','Cast':'Cast','Hit':'Hit','Death':'DeathBackward'}
DUR={'Standing':3.0,'Fidget':3.2,'Walking':.96,'Running':.72,'Attack':1.15,'Cast':1.35,'Hit':.5,'Death':2.15}
base={};full={}
for role,src in role_src.items():
 a=bpy.data.actions[src];n=round(DUR[role]*FPS);base[role]=[];full[role]=[]
 for i in range(n+1):
  t=i/FPS;u=i/n
  if role in ('Attack','Cast'):u=max(0,min(1,(t-.15)/(.8 if role=='Attack' else 1.0)))
  sf=u*float(a.frame_range[1]);base[role].append(sample(a,sf));full[role].append(sample(bpy.data.actions[role+'Full'],sf) if role+'Full' in bpy.data.actions else None)
standing=base['Standing'][0]
# Gait retains source torso rhythm; ankle constraints remove sliding and excessive source flight.
output={};diagnostics={};prevq={}
for role,poses in base.items():
 out=[];rows=[];n=len(poses)-1;prev_arm.clear()
 for i,pose in enumerate(poses):
  t=i/FPS;u=i/n;p=pose.copy()
  if role=='Fidget':
   for n0 in ('B_Pelvis','B_Spine','B_Spine1','B_Spine2'):p[n0]=(standing[n0][0].slerp(p[n0][0],.4),p[n0][1])
  if role in ('Attack','Cast','Hit','Death'):
   w=smooth(t/(.15 if role!='Hit' else .08))
   if role!='Death':w=min(w,smooth((DUR[role]-t)/(.20 if role!='Hit' else .12)))
   p=blend(standing,p,w)
  apply(p)
  original={sd:(pos(f'B_{sd}_Hand'),wm(f'B_{sd}_Hand').to_3x3(),pos(f'B_{sd}_Forearm'))for sd in 'LR'}
  for sd in 'LR':
   bn=f'B_{sd}_Clavicle';native=wm('B_Spine2').to_3x3()@rest['B_Spine2'].to_3x3().inverted()@rest[bn].to_3x3();motion=wm(bn).to_3x3();put(bn,native.to_quaternion().slerp(motion.to_quaternion(),.35 if role in ('Attack','Cast','Death') else .12).to_matrix())
  if role!='Death':
   targetz=.969
   if role in ('Walking','Running'):targetz+=.012+.008*math.cos(4*math.pi*u)
   elif role in ('Attack','Cast') and full[role][i]:targetz-=.016*math.sin(math.pi*u)**2
   elif role=='Hit':targetz-=.018*math.sin(math.pi*u)**2
   else:targetz+=.002*math.sin(math.tau*u)
   shiftpelvis(Vector((-pos('B_Pelvis').x,-.065-pos('B_Pelvis').y,targetz-pos('B_Pelvis').z)))
   if role in ('Walking','Running'):
    # Preserve source chest lean; the low native carry replaces the source's raised combat guard.
    for sd,off in [('L',0),('R',.5)]:
     ph=(u+off)%1;stance=.54 if role=='Walking' else .48
     if ph<stance:y=.16-.32*ph/stance;lift=0
     else:q=(ph-stance)/(1-stance);y=-.16+.32*smooth(q);lift=(.085 if role=='Walking' else .13)*math.sin(math.pi*q)
     T=home[sd].copy();T.y-=y;T.z+=lift;leg(sd,T)
   elif role in ('Attack','Cast'):
    # 20% of library lunge displacement becomes one discrete step with a planted hold.
    for sd in 'LR':
     T=home[sd].copy()
     if sd=='L':
      a=smooth((u-.12)/.18) if u<.62 else 1-smooth((u-.62)/.28);T.y-=.10*a;T.z+=.030*(math.sin(math.pi*max(0,min(1,(u-.12)/.18))) if u<.32 else math.sin(math.pi*max(0,min(1,(u-.62)/.28))))
     leg(sd,T)
   else:
    for sd in 'LR':leg(sd,home[sd])
  if role=='Death':
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(me.vertices[j].co.z for j in ground_ids);ev.to_mesh_clear();dz=.003-low;shiftpelvis(Vector((0,0,dz)))
   original={sd:(W+Vector((0,0,dz)),R,E+Vector((0,0,dz)))for sd,(W,R,E)in original.items()}
  for sd in 'LR':
   sign=1 if sd=='L' else -1;S=pos(f'B_{sd}_UpperArm');W,R,E=original[sd]
   if role in ('Standing','Fidget','Walking','Running','Hit'):
    swing=(.075 if role=='Walking' else .12 if role=='Running' else .008)*math.sin(math.tau*u+(0 if sd=='L' else math.pi))
    W=S+Vector((sign*.085,-.012+swing,-(sides[sd].l1+sides[sd].l2)*.985+.010+abs(swing)*.12))
    W.x=sign*max(.290,sign*W.x)
    if role=='Fidget':W.z+=.009*math.sin(math.tau*u);W.y+=.008*math.sin(math.tau*u*2)
    if role=='Hit':W.y-=.060*math.sin(math.pi*u)**2;W.z+=.075*math.sin(math.pi*u)**2
    if sd=='L':R=handrot(sd,Vector((-1,0,0)),Vector((0,-swing*.7,-1)))
    else:R=handrot(sd,Vector((.954,-.30,0)),Vector((0,-swing*.7,-1)))
    pole=Vector((sign*.08,1,0));fitarm(sd,W,R,pole)
   elif role in ('Attack','Cast'):
    # Source elbows choose the bend plane; re-solve with the fitted lengths and a pure anatomical hinge.
    if role=='Cast' and sd=='R':
     W=Vector((-.30,-.045-.025*math.sin(math.pi*u),.845+.05*math.sin(math.pi*u)));R=handrot(sd,Vector((.954,-.30,0)))
    fitarm(sd,W,R,Vector((-.08,1,0)) if role=='Cast' and sd=='R' else E-S,search=not(role=='Cast' and sd=='R'))
   else:
    if sd=='R':
     W.x=min(W.x,-.375)
     # A long held spear may not continue the unarmed source's wrist roll through the floor.
     for _ in range(3):
      centre=W+R@Vector(G['handle_centre_hand_local']);axis=R@Vector(G['handle_axis_hand_local']);lo=max(-.95,-(centre.z-.025)/1.08);hi=min(.95,(centre.z-.025)/.89);az=max(lo,min(hi,axis.z));flat=Vector((axis.x,axis.y,0)).normalized();want=flat*math.sqrt(max(0,1-az*az))+Vector((0,0,az));R=axis.rotation_difference(want).to_matrix()@R
    if sd=='L':W.z=max(W.z,.21*smooth((u-.48)/.18))
    fitarm(sd,W,R,E-S,search=True)
   if sd=='R':
    for bn,q in G['finger_local'].items():rig.pose.bones[bn].rotation_quaternion=Quaternion(q)
   elif sd=='L':
    for b in rig.pose.bones:
     if b.name.startswith('B_L_Finger'):b.rotation_quaternion=Quaternion().slerp(b.rotation_quaternion,.20 if role in ('Attack','Cast','Death') else 0)
   # Deformation helpers distribute roll while the elbow remains a hinge.
   fb=rig.data.bones[f'B_{sd}_Forearm'];hb=rig.data.bones[f'B_{sd}_Hand'];seg=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(wm(fb.name).inverted()@wm(hb.name)).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=swing_twist_deg(rel@rr.inverted(),seg)[1]
   rig.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(seg,math.radians(max(-85,min(85,.65*tw))))
   ub=rig.data.bones[f'B_{sd}_UpperArm'];ax=(ub.matrix_local.inverted()@fb.head_local).normalized();uw=swing_twist_deg(rig.pose.bones[ub.name].rotation_quaternion,ax)[1];rig.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,math.radians(-.5*uw))
  bpy.context.view_layer.update()
  if role=='Death':
   # Preserve the library collapse and translation; only resolve the skin/floor contact.
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(v.co.z for v in me.vertices if pv[v.index]==0);ev.to_mesh_clear();shiftpelvis(Vector((0,0,max(0,.003-low))))
  out.append(capture());pel=pos('B_Pelvis');trunk=pos('B_Neck')-pel;rows.append({'pelvis_height_m':pel.z,'trunk_lean_deg':math.degrees(trunk.angle(Vector((0,0,1))))})
 output[role]=out
 if role=='Standing':standing=out[0]
 diagnostics[role]={'duration':n/FPS,'pelvis_height_range_m':[min(r['pelvis_height_m']for r in rows),max(r['pelvis_height_m']for r in rows)],'trunk_lean_range_deg':[min(r['trunk_lean_deg']for r in rows),max(r['trunk_lean_deg']for r in rows)]};print('FITTED',role,diagnostics[role],flush=True)
output['Dead']=[output['Death'][-1]]*2
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
sc.render.fps=FPS
for role,poses in output.items():
 a=bpy.data.actions.new(role);a.use_fake_user=True;setact(a);prev={}
 for i,pose in enumerate(poses):
  for n,(q,l)in pose.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=i)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=i)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
setact(None);(P/'review/motion_posture.json').write_text(json.dumps(diagnostics,indent=2));(P/'work/hand_frames.json').write_text(json.dumps({s:{'finger':list(v[0]),'palm':list(v[1])} for s,v in handframe.items()},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_fit.blend'))
# Quick whole-body review before adding equipment.
common.workbench_clay(sc)
for role in output:
 a=bpy.data.actions[role];setact(a)
 for j in range(5):
  f=float(a.frame_range[1])*j/4;sc.frame_set(int(f),subframe=f-int(f));common.render_views(str(P/f'review/fit_{role}_{j}'),.85,2.35,views=('front','left'),resolution=(260,360))
