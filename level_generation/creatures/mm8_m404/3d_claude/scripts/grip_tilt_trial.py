"""Fit continuous elbow planes and hand roll to the shared sword grip."""
import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_stance.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene
G={s:json.load(open(p/('work/grip_pose_'+s+'.json'))) for s in 'RL'}
C={s:Vector(G[s]['handle_centre_hand_local']) for s in G};A={s:Vector(G[s]['handle_axis_hand_local']).normalized() for s in G}
SOURCE_A=A['R'].copy()
for side in 'RL':
 h=rig.data.bones['B_'+side+'_Hand'];f=rig.data.bones['B_'+side+'_Finger2'].head_local-h.head_local
 f=h.matrix_local.to_3x3().inverted()@f;f=(f-A[side]*f.dot(A[side])).normalized()
 A[side]=(A[side]*math.cos(math.radians(20))+f*math.sin(math.radians(20))).normalized()
def setact(act):
 rig.animation_data_create();rig.animation_data.action=act
 if act is not None and len(act.slots):rig.animation_data.action_slot=act.slots[0]
def restore(snap):
 for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def smooth(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def fitted(Mu,Mf,Mh,T,phi):
 S,E0,W0=Mu.translation,Mf.translation,Mh.translation
 l1,l2=(E0-S).length,(W0-E0).length;d=T-S;dist=d.length;reach=dist/(l1+l2)
 if reach>.999:T=S+d.normalized()*(l1+l2)*.999;d=T-S;dist=d.length
 u=d.normalized();r=(W0-S).normalized();v=E0-S-r*(E0-S).dot(r)
 v=r.rotation_difference(u)@v;v=(v-u*v.dot(u)).normalized();v=Quaternion(u,math.radians(phi))@v
 ca=max(-1,min(1,(l1*l1+dist*dist-l2*l2)/(2*l1*dist)))
 E=S+l1*(u*ca+v*math.sqrt(max(0,1-ca*ca)))
 a0,a1=(E0-S).normalized(),(E-S).normalized();q=a0.rotation_difference(a1)
 n0=q@((E0-S).cross(W0-E0));n1=(E-S).cross(T-E)
 if n0.length>1e-6 and n1.length>1e-6:
  n0=(n0-a1*n0.dot(a1)).normalized();n1=(n1-a1*n1.dot(a1)).normalized()
  q=Quaternion(a1,math.atan2(a1.dot(n0.cross(n1)),n0.dot(n1)))@q
 R=q.to_matrix()@Mf.to_3x3().normalized();f0=q@((W0-E0).normalized())
 R=f0.rotation_difference((T-E).normalized()).to_matrix()@R
 return R,S+v,reach,q.to_matrix()@Mu.to_3x3().normalized(),E,T
skin=np.load(p/'work/surface_cost.npz');skin_names=list(skin['names']);cost_data={}
for side in 'RL':
 names=['B_'+side+'_'+n for n in ('UpperArm','Forearm','Hand')]
 w=skin['weights'];arm=w[:,[skin_names.index(n) for n in names]].sum(1)
 edges=skin['edges'];keep=(skin['piece']==0)&(arm>.15)&(skin['co'][:,2]>1.12)
 edges=edges[keep[edges].all(1)];ids,edge=np.unique(edges,return_inverse=True);edge=edge.reshape(-1,2)
 co=skin['co'][ids];length=np.linalg.norm(co[edge[:,0]]-co[edge[:,1]],axis=1)
 parts={n:(np.c_[co,np.ones(len(co))]@np.array(rig.data.bones[n].matrix_local.inverted()).T)*w[ids,skin_names.index(n),None] for n in skin_names if n in rig.data.bones and w[ids,skin_names.index(n)].max()>1e-6}
 cost_data[side]=(parts,edge,length)
PH=np.arange(-180,180,10);PS=np.arange(0,360,10)
dp=np.abs((PH[:,None]-PH[None,:]+180)%360-180)*1.0;ds=np.abs((PS[:,None]-PS[None,:]+180)%360-180)*1.0
dp[dp>30]=1e8;ds[ds>30]=1e8
def fit_side(side,frames):
 names=['B_'+side+'_'+s for s in ('UpperArm','Forearm','Hand')]
 rel=(rig.data.bones[names[1]].matrix_local.to_3x3().inverted()@rig.data.bones[names[2]].matrix_local.to_3x3()).inverted()
 tables=[]
 for fr in frames:
  Mu,Mf,Mh=fr['mat'][side];center=fr['center']-(fr['axis']*.15 if side=='L' else Vector())
  ur=rig.data.bones[names[0]].matrix_local.to_3x3();cr=rig.data.bones['B_'+side+'_Clavicle'].matrix_local.to_3x3()
  neutral=fr['clavicle'][side]@cr.inverted()@ur
  uaxis=(ur.inverted()@(rig.data.bones[names[1]].head_local-rig.data.bones[names[0]].head_local)).normalized()
  parts,edge,length=cost_data[side]
  const=sum((v@fr['world'][n].T)[:,:3] for n,v in parts.items() if n not in names)
  table=np.empty((len(PH),len(PS)))
  for j,psi in enumerate(PS):
   R=Quaternion(fr['axis'],math.radians(psi)).to_matrix()@fr['base'][side];T=center-R@C[side]
   for i,phi in enumerate(PH):
    F,_,reach,U,E,actualT=fitted(Mu,Mf,Mh,T,phi);q=(rel@F.inverted()@R).to_quaternion()
    sw,tw=armik.split_swing_twist(q,Vector((0,1,0)));sw=math.degrees(min(sw.angle,2*math.pi-sw.angle));tw=abs(math.degrees(tw))
    _,ut=armik.split_swing_twist((neutral.inverted()@U).to_quaternion(),uaxis);ut=abs(math.degrees(ut))
    posed=const.copy()
    for n,rot,loc in zip(names,(U,F,R),(Mu.translation,E,actualT)):
     if n not in parts:continue
     M=rot.to_4x4();M.translation=loc;posed+=(parts[n]@np.array(M).T)[:,:3]
    stretch=np.linalg.norm(posed[edge[:,0]]-posed[edge[:,1]],axis=1)/np.maximum(length,1e-6)
    p99=float(np.quantile(stretch,.99));skin_cost=1500*max(0,p99-1.90)**2+30*p99
    table[i,j]=skin_cost+3*max(0,ut-95)**2+.25*ut+sw+.03*sw*sw+.4*tw+.13*abs(phi)+8*max(0,sw-52)**2+3*max(0,tw-105)**2+1e6*max(0,reach-.995)**2
  tables.append(table)
 acc=tables[0].copy();back=[]
 for table in tables[1:]:
  a=acc[None,:,:]+dp[:,:,None];a1=a.argmin(1);m=a.min(1)
  b=m[:,None,:]+ds[None,:,:];a2=b.argmin(2);acc=b.min(2)+table;back.append((a1,a2))
 i,j=np.unravel_index(acc.argmin(),acc.shape);path=[(i,j)]
 for a1,a2 in reversed(back):j0=a2[i,j];i,j=a1[i,j0],j0;path.append((i,j))
 path.reverse();phi=np.degrees(np.unwrap(np.radians([PH[i] for i,j in path])));psi=np.unwrap(np.radians([PS[j] for i,j in path]))
 # Smooth only the fit controls; the sourced body and blade trajectory retain their keyed timing.
 kernel=np.array([1,4,1],float)/6
 phi=np.convolve(np.pad(phi,1,mode='edge'),kernel,'valid');psi=np.degrees(np.convolve(np.pad(psi,1,mode='edge'),kernel,'valid'))
 return list(zip(phi,psi))
setact(bpy.data.actions['Standing']);sc.frame_set(0)
homeChest=armik.W(rig,'B_Spine2').translation.copy()
homeWrist=armik.W(rig,'B_R_Hand').translation.copy()
guardAxis=Vector((.62,-.20,.76)).normalized();guardCenter=Vector((-.055,-.38,1.20))
report={}
for act in [bpy.data.actions[n] for n in ('Attack','Death')]:
 frames=[]
 for f in range(int(act.frame_range[1])+1):
  setact(act);sc.frame_set(f);snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};setact(None);restore(snap)
  mats={s:[armik.W(rig,'B_'+s+'_'+n).copy() for n in ('UpperArm','Forearm','Hand')] for s in 'RL'}
  RH=mats['R'][2];axis=(RH.to_3x3()@SOURCE_A).normalized();center=RH@C['R']
  if act.name in ('Standing','Fidget'):
   axis=guardAxis.copy();center=guardCenter+Vector((0,0,.003*math.sin(f*.12)))
  elif act.name=='Walking':
   chest=armik.W(rig,'B_Spine2').translation
   center=guardCenter+(chest-homeChest)+(RH.translation-homeWrist-(chest-homeChest))*.3
   axis=guardAxis.copy()
  elif act.name in ('Attack','Hit','Death'):
   end=int(act.frame_range[1]);enter=3 if act.name=='Hit' else 6;leave=5 if act.name=='Hit' else 6
   blend=smooth(f/enter)
   if act.name!='Death':blend=min(blend,smooth((end-f)/leave))
   axis=guardAxis.slerp(axis,blend).normalized();center=guardCenter.lerp(center,blend)
  if act.name=='Death':
   t=smooth((f-12)/12)
   feet=(armik.W(rig,'B_L_Foot').translation+armik.W(rig,'B_R_Foot').translation)*.5
   along=feet-armik.W(rig,'B_Head').translation;along.z=0;along.normalize()
   shoulder=mats['R'][0].translation;out=shoulder-armik.W(rig,'B_Spine2').translation;out.z=0;out.normalize();held=shoulder+out*.38+along*.10;held.z=shoulder.z+.04
   axis=axis.slerp(along,t).normalized();center=center.lerp(held,t)
  if act.name=='Attack':
   center.y+=.06*math.exp(-((f-15)/3)**2)
  # Centre the shared grip in the overlap of both arms' reachable volumes.
  if act.name!='Death' or f<20:
   for _ in range(6):
    for s in 'RL':
     S,E,W=[m.translation for m in mats[s]];reach=(E-S).length+(W-E).length
     g=center-(axis*.15 if s=='L' else Vector());d=g-S;limit=reach-.045
     if d.length>limit:center-=d.normalized()*(d.length-limit)
  # Use the fitted rest arm carried by its clavicle as a continuous IK reference.
  refs={}
  for side in 'RL':
   n='B_'+side+'_Clavicle';D=armik.W(rig,n)@rig.data.bones[n].matrix_local.inverted()
   refs[side]=[D@rig.data.bones['B_'+side+'_'+part].matrix_local for part in ('UpperArm','Forearm','Hand')]
  mats=refs
  frames.append({'world':{n:np.array(armik.W(rig,n)) for n in rig.pose.bones.keys()},'clavicle':{s:armik.W(rig,'B_'+s+'_Clavicle').to_3x3().normalized() for s in 'RL'},'snap':snap,'mat':mats,'center':center,'axis':axis})
 # Parallel transport avoids a hand-roll discontinuity when the sword crosses vertical.
 bases={s:armik.hand_rot(A[s],frames[0]['axis'],0) for s in 'RL'};last=frames[0]['axis']
 for fr in frames:
  q=last.rotation_difference(fr['axis']).to_matrix();bases={s:q@R for s,R in bases.items()}
  fr['base']={s:R.copy() for s,R in bases.items()};last=fr['axis']
 paths={s:fit_side(s,frames) for s in 'RL'};poses=[];gaps=[];swings=[];reaches=[]
 for f,fr in enumerate(frames):
  restore(fr['snap'])
  for side in 'RL':
   for part in ('UpperArm','Forearm','Hand'):rig.pose.bones['B_'+side+'_'+part].matrix_basis=Matrix()
  bpy.context.view_layer.update()
  release=smooth((f-12)/9) if act.name=='Death' else 0
  for s in 'RL':
   phi,psi=paths[s][f];R=Quaternion(fr['axis'],math.radians(psi)).to_matrix()@fr['base'][s];center=fr['center']-(fr['axis']*.15 if s=='L' else Vector());T=center-R@C[s]
   _,pole,reach,U,_,_=fitted(*fr['mat'][s],T,phi)
   armik.solve(rig,s,T,pole=pole,hand_rot=R);reaches.append(reach)
   if s=='L' and release:
    for n in ('UpperArm','Forearm','Hand'):
     pb=rig.pose.bones['B_L_'+n];target=Quaternion() if n=='Hand' else fr['snap'][pb.name].to_quaternion()
     pb.rotation_quaternion=pb.rotation_quaternion.slerp(target,release)
    bpy.context.view_layer.update()
   for n,q in G[s]['finger_local'].items():
    rig.pose.bones[n].rotation_quaternion=Quaternion(q).slerp(fr['snap'][n].to_quaternion(),release if s=='L' else 0)
   bpy.context.view_layer.update()
   if s!='L' or release==0:gaps.append(((armik.W(rig,'B_'+s+'_Hand')@C[s])-center).length)
   sw=armik.wrist_cost(rig,s,armik.W(rig,'B_'+s+'_Hand').to_3x3().normalized())[0];swings.append(sw)
   if sw>55:print('WRIST_WARNING',act.name,f,s,round(sw,2),round(phi,2),round(psi,2),flush=True)
  poses.append({n:rig.pose.bones[n].rotation_quaternion.copy() for n in rig.pose.bones.keys()})
 setact(act);previous={}
 for f,pose in enumerate(poses):
  for n,q in pose.items():
   if n in previous and q.dot(previous[n])<0:q=-q
   previous[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 report[act.name]={'max_grip_gap_m':max(gaps),'max_left_axis_correction_deg':0,'max_left_reach':max(reaches),'max_wrist_swing_deg':max(swings)}
 print('TWOHAND',act.name,report[act.name],flush=True)

json.dump(report,open(p/'work/grip_tilt_trial.json','w'),indent=2)
