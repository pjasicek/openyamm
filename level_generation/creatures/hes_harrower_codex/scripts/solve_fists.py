"""Solve native Demon fingers around a palm-centred handle, using the playbook's spread/curl model."""
from pathlib import Path
import json,numpy as np
from scipy.optimize import differential_evolution,minimize
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parents[1];DATA=json.loads((P/'work/hand_rest_r2.json').read_text())
RADIUS=.026
unit=lambda v:np.asarray(v)/np.linalg.norm(v)
def rot(axis,angle):return Rotation.from_rotvec(np.asarray(axis)*angle).as_matrix()
for side,d in DATA.items():
 old=json.loads((P/f'work/review_v1/grip_pose_{side}.json').read_text());B=d['bones'];A=unit(old['handle_axis_hand_local'])
 chains={i:[f'B_{side}_Finger{i}',f'B_{side}_Finger{i}1',f'B_{side}_Finger{i}2'] for i in range(5)}
 if side=='R':chains[0]=['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']
 knuckles=np.array([B[c[0]]['head'] for i,c in chains.items() if i]);kn=knuckles.mean(0)
 A=np.linalg.svd(knuckles-kn)[2][0]
 if A@np.array(old['handle_axis_hand_local'])<0:A=-A
 F=unit(kn);N=unit(np.cross(A,F));tips=np.mean([B[c[-1]]['tail'] for i,c in chains.items() if i],axis=0)
 if (tips-kn)@N<0:N=-N
 C=kn-.010*F+.060*N
 points=np.array([v['co'] for v in d['vertices']]);W=[v['weights'] for v in d['vertices']]
 FL={};report={};Ms={}
 for finger,ch in chains.items():
  js=np.array([B[n]['head'] for n in ch]+[B[ch[-1]]['tail']]);belongs=np.array([sum(w.get(n,0) for n in ch)>.5 for w in W]);skin=points[belongs]
  dist=[]
  for a,b in zip(js[:-1],js[1:]):
   t=np.clip((skin-a)@(b-a)/np.dot(b-a,b-a),0,1);dist.append(np.linalg.norm(skin-a-t[:,None]*(b-a),axis=1))
  half=float(np.median(np.min(dist,axis=0)));want=RADIUS+half+.002
  axis=A.copy()
  if (rot(axis,.3)@(js[1]-js[0]))@N < (js[1]-js[0])@N:axis=-axis
  rest=[np.array(B[n]['matrix']) for n in ch]
  ownW=np.array([[W[j].get(n,0) for n in ch] for j in np.flatnonzero(belongs)]);unmoved=skin*(1-ownW.sum(1))[:,None]
  local_skin=[np.c_[skin,np.ones(len(skin))]@np.linalg.inv(m).T for m in rest]
  def pose(x):
   # Close the splay first, then curl each phalanx around the fixed handle axis.
   spread_axis=F if finger==0 else N
   baseR=rot(spread_axis,x[0]);p=js[0]+(js-js[0])@baseR.T;Rs=[baseR.copy() for _ in ch]
   flex_axis=axis if finger else unit(np.cross(baseR@(js[1]-js[0]),N))
   for k,angle in enumerate(x[1:]):
    rr=rot(flex_axis,angle)
    p[k+1:]=p[k]+(p[k+1:]-p[k])@rr.T
    for j in range(k,3):Rs[j]=rr@Rs[j]
   matrices=[]
   for k in range(3):
    m=np.eye(4);m[:3,:3]=Rs[k]@rest[k][:3,:3];m[:3,3]=p[k];matrices.append(m)
   return p,matrices
  def cost(x):
   p,matrices=pose(x);samples=np.concatenate([a+(b-a)*np.array([.2,.5,.8,1.])[:,None] for a,b in zip(p[:-1],p[1:])])
   q=samples-C;rad=np.linalg.norm(q-np.outer(q@A,A),axis=1)
   posed_skin=unmoved.copy()
   for k,m in enumerate(matrices):posed_skin+=ownW[:,k,None]*(local_skin[k]@m.T)[:,:3]
   delta=posed_skin-C;along=delta@A;skinrad=np.linalg.norm(delta-np.outer(along,A),axis=1);near=skinrad[np.abs(along)<.09]
   if len(near)<5:return 100.
   score=.025*np.mean((rad-want)**2)
   score+=500*np.mean(np.maximum(RADIUS-.0005-near,0)**2)
   score+=12*(np.percentile(near,5)-(RADIUS+.0015))**2+3*(np.percentile(near,15)-(RADIUS+.006))**2
   if finger:
    score+=3*max(0,(p[-1]-C)@F-.020)**2
    score+=.1*np.mean(((p[1:]-p[0])@A)**2)
    score+=.002*max(0,x[3]-x[2])**2
    score+=.05*max(0,sum(x[1:])-np.radians(160))**2
   else:
    score+=2*max(0,abs((p[-1]-C)@A)-.065)**2
    score+=2*max(0,(p[-1]-C)@F-.02)**2
   return score
  bounds=np.radians([(-65,65),(0,125),(0,130),(0,100)] if finger else [(-140,140),(-85,100),(-45,110),(0,100)])
  result=differential_evolution(cost,bounds,seed=11+finger,popsize=12,maxiter=130,tol=1e-7,polish=True)
  posed,matrices=pose(result.x)
  for i,n in enumerate(ch):
   parent=matrices[i-1] if i else np.eye(4);parent_rest=rest[i-1] if i else np.eye(4)
   local_rest=np.linalg.inv(parent_rest)@rest[i];local_pose=np.linalg.inv(parent)@matrices[i]
   q=Rotation.from_matrix((np.linalg.inv(local_rest)@local_pose)[:3,:3]).as_quat();FL[n]=[float(q[3]),*q[:3].tolist()];Ms[n]=matrices[i].tolist()
  report[str(finger)]={'angles_degrees':np.degrees(result.x).tolist(),'half_thickness_m':half,'cost':float(result.fun),'joints':posed.tolist()}
 old.update(finger_local=FL,handle_centre_hand_local=C.tolist(),handle_axis_hand_local=A.tolist(),radius=RADIUS,solve='native-mesh spread/curl with fingertip closure constraint',finger_solution=report)
 (P/f'work/grip_pose_r2_{side}.json').write_text(json.dumps(old,indent=2)+'\n')
 print(side,'centre',np.round(C,4),'radius',RADIUS,'angles',{k:np.round(v['angles_degrees'],1).tolist() for k,v in report.items()},flush=True)
