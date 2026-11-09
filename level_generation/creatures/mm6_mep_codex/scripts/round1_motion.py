import bpy,sys,json,math,os
os.environ["SKIP_PILOT_RENDERS"]="1"
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common,pose_helpers as ph
bpy.ops.wm.open_mainfile(filepath=str(p/'work/retarget_raw.blend'));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];B=r.data.bones;ph.init(r);scene=bpy.context.scene;scene.render.fps=30
names=ph.names;G=json.loads((p/'work/grip_pose.json').read_text());ga=Vector(G['handle_axis_hand_local']);gc=Vector(G['handle_centre_hand_local'])
raw={};world={}
for role in ['Standing','Walking','Running','Fidget','Hit','Attack','Cast','Death']:
 act=bpy.data.actions[role];ph.setact(act);raw[role]=[];world[role]=[]
 for f in range(int(act.frame_range[1])+1):
  scene.frame_set(f);raw[role].append(ph.capture());world[role].append({n:r.pose.bones[n].matrix.copy() for n in names})
ph.setact(None);neutral={n:(Quaternion(),Vector()) for n in names};ph.apply(neutral)
fd={};pn={}
for s in ['L','R']:
 h=f'B_{s}_Hand';fd[s]=(B[f'B_{s}_Finger2'].head_local-B[h].head_local).normalized();t=B[f'B_{s}_Finger1'].head_local-B[f'B_{s}_Finger4'].head_local;pn[s]=fd[s].cross(t).normalized()
 if pn[s].y>0:pn[s]=-pn[s]
def palm(s,d,n):
 h=f'B_{s}_Hand';ph.worldrot(h,(ph.basis(d,n)@ph.basis(fd[s],pn[s]).transposed()).to_quaternion()@B[h].matrix_local.to_quaternion())
h='B_R_Hand';fl=B[h].matrix_local.to_3x3().inverted()@fd['R'];gripq=(ph.basis((0,0,1),(0,-1,0))@ph.basis(ga,fl).transposed()).to_quaternion()
feet={s:B[f'B_{s}_Foot'].head_local.copy() for s in ['L','R']}
def leg(s,target):
 ph.chain(s,target,r.pose.bones[f'B_{s}_Thigh'].head+Vector((0,-1,0)),leg=True);ph.worldrot(f'B_{s}_Foot',B[f'B_{s}_Foot'].matrix_local.to_quaternion());r.pose.bones[f'B_{s}_Toe0'].rotation_quaternion=Quaternion();ph.update()
def fingers(release=0):
 for n in names:
  if 'Finger' in n:
   q=Quaternion(G['finger_local'][n]) if n in G['finger_local'] else Quaternion().slerp(raw['Standing'][0][n][0],.14)
   r.pose.bones[n].rotation_quaternion=q.slerp(Quaternion(),release) if '_R_' in n else q
 ph.update()
rw=Vector((-.32,-.22,1.09));lw=Vector((.245,-.015,.886))
def arms(wr=rw,wl=lw,rq=gripq,lq=None):
 for s,w,sign in [('R',wr,-1),('L',wl,1)]:
  sh=r.pose.bones[f'B_{s}_UpperArm'].head;pole=Vector((sh.x+sign*.16,sh.y+.10,sh.z-.21));ph.chain(s,w,pole)
  if s=='R':
   fore=(r.pose.bones['B_R_Hand'].head-r.pose.bones['B_R_Forearm'].head).normalized();axis=rq@ga;rq=(ph.basis(axis,fore)@ph.basis(ga,fl).transposed()).to_quaternion();direction=rq@fl;angle=direction.angle(fore)
   if angle>math.radians(60):rq=Quaternion().slerp(direction.rotation_difference(fore),(angle-math.radians(60))/angle)@rq
   ph.worldrot('B_R_Hand',rq)
  elif lq is None:
   direction=Vector((0,0,-1));fore=(r.pose.bones['B_L_Hand'].head-r.pose.bones['B_L_Forearm'].head).normalized();angle=direction.angle(fore)
   if angle>math.radians(52):direction=Quaternion().slerp(direction.rotation_difference(fore),(angle-math.radians(52))/angle)@direction
   palm('L',direction,(-1,0,0))
  else:ph.worldrot('B_L_Hand',lq)
 # Limit anatomical roll after the mesh-derived palm orientation is applied.
 for sd in 'LR':
  fb,hb=B[f'B_{sd}_Forearm'],B[f'B_{sd}_Hand'];Rf=r.pose.bones[fb.name].matrix.to_quaternion()@fb.matrix_local.to_quaternion().inverted();Rh=r.pose.bones[hb.name].matrix.to_quaternion()@hb.matrix_local.to_quaternion().inverted();q=Rf.inverted()@Rh;axis=(hb.head_local-fb.head_local).normalized()
  tw=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);tw=(tw+math.pi)%math.tau-math.pi;clamped=min(math.radians(84),max(-math.radians(84),tw))
  ph.worldrot(hb.name,Rf@q@Quaternion(axis,clamped-tw)@hb.matrix_local.to_quaternion())
 fingers()
ph.apply(neutral);root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z-=.008;root.matrix=m;ph.update()
for s in feet:leg(s,feet[s])
arms();base=ph.capture();baseworld={n:r.pose.bones[n].matrix.copy() for n in names};out={}
for role in ['Standing','Fidget','Walking','Running']:
 ph.previous.clear();rows=[];N=120 if role=='Fidget' else 60 if role=='Standing' else len(raw[role])-1
 for i in range(N+1):
  ph.apply(base);t=i/N;wave=math.sin(math.tau*t);src=raw[role][round(t*(len(raw[role])-1))]
  for n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
   r.pose.bones[n].rotation_quaternion=base[n][0].slerp(src[n][0],.75 if role=='Running' else .45 if role=='Walking' else .6)
  ph.update();root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z+=.003*math.sin(t*math.tau*2);root.matrix=m;ph.update()
  for s,phase in [('L',0),('R',.5)]:
   target=feet[s].copy()
   if role in ['Walking','Running']:
    u=(t+phase)%1;d=.17 if role=='Walking' else .22
    if u<.55:target.y+=-d+2*d*u/.55
    else:
     v=(u-.55)/.45;target.y+=d-2*d*ph.smooth(v);target.z+=(.085 if role=='Walking' else .11)*math.sin(math.pi*v)
   leg(s,target)
  wr=rw+Vector((0,.02*wave if role=='Fidget' else (.10 if role=='Running' else .065)*wave if role in ['Walking','Running'] else .002*wave,.012*wave if role=='Fidget' else .002*wave));wl=lw+Vector((0,-(.19 if role=='Running' else .095)*wave if role in ['Walking','Running'] else -.018*wave if role=='Fidget' else .002*wave,(.12 if role=='Running' else 0)+.005*wave))
  arms(wr,wl,Quaternion((1,0,0),(.08 if role=='Fidget' else .03)*wave)@gripq)
  if role=='Fidget':ph.worldrot('B_Head',Quaternion((0,0,1),.17*wave)@r.pose.bones['B_Head'].matrix.to_quaternion())
  rows.append(ph.capture())
 rows[-1]=rows[0];out[role]=rows;ph.write(role,rows)
# Library trajectories retained above an upright stance; discrete steps use 20 percent source travel.
for role in ['Attack','Cast','Hit']:
 ph.previous.clear();rows=[];N=len(raw[role])-1
 W0=world[role][0];ch0=W0['B_Spine2'].to_quaternion();chb=baseworld['B_Spine2'].to_quaternion();C=chb@ch0.inverted()
 for i,src in enumerate(raw[role]):
  t=i/N;u=ph.smooth(i/(4 if role=='Hit' else 7))*ph.smooth((N-i)/(4 if role=='Hit' else 7));ph.apply(base)
  strength=.9 if role=='Hit' else .50 if role=='Attack' else .85
  for n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']:
   delta=src[n][0]@raw[role][0][n][0].inverted();q=delta@base[n][0];r.pose.bones[n].rotation_quaternion=base[n][0].slerp(q,u*strength);ph.update()
  root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();dp=world[role][i]['B_Pelvis'].translation-W0['B_Pelvis'].translation;m.translation+=Vector((dp.x*.2,dp.y*.2,min(0,dp.z*.2) if role=='Hit' else dp.z*.2))*u;
  if role=='Attack':m.translation.y-=.08*math.sin(math.pi*t)**2
  root.matrix=m;ph.update()
  for s in feet:
   target=feet[s].copy()
   if s=='L' and role!='Hit':
    # Short lifted outbound and return steps, with planted intervals.
    if t<.25:v=ph.smooth(t/.25);target.y-=.13*v;target.z+=.04*math.sin(math.pi*t/.25)
    elif t<.65:target.y-=.13
    elif t<.9:v=(t-.65)/.25;target.y-=.13*(1-ph.smooth(v));target.z+=.04*math.sin(math.pi*v)
   leg(s,target)
  dw={s:C@(world[role][i][f'B_{s}_Hand'].translation-W0[f'B_{s}_Hand'].translation) for s in ['L','R']}
  wr=rw+dw['R']*u*(.45 if role=='Hit' else .42 if role=='Attack' else .72);wl=lw+dw['L']*u*(.2 if role=='Hit' else .4)
  wr.x=min(wr.x,-.31);wr.y=min(wr.y,-.24 if role=='Attack' else -.16);wl.x=max(wl.x,.285);wl.y=min(wl.y,-.015)
  def track(keys):
   for (ta,a),(tb,b) in zip(keys,keys[1:]):
    if t<=tb:return Vector(a).lerp(Vector(b),ph.smooth((t-ta)/(tb-ta)))
   return Vector(keys[-1][1])
  if role=='Attack':
   lean=math.sin(math.pi*t)**2
   turn=track([(0,(0,0,0)),(.40,(0,0,-.28)),(.60,(0,0,.28)),(.78,(0,0,.15)),(1,(0,0,0))]).z
   ph.worldrot('B_Spine',Quaternion((0,0,1),turn)@r.pose.bones['B_Spine'].matrix.to_quaternion())
   for n in ['B_Spine','B_Spine1','B_Spine2']:ph.worldrot(n,Quaternion((1,0,0),track([(0,(0,0,0)),(.4,(-.025,0,0)),(.58,(.11,0,0)),(.74,(.07,0,0)),(1,(0,0,0))]).x)@r.pose.bones[n].matrix.to_quaternion())
   wr=track([(0,rw),(.20,(-.39,-.22,1.38)),(.40,(-.40,-.20,1.45)),(.58,(-.29,-.56,1.27)),(.72,(-.33,-.42,1.08)),(1,rw)])
   axis=track([(0,(0,0,1)),(.20,(0,-.35,.94)),(.40,(.20,-.94,.30)),(.49,(.35,.25,.90)),(.58,(-.30,.88,.36)),(.72,(-.50,.75,.43)),(1,(0,0,1))]).normalized()
   rq=(gripq@ga).rotation_difference(axis)@gripq
   wl=track([(0,lw),(.4,(.29,-.19,1.03)),(.60,(.40,.0,1.03)),(.78,(.32,.04,.94)),(1,lw)])
  elif role=='Cast':
   wl=lw+Vector((.06,-.055,.04))*math.sin(math.pi*t)**2
   wr=track([(0,rw),(.30,(-.34,-.18,1.36)),(.57,(-.30,-.61,1.31)),(.70,(-.30,-.61,1.31)),(1,rw)])
   axis=track([(0,(0,0,1)),(.30,(.1,-.1,.99)),(.57,(.30,-.70,.65)),(.70,(.30,-.70,.65)),(1,(0,0,1))]).normalized()
   rq=(gripq@ga).rotation_difference(axis)@gripq
   lean=math.sin(math.pi*t)**2
   for n in ['B_Spine','B_Spine1','B_Spine2']:
    ph.worldrot(n,Quaternion((1,0,0),.10*lean)@r.pose.bones[n].matrix.to_quaternion())
   root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.y-=.07*lean;root.matrix=m;ph.update()
   for sd in feet:leg(sd,feet[sd]+Vector((0,-.13 if sd=='L' else 0,0))*lean)
  else:
   lean=math.sin(math.pi*t)**2
   for n in ['B_Spine','B_Spine1','B_Spine2','B_Head']:
    ph.worldrot(n,Quaternion((1,0,0),-.18*lean)@r.pose.bones[n].matrix.to_quaternion())
   wr=rw+Vector((-.02,.08*lean,.18*lean));wl=lw+Vector((.08*lean,.06*lean,.12*lean));rq=Quaternion((1,0,0),-.25*lean)@gripq
  arms(wr,wl,rq);rows.append(ph.capture())
 if role in ['Attack','Cast']:rows=[base]*7+rows
 rows[0]=base;rows[-1]=base;out[role]=rows;ph.write(role,rows)

ph.apply(base);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round1_motion.blend'))
