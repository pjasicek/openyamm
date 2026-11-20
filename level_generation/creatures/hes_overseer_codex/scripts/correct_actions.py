"""Fit source arm motion to the retained limb proportions; distribute twist through the skin."""
import bpy,math,sys,os,runpy,json
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'))
from armik import split_swing_twist
bpy.ops.wm.open_mainfile(filepath=str(P/'work/overseer_actions.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;grips=json.loads((P/'work/grip_pose.json').read_text())
rest={b.name:b.matrix_local.copy() for b in rig.data.bones};order=[b.name for b in rig.data.bones]
def basis(a,b):
 a=a.normalized();b=(b-a*a.dot(b)).normalized();return Matrix((a,b,a.cross(b))).transposed()
def short_angle(q):return min(q.angle,2*math.pi-q.angle)
def active(action):
 rig.animation_data.action=action
 if action.slots:rig.animation_data.action_slot=action.slots[0]
def frame(f):scene.frame_set(math.floor(f),subframe=f%1)
summary={}
for action in [a for a in bpy.data.actions if a.name.startswith('Overseer_')]:
 active(action);end=float(action.frame_end);times=sorted(set(list(np.arange(0,end,1))+[end]));frames=[]
 for f in times:
  frame(f);frames.append({'local':{n:rig.pose.bones[n].matrix_basis.copy() for n in order},'world':{n:rig.pose.bones[n].matrix.copy() for n in order}})
 for sd in 'LR':
  un,fn,hn,cn=[f'B_{sd}_{p}' for p in ['UpperArm','Forearm','Hand','Clavicle']];ur,fr,hr=[rest[n].to_3x3().normalized() for n in [un,fn,hn]];ru=(rest[fn].translation-rest[un].translation).normalized();rf=(rest[hn].translation-rest[fn].translation).normalized()
  finger_axis=(sum((rest[f'B_{sd}_Finger{d}'].translation for d in range(6)),Vector())/6-rest[hn].translation).normalized();ha=hr.transposed()@finger_axis
  local_basis=basis(ur.transposed()@ru,Vector((0,0,-1)));candidates=[];costs=[];phis=np.arange(-180,180,5)
  for fi,fr0 in enumerate(frames):
   w=fr0['world'];S,E0,T=[w[n].translation.copy() for n in [un,fn,hn]];a=(E0-S).length;b=(T-E0).length
   time=times[fi]/48
   if sd=='L' and action.name=='Overseer_AttackRanged':
    # Place the fitted firing wrist below the eyes; the retained pistol is taller than the library prop.
    weight=max(0,min(1,time/.15))*max(0,min(1,(1.2-time)/.30));weight=weight*weight*(3-2*weight)
    T=T.lerp(S+Vector((.14,-.45,.055)),weight);E0=E0.lerp(S+Vector((.22,-.17,-.10)),weight)
   if sd=='R' and action.name=='Overseer_AttackMelee':
    window=max(0,min(1,(time-.95)/.3))*max(0,min(1,(2.4-time)/.5));window=window*window*(3-2*window);T.x=T.x*(1-window)+min(T.x,-.55)*window
    grip_axis=rest[hn].to_3x3().inverted()@Matrix(grips[sd]['rotation_bind'])@Vector((0,0,1));H=w[hn].to_quaternion();swing=(H@grip_axis).rotation_difference(Vector((0,0,1)));H=Quaternion().slerp(swing,window)@H;w[hn]=Matrix.LocRotScale(w[hn].translation,H,Vector((1,1,1)))
   if sd=='R' and action.name=='Overseer_Death':T.x-=.05
   if (T-S).length>(a+b)*.99:T=S+(T-S).normalized()*(a+b)*.99
   d=(T-S).length;axis=(T-S).normalized();pole=(E0-S)-axis*(E0-S).dot(axis);pole.normalize();ca=max(-1,min(1,(a*a+d*d-b*b)/(2*a*d)));neutral_u=w[cn].to_3x3().normalized()@rest[cn].to_3x3().normalized().transposed()@ur
   row=[];cs=[]
   for phi in phis:
    E=S+a*(axis*ca+(Quaternion(axis,math.radians(float(phi)))@pole)*math.sqrt(max(0,1-ca*ca)));u=(E-S).normalized();f=(T-E).normalized();hinge=u.cross(f).normalized();U=basis(u,hinge)@local_basis.transposed();F0=U@ur.transposed()@fr;F=(F0@(fr.transposed()@rf)).rotation_difference(f).to_matrix()@F0
    neutral_h=F@fr.transposed()@hr;rel=(neutral_h.transposed()@w[hn].to_3x3().normalized()).to_quaternion();sw,tw=split_swing_twist(rel,ha);swing=math.degrees(short_angle(sw));roll=math.degrees(tw);_,ut=split_swing_twist((neutral_u.transposed()@U).to_quaternion(),ur.transposed()@ru);upper=abs(math.degrees(ut))
    # Preserve the library hand direction whenever the fitted wrist can support it.
    clamped=Quaternion().slerp(sw,min(1,math.radians(45)/max(short_angle(sw),1e-8)))@Quaternion(ha,max(-math.radians(70),min(math.radians(70),tw)))
    H=neutral_h@clamped.to_matrix();change=math.degrees(short_angle(w[hn].to_quaternion().rotation_difference(H.to_quaternion())))
    cost=200*max(0,upper-50)**2+4*max(0,swing-45)**2+max(0,abs(roll)-70)**2+.015*float(phi)**2+.02*change**2
    row.append((U,F,H));cs.append(cost)
   candidates.append(row);costs.append(cs)
  delta=(phis[:,None]-phis[None,:]+180)%360-180;transition=.35*delta**2;acc=np.array(costs[0]);backs=[]
  for cs in costs[1:]:
   trials=acc[:,None]+transition;back=trials.argmin(0);backs.append(back);acc=np.array(cs)+trials[back,np.arange(len(phis))]
  path=[int(acc.argmin())]
  for back in reversed(backs):path.append(int(back[path[-1]]))
  path.reverse()
  for fr0,row,chosen in zip(frames,candidates,path):
   for n,M in fr0['local'].items():rig.pose.bones[n].matrix_basis=M
   bpy.context.view_layer.update()
   for n,R in zip([un,fn,hn],row[chosen]):
    pb=rig.pose.bones[n];M=R.to_4x4();M.translation=pb.head;pb.matrix=M;bpy.context.view_layer.update();fr0['local'][n]=pb.matrix_basis.copy()
  summary[action.name+' '+sd]={'max_elbow_adjustment_deg':int(max(abs(phis[i]) for i in path))}
 # Smooth the fitted local rotations, including the source trunk/wing transitions.
 for _ in range(10 if action.name=='Overseer_Cast' else 4):
  old=[{n:m.to_quaternion() for n,m in fr0['local'].items()} for fr0 in frames]
  for i in range(1,len(frames)-1):
   for n in order:
    if '_Finger' in n and not n.startswith('B_Wing'):continue
    m=frames[i]['local'][n];q=old[i][n].slerp(old[i-1][n].slerp(old[i+1][n],.5),.5);_,_,scale=m.decompose();frames[i]['local'][n]=Matrix.LocRotScale(m.translation,q,scale)
 if action.name=='Overseer_AttackRanged':
  # Keep the fitted library aim and add a controlled wrist recoil for this heavy pulse pistol.
  directions=[]
  for fr0 in frames:
   for n,M in fr0['local'].items():rig.pose.bones[n].matrix_basis=M
   bpy.context.view_layer.update();M=rig.pose.bones['B_L_Hand'].matrix.to_3x3()@rest['B_L_Hand'].to_3x3().inverted()@Matrix(grips['L']['rotation_bind']);directions.append(M@Vector((0,-1,0)))
  aim_i=max((i for i,t in enumerate(times) if .15<=t/48<=.42),key=lambda i:-directions[i].y)

  names=[f'B_L_{part}' for part in ['UpperArm','Forearm','Hand']]
  for n,M in frames[aim_i]['local'].items():rig.pose.bones[n].matrix_basis=M
  bpy.context.view_layer.update();aim_upper=rig.pose.bones['B_L_UpperArm'].matrix.to_quaternion()
  ready={n:frames[0]['local'][n].copy() for n in names};aim={n:frames[aim_i]['local'][n].to_quaternion() for n in names};kick={n:q.copy() for n,q in aim.items()};axis=rest['B_L_Hand'].to_3x3().inverted()@Matrix(grips['L']['rotation_bind'])@Vector((1,0,0));kick['B_L_Hand']=aim['B_L_Hand']@Quaternion(axis,math.radians(-10))
  def ease(x):x=max(0,min(1,x));return max(0,min(1,x*x*x*(10+x*(-15+6*x))))
  for f,fr0 in zip(times,frames):
   t=f/48;weight=ease((t-.03)/.32)*(1-ease((t-.85)/.35));recoil=ease((t-.45)/.08)*(1-ease((t-.53)/.20))
   for n in names:
    loc,q,scale=ready[n].decompose();q=q.slerp(aim[n].slerp(kick[n],recoil),weight);fr0['local'][n]=Matrix.LocRotScale(loc,q,scale)
   # Counter the flight clavicle sway while aiming, retaining the fitted elbow/wrist shape.
   for n,M in fr0['local'].items():rig.pose.bones[n].matrix_basis=M
   bpy.context.view_layer.update();pb=rig.pose.bones['B_L_UpperArm'];current=pb.matrix.to_quaternion();target=aim_upper
   M=Matrix.LocRotScale(pb.head,current.slerp(target,weight),Vector((1,1,1)));pb.matrix=M;bpy.context.view_layer.update();fr0['local'][pb.name]=pb.matrix_basis.copy()
  record={'source':'PistolAttackL1 fitted poses; ArmedIdle ready','aim_source_time_s':times[aim_i]/48,'recoil_layer':'10 degree upward muzzle kick about fitted grip axis','recoil_degrees':10,'aim_hold_s':[.35,.45],'release_s':.45,'recoil_peak_s':.53,'aim_recovered_s':.73,'lower_start_s':.85,'end_s':1.2,'interpolation':'quintic ease, sign-continuous quaternion blend'}
  (P/'work/ranged_fit.json').write_text(json.dumps(record,indent=2)+'\n')
 previous={}
 for f,fr0 in zip(times,frames):
  for n,M in fr0['local'].items():
   pb=rig.pose.bones[n];loc,q,scale=M.decompose()
   if n in previous and q.dot(previous[n])<0:q.negate()
   previous[n]=q.copy();pb.rotation_mode='QUATERNION';pb.location=loc;pb.rotation_quaternion=q;pb.scale=scale
   for key in ['location','rotation_quaternion','scale']:pb.keyframe_insert(key,frame=float(f))
 print('FITTED',action.name,flush=True)
rig.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/overseer_joint_corrected.blend'))
(P/'work/joint_fit.json').write_text(json.dumps(summary,indent=2)+'\n')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
sys.argv=['twist_bones.py','--',str(P/'work/overseer_joint_corrected.blend'),str(P/'work/overseer_actions.blend')]
runpy.run_path(str(P.parent/'mm6_natm_claude/scripts/twist_bones.py'),run_name='__main__')
# Blend the fitted elbow/wrist skin over existing mesh edges, preserving finger ownership.
body=bpy.data.objects['Body'];co=np.array([v.co[:] for v in body.data.vertices]);unique,inv=np.unique(np.round(co,5),axis=0,return_inverse=True);edges=np.unique(np.sort(inv[np.array([e.vertices[:] for e in body.data.edges])],axis=1),axis=0);counts=np.bincount(inv)
for sd in 'LR':
 names=[f'B_{sd}_{n}' for n in ['UpperArm','UpperArmTwist','Forearm','ForearmTwist','Hand','Clavicle']]+['B_Spine','B_Spine1','B_Spine2'];groups=[body.vertex_groups[n] for n in names];lookup={g.index:i for i,g in enumerate(groups)};raw=np.zeros((len(co),len(groups)));finger=np.zeros(len(co))
 for v in body.data.vertices:
  for g in v.groups:
   if g.group in lookup:raw[v.index,lookup[g.group]]=g.weight
   if body.vertex_groups[g.group].name.startswith(f'B_{sd}_Finger'):finger[v.index]+=g.weight
 total=raw.sum(1);u=np.zeros((len(unique),len(groups)));np.add.at(u,inv,raw);u/=counts[:,None];uf=np.zeros(len(unique));np.add.at(uf,inv,finger);uf/=counts;fraction=u.sum(1);sx=unique[:,0]*(1 if sd=='L' else -1);armpit=(sx>.07)&(sx<.27)&(unique[:,2]>.92)&(unique[:,2]<1.22);palm_axis=np.array((sum((rest[f'B_{sd}_Finger{d}'].translation for d in range(6)),Vector())/6-rest[f'B_{sd}_Hand'].translation).normalized());distal=(unique-np.array(rest[f'B_{sd}_Hand'].translation))@palm_axis;allowed=(fraction>.05)&(uf<.05)&((u[:,:5].sum(1)>.3)|armpit)&(distal<.015);ee=edges[allowed[edges].all(1)]
 for _ in range(6):
  sums=u.copy();degree=np.ones(len(u));np.add.at(sums,ee[:,0],u[ee[:,1]]);np.add.at(sums,ee[:,1],u[ee[:,0]]);np.add.at(degree,ee[:,0],1);np.add.at(degree,ee[:,1],1);u=.65*u+.35*sums/degree[:,None];u*=fraction[:,None]/np.maximum(u.sum(1)[:,None],1e-12)
 smoothed=u[inv];smoothed*=total[:,None]/np.maximum(smoothed.sum(1)[:,None],1e-12)
 for j,g in enumerate(groups):
  g.remove(list(range(len(co))))
  for vi in np.flatnonzero(smoothed[:,j]>1e-8):g.add([int(vi)],float(smoothed[vi,j]),'REPLACE')
# The runtime supports four weights; prune only the added twist blends and renormalize.
for o in bpy.data.objects:
 if o.type!='MESH':continue
 for v in o.data.vertices:
  ws=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-8],key=lambda x:-x[1]);keep=ws[:4];total=sum(w for _,w in keep)
  if not total:continue
  for gi,w in ws:o.vertex_groups[gi].remove([v.index])
  for gi,w in keep:o.vertex_groups[gi].add([v.index],w/total,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/overseer_actions.blend'))
