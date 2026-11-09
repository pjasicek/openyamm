"""Adapt selected library clips to the native upright stance and forearm-mounted blade."""
import bpy,sys,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_actions.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30
from arm_ik import Side,swing_twist_deg
from hand_weights import repair_hand_weights
repair_hand_weights(body,rig)
SIDES={s:Side(s) for s in 'LR'};names=[b.name for b in rig.data.bones]
def setact(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 setact(a);scene.frame_set(int(f),subframe=float(f-int(f)))
 return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names}
def apply(p):
 setact(None)
 for n,(q,l) in p.items():
  pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
 bpy.context.view_layer.update()
def snapshot():return {n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy())for n in names}
def world(n):return rig.matrix_world@rig.pose.bones[n].matrix
def put(n,R):
 pb=rig.pose.bones[n];m=R.to_4x4();m.translation=world(n).translation;pb.matrix=rig.matrix_world.inverted()@m;bpy.context.view_layer.update()
def aim(n,child,T):
 m=world(n);q=(world(child).translation-m.translation).rotation_difference(T-m.translation);put(n,q.to_matrix()@m.to_3x3())
def leg(sd,T,R):
 th,ca,ft=[f'B_{sd}_{k}' for k in ('Thigh','Calf','Foot')];H=world(th).translation;K=world(ca).translation;A=world(ft).translation;a=(K-H).length;b=(A-K).length;D=T-H;d=min(D.length,(a+b)*.999);u=D.normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);N=H+a*(u*c+v*math.sqrt(max(0,1-c*c)));aim(th,ca,N);aim(ca,ft,T);put(ft,R)
def smooth(u):u=min(1,max(0,u));return u*u*(3-2*u)
def blend(a,b,t):return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t))for n in names}
def frame(a,n):
 a=a.normalized();n=(n-a*n.dot(a)).normalized();return Matrix((a,n,a.cross(n))).transposed()
LONG={};PALM={};HF={}
for sd in 'LR':
 h=rig.data.bones[f'B_{sd}_Hand'];w=h.head_local;d=rig.data.bones[f'B_{sd}_Finger2'].head_local-w;t=rig.data.bones[f'B_{sd}_Finger1'].head_local-rig.data.bones[f'B_{sd}_Finger4'].head_local;n=d.cross(t)*(-1 if sd=='R'else 1);iv=h.matrix_local.to_3x3().inverted();LONG[sd]=(iv@d).normalized();PALM[sd]=(iv@n).normalized();HF[sd]=frame(LONG[sd],PALM[sd])
(p:=P/'work/hand_frames.json').write_text(json.dumps({s:{'long_local':list(LONG[s]),'palm_local':list(PALM[s])}for s in 'LR'},indent=2))
def handrot(sd,axis,normal):return frame(axis,normal)@HF[sd].inverted()
def arm(sd,T,R,pole):
 obj=SIDES[sd];S=world(f'B_{sd}_UpperArm').translation;v=T-S
 if v.length>(obj.l1+obj.l2)*.97:T=S+v.normalized()*(obj.l1+obj.l2)*.97
 candidates=[];axis=(T-S).normalized()
 for deg in range(-180,181,10):
  r=obj.pose_anatomical(T,R,Quaternion(axis,math.radians(deg))@pole);base=world(f'B_{sd}_Clavicle').to_3x3()@obj.rel['Arm'];roll=abs(swing_twist_deg((base.inverted()@r['Ra']).to_quaternion(),obj.uA)[1]);cost=abs(deg)*.02+roll*.1+max(0,roll-45)*100
  if getattr(obj,'previous_Ra',None) is not None:cost+=.05*math.degrees(obj.previous_Ra.to_quaternion().rotation_difference(r['Ra'].to_quaternion()).angle)
  candidates.append((cost,r,roll))
 _,r,roll=min(candidates,key=lambda x:x[0])
 base=r['Rf']@obj.rel['Hand'];q=(base.inverted()@R).to_quaternion();ax=(base.inverted()@(r['W']-r['E'])).normalized();tw=2*math.atan2(Vector((q.x,q.y,q.z)).dot(ax),q.w);tw=(tw+math.pi)%(2*math.pi)-math.pi;sw=q@Quaternion(ax,-tw)
 if sw.w<0:sw=-sw
 if sw.angle>math.radians(50):sw=Quaternion().slerp(sw,math.radians(50)/sw.angle)
 r['Rh']=base@(sw@Quaternion(ax,min(math.radians(85),max(-math.radians(85),tw)))).to_matrix();obj.apply(r);return r['miss'],roll
# Correct ownership before any motion is evaluated; feathers follow their local skin or their rigid band.
co=np.array([tuple(v.co)for v in body.data.vertices]);piece=np.array([x.value for x in body.data.attributes['piece'].data]);groups={g.name:g for g in body.vertex_groups};gn={g.index:g.name for g in body.vertex_groups}
def weights(i):return {gn[e.group]:e.weight for e in body.data.vertices[i].groups}
def putweights(i,w):
 w={n:float(x)for n,x in w.items()if x>1e-7};w=dict(sorted(w.items(),key=lambda x:-x[1])[:4]);tot=sum(w.values());assert tot>0
 for g in list(body.data.vertices[i].groups):body.vertex_groups[g.group].remove([i])
 for n,x in w.items():groups[n].add([i],x/tot,'REPLACE')
centres={v:co[piece==v].mean(0)for v in set(piece.tolist())}
from cloth_region import garment
clothmask=garment(body.data,co,piece)
for i,(x,y,z)in enumerate(co):
 pt=int(piece[i]);sd='L'if x>0 else'R';w=weights(i)
 if pt in [3,5,8,9]:w={'B_Head':1}
 elif pt==6:w={'B_Neck':1}
 elif pt==4:w={'B_Pelvis':1}
 elif pt in [10,11,12,13]:w={f'B_{sd}_Foot':1}
 elif pt not in [0,1,2]:
  cx,cy,cz=centres[pt]
  if cx<-.26 and .80<cz<1.14:w={'B_R_Forearm':1}
  elif cx<-.12 and cz>1.23:w={'B_R_UpperArm':.40,'B_R_Clavicle':.60}
  elif cz>1.20:w={'B_Spine2':1}
  elif cz>.85:w={'B_Pelvis':1}
  else:
   t=float(np.clip((.93-z)/.36,0,1));left=float(np.clip((x+.09)/.18,0,1));w={'B_Pelvis':1-t,'B_L_Thigh':t*left,'B_R_Thigh':t*(1-left)}
 if pt==0 and abs(x)<.15 and 1.04<z<1.32:
  lost=0;t=float(np.clip((abs(x)-.075)/.075,0,1))
  for n in list(w):
   if any(k in n for k in ['UpperArm','Forearm','Hand','Clavicle']):lost+=w[n]*(1-t);w[n]*=t
  w['B_Spine2']=w.get('B_Spine2',0)+lost
 if pt in [0,2] and clothmask[i]:
  t=float(np.clip((1.015-z)/.40,0,1));left=float(np.clip((x+.12)/.24,0,1));w={'B_Pelvis':1-t*.8,'B_L_Thigh':t*.8*left,'B_R_Thigh':t*.8*(1-left)}
 putweights(i,w)
# Sole support points are identified in the actual rest mesh, not from bone tails.
sole={}
for sd in 'LR':
 ids=[i for i in range(len(co))if piece[i]==1 and co[i,0]*(1 if sd=='L'else -1)>0 and co[i,2]<.075];z=min(co[i,2]for i in ids);sole[sd]=[i for i in ids if co[i,2]<z+.009];assert len(sole[sd])>=8
 # Bare feet/toes below the ankle are a rigid support patch.
 for i in ids:putweights(i,{f'B_{sd}_Foot':1})
def evaluated():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.array([tuple(body.matrix_world@v.co)for v in me.vertices]);ev.to_mesh_clear();return a
def solepoints(sd):return evaluated()[sole[sd]]
def flat(sd):
 ft=f'B_{sd}_Foot';pts=solepoints(sd);n=Vector(np.linalg.svd(pts-pts.mean(0))[2][-1]);n*=1 if n.z>0 else -1;put(ft,n.rotation_difference(Vector((0,0,1))).to_matrix()@world(ft).to_3x3())
 pts=solepoints(sd);rest=co[sole[sd]];fwd=Vector(pts[rest[:,1]<np.quantile(rest[:,1],.25)].mean(0)-pts[rest[:,1]>np.quantile(rest[:,1],.75)].mean(0));fwd.z=0;put(ft,fwd.rotation_difference(Vector((0,-1,0))).to_matrix()@world(ft).to_3x3());pts=solepoints(sd);T=world(ft).translation;T.z+=.002-pts[:,2].min();leg(sd,T,world(ft).to_3x3())
GRIP=json.loads((P/'work/shield_grip.json').read_text())
source={a.name:[sample(a,f)for f in range(int(a.frame_range[1])+1)]for a in bpy.data.actions if a.use_fake_user}
ST=source['Standing'][0];apply(ST)
for sd in 'LR':flat(sd)
for sd in 'LR':
 sg=1 if sd=='L'else -1;T=Vector((.285,-.14,1.025))if sd=='L'else Vector((-.245,-.055,.78));R=handrot(sd,Vector((0,0,-1)),Vector((.8,-.6,0))if sd=='L'else Vector((1,0,0)));arm(sd,T,R,Vector((0,-1,0)))
for n in names:
 if 'Finger'in n:rig.pose.bones[n].rotation_quaternion=Quaternion(GRIP['finger_local'][n])if n in GRIP['finger_local']else Quaternion()
bpy.context.view_layer.update();ST=snapshot();HOME={s:world(f'B_{s}_Foot').copy()for s in 'LR'};HW={s:world(f'B_{s}_Hand').copy()for s in 'LR'};PEL=world('B_Pelvis').copy()
peaks={s:0 for s in 'LR'}
for p in source['Walking']:
 apply(p);a=evaluated();low={s:a[sole[s],2].min()for s in 'LR'}
 for s in 'LR':peaks[s]=max(peaks[s],low[s]-min(low.values()))
allposes={};report={}
roles=['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget']
for role in roles:
 for obj in SIDES.values():obj.previous_Ra=None;obj.previous_Rf=None
 src=source['Standing'if role=='Fidget'else role];lead=6 if role in ['Attack','Cast']else 0;outro=6 if lead else 0;nf=len(src)+lead+outro;poses=[];errors=[]
 for fi in range((nf-1)*2+1):
  f=fi/2;j=max(0,min(len(src)-1,f-lead));k=int(j);phase=f/max(1,nf-1);p=blend(src[k],src[min(k+1,len(src)-1)],j-k)
  env=min(smooth(f/max(1,lead)),smooth((nf-1-f)/max(1,outro)))if lead else 1
  if role in ['Attack','Cast']:p=blend(ST,p,env)
  if role=='Standing':p=blend(ST,p,.12)
  if role=='Fidget':p=blend(ST,p,.30)
  if role=='Hit':p=blend(ST,p,.35*min(smooth(f/3),smooth((nf-1-f)/4)))
  if role=='Death':p=blend(ST,p,smooth(f/8))
  apply(p)
  if role in ['Attack','Cast']:
   # Source torso and arms retain momentum; constrain the long native skirt to a discrete step.
   sp=world('B_Spine');v=world('B_Neck').translation-sp.translation;u=v.normalized().lerp(Vector((0,0,1)),.60).normalized();put('B_Spine',v.rotation_difference(u).to_matrix()@sp.to_3x3())
   m=world('B_Pelvis');m.translation=PEL.translation+Vector((.012*math.sin(phase*math.tau),0,-.018*math.sin(math.pi*phase)**2));rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
   for sd in 'LR':
    T=HOME[sd].translation.copy();u=0
    if sd=='L':
     if j<3:u=0
     elif j<9:u=(j-3)/6
     elif j<22:u=1
     else:u=max(0,(len(src)-1-j)/max(1,len(src)-1-22))
     T.y-=.085*smooth(u)*env;T.z+=.045*math.sin(math.pi*u)*env
    leg(sd,T,HOME[sd].to_3x3())
  if role in ['Walking','Running']:
   m=world('B_Pelvis');m.translation.z+=.035 if role=='Walking'else .02;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
   a=evaluated();low={s:a[sole[s],2].min()for s in 'LR'};ground=min(low.values())
   for sd in 'LR':
    m=world(f'B_{sd}_Foot');lift=(.10*max(0,low[sd]-ground)/max(peaks[sd],.001))if role=='Walking'else min(.14,max(0,low[sd]-ground));rot=HOME[sd].to_3x3();put(f'B_{sd}_Foot',rot);T=m.translation.copy()
    if role=='Running':T.x=HOME[sd].translation.x+(T.x-HOME[sd].translation.x)*.8;T.y=HOME[sd].translation.y+(T.y-HOME[sd].translation.y)*.8
    T.z+=.002+lift-solepoints(sd)[:,2].min();leg(sd,T,rot)
  if role in ['Standing','Fidget','Hit']:
   if role=='Hit':
    m=world('B_Pelvis');m.translation.z=PEL.translation.z+.006*math.sin(phase*math.tau);rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
   for sd in 'LR':leg(sd,HOME[sd].translation,HOME[sd].to_3x3())
  if role=='Death':
   a=evaluated();core=(piece==1)|((piece==0)&(np.abs(co[:,0])<.16))|np.isin(piece,[3,5]);bottom=a[core,2].min();m=world('B_Pelvis');m.translation.z+=.002-bottom;rig.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
  for sd in 'LR':
   sg=1 if sd=='L'else -1;M=world(f'B_{sd}_Hand');T=M.translation.copy();Rh=M.to_3x3();pole=world(f'B_{sd}_Forearm').translation-world(f'B_{sd}_UpperArm').translation
   if role in ['Standing','Fidget','Walking','Running','Hit']:
    T=HW[sd].translation.copy();Rh=HW[sd].to_3x3();amp={'Standing':.002,'Fidget':.009,'Walking':.04,'Running':.065,'Hit':.035}[role];T.y+=amp*math.sin(phase*math.tau+(0 if sd=='R'else math.pi));T.z+=amp*.35*math.sin(phase*math.pi)**2;pole=Vector((0,-1,0))
   elif sd=='L' and role in ['Attack','Cast']:
    T=HW[sd].translation+Vector((.01,-.045*math.sin(math.pi*phase),.025*math.sin(math.pi*phase)));Rh=HW[sd].to_3x3();pole=Vector((0,-1,0))
   elif role=='Death':
    T.x=sg*max(abs(T.x),.25);T.z=max(T.z,.10);pole=Vector((sg*.3,-1,.2))
   if role in ['Attack','Cast']and sd=='R':T.x=min(T.x,-.20)
   e,r=arm(sd,T,Rh,pole);errors.append((e,r))
  for n in names:
   if 'Finger'in n:rig.pose.bones[n].rotation_quaternion=Quaternion(GRIP['finger_local'][n])if n in GRIP['finger_local']else Quaternion()
  bpy.context.view_layer.update();poses.append(snapshot())
 allposes[role]=poses;report[role]={'frames_60hz':len(poses),'ik_error_max_m':max(x[0]for x in errors),'upper_roll_max_deg':max(x[1]for x in errors)}
 print('ADAPTED',role,report[role],flush=True)
# Retain a held corpse under its runtime role; source clips are removed from the production master.
allposes['Dead']=[allposes['Death'][-1]]*61
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
scene.render.fps=60
for role,poses in allposes.items():
 act=bpy.data.actions.new(role);act.use_fake_user=True;setact(act);prev={}
 for f,p in enumerate(poses):
  for n,(q,l)in p.items():
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
 act.use_frame_range=True;act.frame_start=0;act.frame_end=len(poses)-1
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
setact(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
(P/'work/animation_adaptation.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_adapted.blend'))
assert set(allposes)==set(roles+['Dead'])
