"""Choose elbow/hand roll over a clip while keeping the measured palm centre on the shaft."""
import math
import numpy as np
import bpy
from mathutils import Vector,Quaternion
import armik

def solve(rig,side,frames,axis,centre_local,anchor=None):
 PH=list(range(-135,136,10));PS=list(range(0,360,5));tables=[]
 ua,fa,hd=[f'B_{side}_{x}' for x in ('UpperArm','Forearm','Hand')]
 rest=(rig.data.bones[fa].matrix_local.to_3x3().inverted()@rig.data.bones[hd].matrix_local.to_3x3()).inverted()
 previous=None;transport=None
 for fr in frames:
  direction=Vector(fr['dir']).normalized();up=Vector((0,0,1))
  reference=(up-direction*up.dot(direction)).normalized()
  if previous is None:transport=reference.copy()
  else:transport=previous.rotation_difference(direction)@transport
  transport=(transport-direction*transport.dot(direction)).normalized()
  fr['roll_offset']=math.degrees(math.atan2(direction.dot(reference.cross(transport)),reference.dot(transport)))
  previous=direction
  for n,m in fr['snap'].items():rig.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update()
  Mu,Mf,Mh=[armik.W(rig,n).copy() for n in (ua,fa,hd)]
  S,E0,W0=[m.translation.copy() for m in (Mu,Mf,Mh)]
  a0=(E0-S).normalized();L1=(E0-S).length;L2=(W0-E0).length
  r=(W0-S).normalized();p0=(E0-S)-r*(E0-S).dot(r)
  torso=(armik.W(rig,'B_Spine2')@rig.data.bones['B_Spine2'].matrix_local.inverted()).inverted()
  C=np.empty((len(PH),len(PS)));metrics=np.empty((*C.shape,3))
  for j,psi in enumerate(PS):
   R=armik.hand_rot(axis,fr['dir'],psi+fr['roll_offset']);T=fr['centre']-R@centre_local
   d=T-S;dist=d.length;reach=max(0,dist-(L1+L2)*.995)
   dist=min(dist,(L1+L2)*.995);u=d.normalized();T=S+u*dist
   p=(r.rotation_difference(u)@p0) if p0.length>1e-6 else Vector((0,0,-1))
   p=(p-u*p.dot(u)).normalized()
   ca=max(-1,min(1,(L1*L1+dist*dist-L2*L2)/(2*L1*dist)))
   for i,phi in enumerate(PH):
    v=Quaternion(u,math.radians(phi))@p;E=S+L1*(u*ca+v*math.sqrt(max(0,1-ca*ca)))
    a1=(E-S).normalized();q=a0.rotation_difference(a1)
    n0=(E0-S).cross(W0-E0);n1=(E-S).cross(T-E)
    if n0.length>1e-6 and n1.length>1e-6:
     n0=q@n0;n0=(n0-a1*n0.dot(a1)).normalized();n1=(n1-a1*n1.dot(a1)).normalized()
     q=Quaternion(a1,math.atan2(a1.dot(n0.cross(n1)),n0.dot(n1)))@q
    carried=q@(W0-E0);qf=carried.normalized().rotation_difference((T-E).normalized())
    rf=qf.to_matrix()@q.to_matrix()@Mf.to_3x3().normalized()
    rel=rest@(rf.inverted()@R);sw,tw=armik.split_swing_twist(rel.to_quaternion(),Vector((0,1,0)))
    swing=math.degrees(min(sw.angle,2*math.pi-sw.angle));twist=math.degrees(tw)
    cost=swing+.045*swing*swing+.55*abs(twist-25)+.04*abs(phi)
    cost+=.9*max(0,swing-55)**2+.7*max(0,abs(twist)-85)**2+reach*100000
    # Clearance of the arm centreline from the posed torso, including the forearm radius.
    for point in (S.lerp(E,.65),E,E.lerp(T,.33),E.lerp(T,.67),T):
     local=torso@point
     if .92<local.z<1.49:
      radius_x=.21 if local.z>1.20 else .17
      clearance=(local.x/radius_x)**2+((local.y+.015)/.19)**2
      cost+=50000*max(0,1-clearance)**2
    C[i,j]=cost;metrics[i,j]=(swing,twist,reach)
  if anchor and (fr is frames[0] or fr is frames[-1]):
   C+=50*np.abs(np.array(PH)[:,None]-anchor['phi'])+50*np.abs((np.array(PS)[None,:]+fr['roll_offset']-anchor['psi']+180)%360-180)
  tables.append((C,metrics))
 dphi=np.abs(np.subtract.outer(np.array(PH,float),np.array(PH,float)))*.5
 dpsi=np.abs((np.subtract.outer(np.array(PS,float),np.array(PS,float))+180)%360-180)*.7
 acc=tables[0][0].copy();back=[]
 for C,_ in tables[1:]:
  a=acc[None,:,:]+dphi[:,:,None];m1=np.min(a,axis=1);a1=np.argmin(a,axis=1)
  b=m1[:,None,:]+dpsi[None,:,:];m2=np.min(b,axis=2);a2=np.argmin(b,axis=2)
  back.append((a1,a2));acc=m2+C
 i,j=np.unravel_index(int(np.argmin(acc)),acc.shape);path=[(i,j)]
 for a1,a2 in reversed(back):
  jp=a2[i,j];ip=a1[i,jp];i,j=ip,jp;path.append((i,j))
 path.reverse()
 ph=np.array([PH[i] for i,j in path],float);ps=np.unwrap(np.radians([PS[j] for i,j in path]))*180/math.pi
 # Smooth quantized roll only; the exact shaft path and impact timing remain intact.
 kernel=np.array([1,4,6,4,1],float)/16
 for a in (ph,ps):
  filtered=np.convolve(np.pad(a,(2,2),mode='edge'),kernel,'valid');a[1:-1]=filtered[1:-1]
 out=[{'phi':float(p),'psi':float(s+fr['roll_offset'])} for p,s,fr in zip(ph,ps,frames)]
 assert np.isfinite(ph).all() and np.isfinite(ps).all()
 return out
