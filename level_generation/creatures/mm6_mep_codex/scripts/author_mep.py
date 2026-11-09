import bpy,sys,json,math
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
   fore=(r.pose.bones['B_R_Hand'].head-r.pose.bones['B_R_Forearm'].head).normalized();direction=rq@fl;angle=direction.angle(fore)
   if angle>math.radians(48):rq=Quaternion().slerp(direction.rotation_difference(fore),(angle-math.radians(48))/angle)@rq
   ph.worldrot('B_R_Hand',rq)
  elif lq is None:palm('L',(0,0,-1),(-1,0,0))
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
   r.pose.bones[n].rotation_quaternion=base[n][0].slerp(src[n][0],.35 if role in ['Walking','Running'] else .6)
  ph.update();root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z+=.003*math.sin(t*math.tau*2);root.matrix=m;ph.update()
  for s,phase in [('L',0),('R',.5)]:
   target=feet[s].copy()
   if role in ['Walking','Running']:
    u=(t+phase)%1;d=.17 if role=='Walking' else .22
    if u<.55:target.y+=-d+2*d*u/.55
    else:
     v=(u-.55)/.45;target.y+=d-2*d*ph.smooth(v);target.z+=(.085 if role=='Walking' else .11)*math.sin(math.pi*v)
   leg(s,target)
  wr=rw+Vector((0,.02*wave if role=='Fidget' else .045*wave if role in ['Walking','Running'] else .002*wave,.012*wave if role=='Fidget' else .002*wave));wl=lw+Vector((0,-.045*wave if role in ['Walking','Running'] else -.018*wave if role=='Fidget' else .002*wave,.005*wave))
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
  strength=.32 if role=='Hit' else .22 if role=='Attack' else .68
  for n in ['B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head','B_L_Clavicle','B_R_Clavicle']:
   delta=world[role][i][n].to_quaternion()@W0[n].to_quaternion().inverted();q=(C@delta@C.inverted())@baseworld[n].to_quaternion();ph.worldrot(n,baseworld[n].to_quaternion().slerp(q,u*strength))
  root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();dp=world[role][i]['B_Pelvis'].translation-W0['B_Pelvis'].translation;m.translation+=Vector((dp.x*.2,dp.y*.2,min(0,dp.z*.2) if role=='Hit' else dp.z*.2))*u;root.matrix=m;ph.update()
  for s in feet:
   target=feet[s].copy()
   if s=='L' and role!='Hit':
    # Short lifted outbound and return steps, with planted intervals.
    if t<.25:v=ph.smooth(t/.25);target.y-=.07*v;target.z+=.04*math.sin(math.pi*t/.25)
    elif t<.65:target.y-=.07
    elif t<.9:v=(t-.65)/.25;target.y-=.07*(1-ph.smooth(v));target.z+=.04*math.sin(math.pi*v)
   leg(s,target)
  dw={s:C@(world[role][i][f'B_{s}_Hand'].translation-W0[f'B_{s}_Hand'].translation) for s in ['L','R']}
  wr=rw+dw['R']*u*(.45 if role=='Hit' else .42 if role=='Attack' else .72);wl=lw+dw['L']*u*(.2 if role=='Hit' else .4)
  wr.x=min(wr.x,-.31);wr.y=min(wr.y,-.24 if role=='Attack' else -.16);wl.x=max(wl.x,.285);wl.y=min(wl.y,-.015)
  if role=='Attack':wr.z=min(1.35,max(1.01,wr.z));wr.y=min(-.36,max(-.52,wr.y));wr.x=max(-.48,wr.x)
  delta=world[role][i]['B_R_Hand'].to_quaternion()@W0['B_R_Hand'].to_quaternion().inverted();rq=gripq.slerp((C@delta@C.inverted())@gripq,u*(.55 if role=='Hit' else .75))
  if role=='Attack':
   ax=rq@ga;safe=Vector((ax.x,max(.12,ax.y),ax.z)).normalized();rq=ax.rotation_difference(safe)@rq
  if role=='Cast':rq=Quaternion((1,0,0),.72*math.sin(math.pi*t)*u)@rq;wr.y-=.06*math.sin(math.pi*t)*u
  arms(wr,wl,rq);rows.append(ph.capture())
 if role in ['Attack','Cast']:rows=[base]*7+rows
 rows[0]=base;rows[-1]=base;out[role]=rows;ph.write(role,rows)
# The Mixamo backward fall supplies momentum and lower-body motion.
ph.previous.clear();rows=[];N=len(raw['Death'])-1
pv=np.zeros(len(body.data.vertices),np.int32);body.data.attributes['piece'].data.foreach_get('value',pv)
for i,src in enumerate(raw['Death']):
 u=ph.smooth(i/10);ph.apply(ph.blend(base,src,u));ph.update()
 chest=r.pose.bones['B_Spine2'].matrix.to_quaternion()@baseworld['B_Spine2'].to_quaternion().inverted()
 for s,sign in [('R',-1),('L',1)]:
  h=f'B_{s}_Hand';sh=r.pose.bones[f'B_{s}_UpperArm'].head.copy();rel=baseworld[h].translation-baseworld[f'B_{s}_UpperArm'].translation;rel=rel.lerp(Vector((sign*.30,-.025,-.32)),ph.smooth(i/22))
  wr=sh+chest@rel;pole=sh+chest@Vector((sign*.17,.09,-.20));ph.chain(s,wr,pole)
  q=chest@baseworld[h].to_quaternion();fore=(r.pose.bones[h].head-r.pose.bones[f'B_{s}_Forearm'].head).normalized();direction=q@(B[h].matrix_local.to_3x3().inverted()@fd[s]);angle=direction.angle(fore)
  if angle>math.radians(48):q=Quaternion().slerp(direction.rotation_difference(fore),(angle-math.radians(48))/angle)@q
  ph.worldrot(h,q)
 fingers(ph.smooth((i-18)/12))
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(v.co.z for v in me.vertices);ev.to_mesh_clear();root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z-=low;root.matrix=m;ph.update();rows.append(ph.capture())
out['Death']=rows;ph.write('Death',rows);ph.write('Dead',[rows[-1]]*31);out['Dead']=[rows[-1]]*31
ph.apply(base);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/anim_pilot.blend'))
common.workbench_clay(scene,textured=True)
for role,frames in ([] if __import__('os').environ.get('SKIP_PILOT_RENDERS') else [('Standing',[0]),('Walking',[3,18]),('Attack',[7,20,28]),('Cast',[15,22]),('Death',[25,N])]):
 ph.setact(bpy.data.actions[role])
 for f in frames:
  scene.frame_set(f);common.render_views(str(p/'review'/f'pilot_{role}_{f}'),.85,2.05,views=('front','left','three_quarter'),resolution=(600,800))
(p/'work/clip_durations.json').write_text(json.dumps({k:(len(v)-1)/30 for k,v in out.items()},indent=2))
