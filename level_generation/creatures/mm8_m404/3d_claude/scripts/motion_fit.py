"""Fit continuous elbow planes and hand roll to the shared sword grip."""
import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_stance.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene
G={s:json.load(open(p/('work/grip_pose_'+s+'.json'))) for s in 'RL'}
C={s:Vector(G[s]['handle_centre_hand_local']) for s in G};A={s:Vector(G[s]['handle_axis_hand_local']).normalized() for s in G}
SOURCE_A=Vector(json.load(open(p/'work/grip_source_R.json'))['axis_hand']).normalized()
def setact(act):
 rig.animation_data_create();rig.animation_data.action=act
 if act is not None and len(act.slots):rig.animation_data.action_slot=act.slots[0]
def restore(snap):
 for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def smooth(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
skin=np.load(p/'work/surface_cost.npz');skin_names=list(skin['names']);cost_data={}
for side in 'RL':
 names=['B_'+side+'_'+n for n in ('UpperArm','Forearm','Hand')]
 w=skin['weights'];arm=w[:,[skin_names.index(n) for n in names]].sum(1)
 edges=skin['edges'];keep=(skin['piece']==0)&(arm>.15)&(skin['co'][:,2]>1.12)
 edges=edges[keep[edges].all(1)];ids,edge=np.unique(edges,return_inverse=True);edge=edge.reshape(-1,2)
 co=skin['co'][ids];length=np.linalg.norm(co[edge[:,0]]-co[edge[:,1]],axis=1)
 parts={n:(np.c_[co,np.ones(len(co))]@np.array(rig.data.bones[n].matrix_local.inverted()).T)*w[ids,skin_names.index(n),None] for n in skin_names if n in rig.data.bones and w[ids,skin_names.index(n)].max()>1e-6}
 cost_data[side]=(parts,edge,length)
head_points=skin['co'][(skin['piece']==7)&(skin['co'][:,2]>1.65)]
head_local=(np.c_[head_points,np.ones(len(head_points))]@np.array(rig.data.bones['B_Head'].matrix_local.inverted()).T)[:,:3]
head_center=(head_local.min(0)+head_local.max(0))*.5
head_radii=(head_local.max(0)-head_local.min(0))*.5+.08
PH=np.arange(-180,180,10);PS=np.arange(0,360,10)
dp=np.abs((PH[:,None]-PH[None,:]+180)%360-180)*1.0;ds=np.abs((PS[:,None]-PS[None,:]+180)%360-180)*1.0

def fit_side(side,frames):
 step=float(frames[1]['time']-frames[0]['time']) if len(frames)>1 else 1.
 dp=np.abs((PH[:,None]-PH[None,:]+180)%360-180);ds=np.abs((PS[:,None]-PS[None,:]+180)%360-180)
 dp=np.where(dp>max(10,60*step),1e8,dp);ds=np.where(ds>max(10,60*step),1e8,ds)
 names=['B_'+side+'_'+s for s in ('UpperArm','Forearm','Hand')]
 rel=(rig.data.bones[names[1]].matrix_local.to_3x3().inverted()@rig.data.bones[names[2]].matrix_local.to_3x3()).inverted()
 tables=[];roll_tables=[];joint_tables=[]
 sample_frames=[frames[i] for i in np.unique(np.linspace(0,len(frames)-1,min(9,len(frames))).astype(int))] if act.name in ('Standing','Walking','Fidget') else frames
 for fr in sample_frames:
  Mu,Mf,Mh=fr['mat'][side];center=fr['center']-(fr['axis']*.15 if side=='L' else Vector())
  hand_rest=rig.data.bones[names[2]].matrix_local;fore_rest=rig.data.bones[names[1]].matrix_local
  roots=[rig.data.bones['B_'+side+'_Finger'+str(k)].head_local for k in (0,1,2,4)]
  hand_axis=(hand_rest.to_3x3().inverted()@(sum(roots,Vector())/len(roots)-hand_rest.translation)).normalized()
  fore_axis=(fore_rest.inverted()@hand_rest.translation).normalized()
  ur=rig.data.bones[names[0]].matrix_local.to_3x3();cr=rig.data.bones['B_'+side+'_Clavicle'].matrix_local.to_3x3()
  neutral=fr['clavicle'][side]@cr.inverted()@ur
  uaxis=(ur.inverted()@(rig.data.bones[names[1]].head_local-rig.data.bones[names[0]].head_local)).normalized()
  parts,edge,length=cost_data[side]
  const=sum((v@fr['world'][n].T)[:,:3] for n,v in parts.items() if n not in names)
  table=np.empty((len(PH),len(PS)));rolls=np.empty_like(table);joints=np.empty((*table.shape,3,4))
  along=np.linspace(.2,1.06,9)[:,None]
  for j,psi in enumerate(PS):
   R=Quaternion(fr['axis'],math.radians(psi)).to_matrix()@fr['base'][side];T=center-R@C[side]
   for i,phi in enumerate(PH):
    F,_,reach,U,E,actualT=armik.fitted(Mu,Mf,Mh,T,phi)
    fore_delta=(F.inverted()@R@rel).to_quaternion();_,fore_roll=armik.split_swing_twist(fore_delta,fore_axis)
    distal=F@Quaternion(fore_axis,.6*fore_roll).to_matrix();q=(rel@distal.inverted()@R).to_quaternion()
    sw,tw=armik.split_swing_twist(q,hand_axis);sw=math.degrees(min(sw.angle,2*math.pi-sw.angle));tw=abs(math.degrees(tw))
    _,ut=armik.split_swing_twist((neutral.inverted()@U).to_quaternion(),uaxis);ut=abs(math.degrees(ut))
    posed=const.copy()
    for n,rot,loc in zip(names,(U,F,R),(Mu.translation,E,actualT)):
     if n not in parts:continue
     M=rot.to_4x4();M.translation=loc;posed+=(parts[n]@np.array(M).T)[:,:3]
    stretch=np.linalg.norm(posed[edge[:,0]]-posed[edge[:,1]],axis=1)/np.maximum(length,1e-6)
    p99=float(np.quantile(stretch,.99));skin_cost=1500*max(0,p99-1.90)**2+30*p99
    points=np.array(E)[None]+along*(np.array(actualT)-np.array(E))[None]
    # A torso capsule and the fitted opposite forearm keep IK elbows from folding through skin.
    world_center=fr['world']['B_Spine1'][:3,3];chest_R=fr['world']['B_Spine1'][:3,:3]
    delta=(points-world_center)@chest_R;delta[:,1]+=.06
    cross=np.sqrt((delta[:,0]/.25)**2+(delta[:,2]/.28)**2+(delta[:,1]/.31)**2)
    clearance=100000*np.maximum(0,1-cross).max()**2
    upper=np.array(Mu.translation)[None]+np.linspace(.25,1,7)[:,None]*(np.array(E)-np.array(Mu.translation))[None]
    hp=np.concatenate([upper,points]);head=fr['world']['B_Head']
    hlocal=(hp-head[:3,3])@head[:3,:3]-head_center
    clearance+=100000*max(0,1-np.linalg.norm(hlocal/head_radii,axis=1).min())**2
    if 'other_forearm' in fr:
     other=fr['other_forearm'];distance=np.linalg.norm(points[:,None]-other[None],axis=2).min()
     clearance+=1e7*max(0,.215-distance)**2
    rolls[i,j]=math.degrees(fore_roll)
    joints[i,j]=[list((neutral.inverted()@U).to_quaternion()),list((U.inverted()@F).to_quaternion()),list((F.inverted()@R).to_quaternion())]
    table[i,j]=2000*max(0,abs(math.degrees(fore_roll))-135)**2+clearance+skin_cost+100*max(0,ut-58)**2+.25*ut+sw+.03*sw*sw+.4*tw+.13*abs(phi)+100*max(0,sw-52)**2+100*max(0,tw-43)**2+1e6*max(0,reach-.995)**2
  tables.append(table);roll_tables.append(rolls);joint_tables.append(joints)
 if act.name in ('Standing','Fidget','Walking'):
  i,j=np.unravel_index(np.sum(tables,axis=0).argmin(),tables[0].shape)
  return [(float(PH[i]),float(PS[j]))]*len(frames)
 constrained={}
 if side in home_controls:
  ends=[0,len(frames)-1] if act.name in ('Attack','Hit') else [0] if act.name=='Death' else []
  for k in ends:
   phi,H=home_controls[side];axis=frames[k]['axis'];base=frames[k]['base'][side];q=(H@base.inverted()).to_quaternion();_,psi=armik.split_swing_twist(q,axis);psi=math.degrees(psi)
   i=int(np.argmin(abs((PH-phi+180)%360-180)));j=int(np.argmin(abs((PS-psi+180)%360-180)));keep=tables[k][i,j];tables[k][:]=1e8;tables[k][i,j]=keep;constrained[k]=(phi,psi)
 acc=tables[0].copy();back=[]
 # Compare actual joint motion; parameter-space distance alone can cross the forearm's roll boundary.
 ip,jp=np.indices(acc.shape);reach=max(1,int(60*step/10))
 for k,table in enumerate(tables[1:],1):
  best=np.full_like(acc,np.inf);chosen=np.zeros(acc.shape+(2,),int)
  for di in range(-reach,reach+1):
   for dj in range(-reach,reach+1):
    pi=(ip+di)%len(PH);pj=(jp+dj)%len(PS)
    dots=np.abs(np.sum(joint_tables[k]*joint_tables[k-1][pi,pj],axis=-1))
    angle=np.degrees(2*np.arccos(np.clip(dots,0,1))).max(-1)
    roll_delta=np.abs(roll_tables[k]-roll_tables[k-1][pi,pj])
    penalty=1e4*np.maximum(0,angle-max(8,50*step))**2+1e4*np.maximum(0,roll_delta-max(8,60*step))**2
    cost=acc[pi,pj]+10*(abs(di)+abs(dj))+penalty
    use=cost<best;best[use]=cost[use];chosen[use]=np.stack([pi,pj],axis=-1)[use]
  acc=best+table;back.append(chosen)
 i,j=np.unravel_index(acc.argmin(),acc.shape);path=[(i,j)]
 for chosen in reversed(back):i,j=chosen[i,j];path.append((i,j))
 path.reverse();phi=np.degrees(np.unwrap(np.radians([PH[i] for i,j in path])));psi=np.unwrap(np.radians([PS[j] for i,j in path]))
 # Smooth only the fit controls; the sourced body and blade trajectory retain their keyed timing.
 kernel=np.array([1,8,1],float)/10
 phi=np.convolve(np.pad(phi,1,mode='edge'),kernel,'valid');psi=np.degrees(np.convolve(np.pad(psi,1,mode='edge'),kernel,'valid'))
 result=list(zip(phi,psi))
 for k,(a,b) in constrained.items():
  reference=result[k][1];b=reference+(b-reference+180)%360-180;result[k]=(a,b)
 return result
setact(bpy.data.actions['Standing']);sc.frame_set(0)
homeChestMatrix=armik.W(rig,'B_Spine2').copy();homeChest=homeChestMatrix.translation.copy();homePelvis=armik.W(rig,'B_Pelvis').copy()
homeWrist=armik.W(rig,'B_R_Hand').translation.copy();homeShoulder=armik.W(rig,'B_R_UpperArm').translation.copy()
guardAxis=Vector((.75,-.20,.63)).normalized();guardCenter=Vector((.05,-.30,1.30))
homeShoulderMean=(armik.W(rig,'B_L_UpperArm').translation+homeShoulder)*.5
def lift_gaze(act,f):
 if act.name!='Attack':return
 M=armik.W(rig,'B_Head');R=M.to_3x3();rest=rig.data.bones['B_Head'].matrix_local.to_3x3()
 forward=R@rest.inverted()@Vector((0,-1,0));right=Vector((0,0,1)).cross(forward).normalized()
 q=Quaternion(right,-math.radians(12)*math.exp(-((f-11.8)/3)**2))
 armik.set_world(rig,'B_Head',armik.rot_world(M,q.to_matrix()@R))
def bake_rotations(act,poses):
 setact(act);previous={}
 for f,pose in poses:
  for n,q in pose.items():
   if n in previous and q.dot(previous[n])<0:q=-q
   previous[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
report={};home_controls={};homeArms={};homeClavs={}

order={name:i for i,name in enumerate(('Standing','Walking','Fidget','Attack','Hit','Death'))}
for act in sorted([a for a in bpy.data.actions if a.use_fake_user],key=lambda a:order[a.name]):
 frames=[]
 if act.name=='Attack':
  # Rotate the closed two-hand assembly about the shoulder line; both grips stay exact through the chop.
  shoulder=homeArms['R'][0].translation;across=(homeArms['L'][0].translation-shoulder).normalized()
  keys=[(0,0),(8,-70),(10,-70),(16,15),(23,10),(36,0)];poses=[];gaps=[];swings=[]
  for f in np.arange(0,float(act.frame_range[1])+.01,.25):
   setact(act);sc.frame_set(int(f),subframe=float(f%1));lift_gaze(act,f)
   snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};setact(None);restore(snap)
   for side in 'RL':rig.pose.bones['B_'+side+'_Clavicle'].matrix_basis=homeClavs[side]
   bpy.context.view_layer.update();D=armik.W(rig,'B_Spine2')@homeChestMatrix.inverted()
   i=max(0,min(len(keys)-2,next((i-1 for i,k in enumerate(keys) if k[0]>f),len(keys)-2)))
   a,b=keys[i],keys[i+1];t=smooth((f-a[0])/(b[0]-a[0]));Q=Quaternion(across,math.radians(a[1]*(1-t)+b[1]*t)).to_matrix()
   for side in 'RL':
    for name,M in zip(('UpperArm','Forearm','Hand'),homeArms[side]):
     target=(Q@M.to_3x3()).to_4x4();target.translation=shoulder+Q@(M.translation-shoulder)
     armik.set_world(rig,'B_'+side+'_'+name,D@target)
    for name,value in G[side]['finger_local'].items():rig.pose.bones[name].rotation_quaternion=Quaternion(value)
    bpy.context.view_layer.update();swings.append(armik.wrist_cost(rig,side,armik.W(rig,'B_'+side+'_Hand').to_3x3())[0])
   R=armik.W(rig,'B_R_Hand');L=armik.W(rig,'B_L_Hand');axis=(R.to_3x3()@A['R']).normalized()
   gaps.append(((R@C['R']-axis*.15)-(L@C['L'])).length)
   poses.append((float(f),{n:rig.pose.bones[n].rotation_quaternion.copy() for n in rig.pose.bones.keys()}))
  bake_rotations(act,poses)
  report[act.name]={'max_grip_gap_m':max(gaps),'max_wrist_swing_deg':max(swings),'max_left_reach':1.0,'method':'closed grip shoulder-line chop over fitted source body'}
  print('TWOHAND',act.name,report[act.name],flush=True)
  continue
 if act.name=='Death':
  setact(act);sc.frame_set(int(act.frame_range[1]));D=armik.W(rig,'B_Spine2')@homeChestMatrix.inverted()
  along=(armik.W(rig,'B_L_Foot').translation+armik.W(rig,'B_R_Foot').translation)*.5-armik.W(rig,'B_Head').translation
  along.z=0;along.normalize();shoulder=armik.W(rig,'B_R_UpperArm').translation
  out=shoulder-armik.W(rig,'B_Spine2').translation;out.z=0;out.normalize()
  target=shoulder+out*.45+along*.10;target.z=shoulder.z+.04
  deathCenter=D.inverted()@target;deathAxis=(D.to_3x3().inverted()@along).normalized()
 frame_step=.25 if act.name in ('Attack','Death') else 1.
 for f in np.arange(0,float(act.frame_range[1])+.01,frame_step):
  setact(act);sc.frame_set(int(f),subframe=float(f%1));lift_gaze(act,f);snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};setact(None);restore(snap)
  mats={s:[armik.W(rig,'B_'+s+'_'+n).copy() for n in ('UpperArm','Forearm','Hand')] for s in 'RL'}
  RH=mats['R'][2];axis=(RH.to_3x3()@SOURCE_A).normalized();center=RH@C['R']
  if act.name in ('Standing','Fidget','Walking'):
   delta=armik.W(rig,'B_Spine2')@homeChestMatrix.inverted()
   center=delta@guardCenter
   if act.name=='Walking':center+=(RH.translation-delta@homeWrist)*.3
   else:center+=Vector((0,0,.003*math.sin(f*.12)))
   axis=(delta.to_3x3()@guardAxis).normalized()
  elif act.name in ('Attack','Hit','Death'):
   end=int(act.frame_range[1]);enter=3 if act.name=='Hit' else 6;leave=5 if act.name=='Hit' else 10
   blend=smooth(f/enter)
   if act.name!='Death':blend=min(blend,smooth((end-f)/leave))
   axis=guardAxis.slerp(axis,blend).normalized();center=guardCenter.lerp(center,blend)
  if act.name=='Death':
   D=armik.W(rig,'B_Spine2')@homeChestMatrix.inverted();t=smooth((f-3)/12)
   center=D@(guardCenter.lerp(Vector((-.62,-.25,1.35)),t)+Vector((0,-.16*math.sin(math.pi*t),0)))
   forward=Vector((0,-1,.1)).normalized()
   localAxis=guardAxis.slerp(forward,smooth((f-3)/9)) if f<=12 else forward.slerp(Vector((-.1,0,-1)).normalized(),smooth((f-12)/12))
   axis=(D.to_3x3()@localAxis).normalized()
  if act.name=='Attack':
   # The longer muzzle needs an overhead arc carried outside its silhouette.
   keys=[(0,(.05,-.37,-.18),(.75,-.20,.63)),(3,(.03,-.40,.10),(.4,-.2,.9)),
         (7,(0,-.27,.40),(.1,.6,.8)),(10,(0,-.30,.38),(0,.4,.92)),
         (13,(0,-.50,.10),(0,-.95,.3)),(16,(0,-.50,.05),(0,-.95,-.31)),
         (20,(0,-.45,-.10),(0,-.9,-.44)),(25,(0,-.45,-.10),(.4,-.9,-.1)),
         (30,(.05,-.40,-.10),(.65,-.3,.70)),(36,(.05,-.37,-.18),(.75,-.20,.63))]
   i=max(0,min(len(keys)-2,next((i-1 for i,k in enumerate(keys) if k[0]>f),len(keys)-2)))
   a,b=keys[i],keys[i+1];t=smooth((f-a[0])/(b[0]-a[0]))
   shoulders=(mats['R'][0].translation+mats['L'][0].translation)*.5
   center=shoulders-homeShoulderMean+guardCenter+Vector(a[1]).lerp(Vector(b[1]),t)-Vector(keys[0][1])
   center.z=max(.95,center.z)
   axis=Vector(a[2]).normalized().slerp(Vector(b[2]).normalized(),t).normalized()
  if act.name=='Hit':center.y-=.04*math.sin(math.pi*f/float(act.frame_range[1]))
  # Centre the shared grip in the overlap of both arms' reachable volumes.
  if act.name!='Death' or f<=3:
   for _ in range(6):
    for s in 'RL':
     S,E,W=[m.translation for m in mats[s]];reach=(E-S).length+(W-E).length
     g=center-(axis*.15 if s=='L' else Vector());d=g-S;limit=reach+.06
     if d.length>limit:center-=d.normalized()*(d.length-limit)
  # Use the fitted rest arm carried by its clavicle as a continuous IK reference.
  refs={}
  for side in 'RL':
   n='B_'+side+'_Clavicle';D=armik.W(rig,n)@rig.data.bones[n].matrix_local.inverted()
   refs[side]=[D@rig.data.bones['B_'+side+'_'+part].matrix_local for part in ('UpperArm','Forearm','Hand')]
  mats=refs
  frames.append({'time':float(f),'world':{n:np.array(armik.W(rig,n)) for n in rig.pose.bones.keys()},'clavicle':{s:armik.W(rig,'B_'+s+'_Clavicle').to_3x3().normalized() for s in 'RL'},'snap':snap,'mat':mats,'center':center,'axis':axis})
 # Parallel transport avoids a hand-roll discontinuity when the sword crosses vertical.
 bases={s:armik.hand_rot(A[s],frames[0]['axis'],0) for s in 'RL'};last=frames[0]['axis']
 for fr in frames:
  q=last.rotation_difference(fr['axis']).to_matrix();bases={s:q@R for s,R in bases.items()}
  fr['base']={s:R.copy() for s,R in bases.items()};last=fr['axis']
 paths={'R':fit_side('R',frames)}
 for fr,(phi,psi) in zip(frames,paths['R']):
  R=Quaternion(fr['axis'],math.radians(psi)).to_matrix()@fr['base']['R'];T=fr['center']-R@C['R'];_,_,_,_,E,T=armik.fitted(*fr['mat']['R'],T,phi)
  fore=np.array(E)[None]+np.linspace(.2,1.06,9)[:,None]*(np.array(T)-np.array(E))[None]
  S=np.array(fr['mat']['R'][0].translation);upper=S[None]+np.linspace(.35,1,7)[:,None]*(np.array(E)-S)[None]
  fr['other_forearm']=np.concatenate([upper,fore])
 paths['L']=fit_side('L',frames)
 if act.name=='Standing':
  for side in 'RL':
   phi,psi=paths[side][0];home_controls[side]=(phi,Quaternion(frames[0]['axis'],math.radians(psi)).to_matrix()@frames[0]['base'][side])
 poses=[];gaps=[];swings=[];reaches=[]
 for f in np.arange(0,frames[-1]['time']+.01,.25):
  index=f/frame_step;lo=int(index);hi=min(lo+1,len(frames)-1);fraction=float(index-lo);a,b=frames[lo],frames[hi]
  setact(act);sc.frame_set(int(f),subframe=float(f%1));lift_gaze(act,f);snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};setact(None);restore(snap)
  refs={}
  for side in 'RL':
   n='B_'+side+'_Clavicle';D=armik.W(rig,n)@rig.data.bones[n].matrix_local.inverted()
   refs[side]=[D@rig.data.bones['B_'+side+'_'+part].matrix_local for part in ('UpperArm','Forearm','Hand')]
  fr={'snap':snap,'mat':refs,'center':a['center'].lerp(b['center'],fraction),'axis':a['axis'].slerp(b['axis'],fraction).normalized(),'base':{side:a['base'][side].to_quaternion().slerp(b['base'][side].to_quaternion(),fraction).to_matrix() for side in 'RL'}}
  # Keep both grips on the same shaft between the source's keys.
  for side in 'RL':
   local_axis=(fr['base'][side]@A[side]).normalized();fr['base'][side]=local_axis.rotation_difference(fr['axis']).to_matrix()@fr['base'][side]
  restore(fr['snap'])
  for side in 'RL':
   for part in ('UpperArm','Forearm','Hand'):rig.pose.bones['B_'+side+'_'+part].matrix_basis=Matrix()
  bpy.context.view_layer.update()
  release=smooth((f-3)/6) if act.name=='Death' else 0
  rotations={}
  for side in 'RL':
   phi,psi=np.array(paths[side][lo])*(1-fraction)+np.array(paths[side][hi])*fraction
   rotations[side]=Quaternion(fr['axis'],math.radians(psi)).to_matrix()@fr['base'][side]
  # Project wrists, including each hand's real grip offset, into the common reachable volume.
  for _ in range(12):
   for side in ('R' if release else 'RL'):
    S,E,W=[m.translation for m in fr['mat'][side]];limit=(E-S).length+(W-E).length-.002
    offset=rotations[side]@C[side]+(fr['axis']*.15 if side=='L' else Vector())
    d=fr['center']-offset-S
    if d.length>limit:fr['center']-=d.normalized()*(d.length-limit)
  for s in 'RL':
   phi,psi=np.array(paths[s][lo])*(1-fraction)+np.array(paths[s][hi])*fraction;R=Quaternion(fr['axis'],math.radians(psi)).to_matrix()@fr['base'][s];center=fr['center']-(fr['axis']*.15 if s=='L' else Vector());T=center-R@C[s]
   _,pole,reach,U,_,_=armik.fitted(*fr['mat'][s],T,phi)
   armik.solve(rig,s,T,pole=pole,hand_rot=R);reaches.append(reach)
   if s=='L' and release:
    heldW=armik.W(rig,'B_L_Hand').translation.copy();heldE=armik.W(rig,'B_L_Forearm').translation.copy()
    heldQ=rig.pose.bones['B_L_Hand'].rotation_quaternion.copy()
    for n in ('UpperArm','Forearm','Hand'):rig.pose.bones['B_L_'+n].matrix_basis=Matrix()
    bpy.context.view_layer.update()
    shoulder=armik.W(rig,'B_L_UpperArm').translation.copy()
    D=armik.W(rig,'B_Spine2')@homeChestMatrix.inverted()
    out=(D.to_3x3()@Vector((1,0,0))).normalized()
    freeW=D@Vector((.58,.08,1.13))
    freeE=D@Vector((.4,.17,1.35))
    bow=out*(.24*math.sin(math.pi*min(1,release*1.7)))
    target=heldW.lerp(freeW,release)+bow
    _,pole,_,_,_,_=armik.fitted(*fr['mat']['L'],target,0)
    armik.solve(rig,'L',target,pole=pole)
    rig.pose.bones['B_L_Hand'].rotation_quaternion=heldQ.slerp(Quaternion(),smooth((release-.2)/.8))
    bpy.context.view_layer.update()
   for n,q in G[s]['finger_local'].items():
    rig.pose.bones[n].rotation_quaternion=Quaternion(q).slerp(Quaternion(),release if s=='L' else 0)
   bpy.context.view_layer.update()
   if s!='L' or release==0:gaps.append(((armik.W(rig,'B_'+s+'_Hand')@C[s])-center).length)
   sw=armik.wrist_cost(rig,s,armik.W(rig,'B_'+s+'_Hand').to_3x3().normalized())[0];swings.append(sw)
   if sw>55:print('WRIST_WARNING',act.name,f,s,round(sw,2),round(phi,2),round(psi,2),flush=True)
  poses.append((float(f),{n:rig.pose.bones[n].rotation_quaternion.copy() for n in rig.pose.bones.keys()}))
 bake_rotations(act,poses)
 if act.name=='Standing':
  setact(act);sc.frame_set(0)
  homeArms={side:[armik.W(rig,'B_'+side+'_'+part).copy() for part in ('UpperArm','Forearm','Hand')] for side in 'RL'}
  homeClavs={side:rig.pose.bones['B_'+side+'_Clavicle'].matrix_basis.copy() for side in 'RL'}
 report[act.name]={'max_grip_gap_m':max(gaps),'max_left_axis_correction_deg':0,'max_left_reach':max(reaches),'max_wrist_swing_deg':max(swings)}
 print('TWOHAND',act.name,report[act.name],flush=True)
setact(None)
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update()
# Blade edge follows the cut plane measured from the sourced attack.
act=bpy.data.actions['Attack'];setact(act);samples=[]
for f in range(int(act.frame_range[1])+1):
 sc.frame_set(f);h=armik.W(rig,'B_R_Hand');axis=(h.to_3x3()@A['R']).normalized();samples.append((h.copy(),h@C['R']+axis*1.2))
velocity=[(samples[i+1][1]-samples[i-1][1])*15 for i in range(1,len(samples)-1)]
idx=max(range(len(velocity)),key=lambda i:-velocity[i].y)+1
H=samples[idx][0];v=H.to_3x3().inverted()@velocity[idx-1];x=(v-A['R']*v.dot(A['R'])).normalized();z=x.cross(A['R']).normalized();x=A['R'].cross(z).normalized()
local=Matrix((x,A['R'],z)).transposed().to_4x4();local.translation=C['R']-A['R']*.075
setact(None)
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update();rest=rig.data.bones['B_R_Hand'].matrix_local@local
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.new('Socket_Sword');b.head=rest.translation;b.tail=b.head+rest.col[1].xyz*.12;b.align_roll(rest.col[2].xyz);b.parent=rig.data.edit_bones['B_R_Hand']
bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(p/'work/sword.blend'),link=False) as (source,target):target.objects=['SwordMesh']
sword=target.objects[0];bpy.context.collection.objects.link(sword);sword.data.transform(rest);sword.matrix_world=Matrix()
g=sword.vertex_groups.new(name='Socket_Sword');g.add(list(range(len(sword.data.vertices))),1,'REPLACE');sword.parent=rig;m=sword.modifiers.new('Armature','ARMATURE');m.object=rig
# Keep render evidence uncluttered by the provisional flat rigging material.
body=bpy.data.objects['Body'];body.data.materials.clear();m=bpy.data.materials.new('Clay');m.diffuse_color=(.54,.62,.64,1);body.data.materials.append(m)
json.dump({'clips':report,'blade_reference_frame':idx,'grip_separation_m':.15,'sword_local_matrix':[list(r) for r in local]},open(p/'work/two_hand_fit.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_grip.blend'))
assert all(r['max_grip_gap_m']<.005 for r in report.values()),'Off-hand reach failed'
