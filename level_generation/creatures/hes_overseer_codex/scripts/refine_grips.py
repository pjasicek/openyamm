"""Coupled skin solve: shared web vertices move with all fingers together, not one digit at a time."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
P=Path(__file__).resolve().parents[1];fit=json.loads((P/'work/finger_fit.json').read_text());a=np.load(P/'work/finger_skin.npz')
co=a['positions'];W=a['weights'];names=a['bone_names'].tolist();edges=a['edges'];result={}
for sd,sg,radius in [('L',1,.025),('R',-1,.027)]:
 chains=[fit['hands'][sd][str(d)]['bones'] for d in range(6)];indices=[names.index(n) for ch in chains for n in ch]
 rest=np.array([fit['rest'][n] for ch in chains for n in ch]);weight=W[:,indices];mask=weight.sum(1)>1e-5
 ids=np.flatnonzero(mask);lookup={int(v):i for i,v in enumerate(ids)};xyz=co[ids];ww=weight[ids];fixed=xyz*(1-ww.sum(1))[:,None];hom=np.c_[xyz,np.ones(len(xyz))]
 ee=np.array([(lookup[int(x)],lookup[int(y)]) for x,y in edges if int(x) in lookup and int(y) in lookup]);lens=np.linalg.norm(xyz[ee[:,1]]-xyz[ee[:,0]],axis=1);ee=ee[lens>1e-5];lens=lens[lens>1e-5]
 digitweight=ww.reshape(len(ids),6,3).sum(2);regions=[digitweight[:,d]>.35 for d in range(6)];assert all(m.any() for m in regions)
 def evaluate(params):
  angles=params[:18].reshape(6,3);center=np.array([sg*params[18],-.238,params[19]]);pos=fixed.copy();trans=[]
  for d in range(6):
   parent=np.eye(4)
   for j in range(3):
    idx=d*3+j;pivot=(parent@rest[idx])[:3,3];R=Rotation.from_rotvec([0,sg*angles[d,j],0]).as_matrix();turn=np.eye(4);turn[:3,:3]=R;turn[:3,3]=pivot-R@pivot;parent=turn@parent
    pos+=(parent@hom.T).T[:,:3]*ww[:,idx,None];trans.append(parent)
  return pos,center,trans
 def gaps(points,center):
  v=points-center;rad=np.linalg.norm(v[:,[0,2]],axis=1)-radius
  # The actual grip extends 11 cm each side; points past its caps are not inside the handle.
  return np.maximum(rad,np.abs(v[:,1])-.11)
 def residual(params):
  pos,c,_=evaluate(params);gap=gaps(pos,c);midgap=gaps((pos[ee[:,0]]+pos[ee[:,1]])*.5,c)
  contact=np.array([np.min(np.abs(gap[m])) for m in regions]);stretch=np.linalg.norm(pos[ee[:,1]]-pos[ee[:,0]],axis=1)/lens
  return np.r_[np.minimum(gap+.0005,0)*20,np.minimum(midgap+.0005,0)*20,contact*6,np.maximum(stretch-3.4,0)*.02,params[:18]*.0001]
 bounds=(np.r_[np.full(18,-1.35),.275,.53],np.r_[np.full(18,1.7),.325,.59])
 seeds=[np.r_[np.radians([0,20,0]+[20,35,5]*5),.302,.565],np.r_[np.radians([0,0,0]+[10,15,0]*5),.29,.56]]
 best=None
 for seed in seeds:
  sol=least_squares(residual,seed,bounds=bounds,max_nfev=600,ftol=1e-9,xtol=1e-9,gtol=1e-9)
  if best is None or np.sum(sol.fun**2)<np.sum(best.fun**2):best=sol
 pos,c,trans=evaluate(best.x);gap=gaps(pos,c);midgap=gaps((pos[ee[:,0]]+pos[ee[:,1]])*.5,c);stretch=np.linalg.norm(pos[ee[:,1]]-pos[ee[:,0]],axis=1)/lens
 local={}
 for d,ch in enumerate(chains):
  for j,n in enumerate(ch):
   idx=d*3+j;target=trans[idx]@rest[idx];basis=np.linalg.inv(rest[idx])@target if j==0 else np.linalg.inv(rest[idx])@rest[idx-1]@np.linalg.inv(trans[idx-1]@rest[idx-1])@target
   q=Rotation.from_matrix(basis[:3,:3]).as_quat();local[n]=[float(q[3]),*map(float,q[:3])]
 r={'center_bind':c.tolist(),'axis_bind':[0,1,0],'radius_m':radius,'finger_local':local,'angles_degrees':np.degrees(best.x[:18]).reshape(6,3).tolist(),'min_gap_mm':float(min(gap.min(),midgap.min())*1000),'digit_contact_mm':[float(np.min(np.abs(gap[m]))*1000) for m in regions],'edge_stretch_max':float(stretch.max()),'edge_stretch_p99':float(np.percentile(stretch,99)),'cost':float(np.sum(best.fun**2))}
 r['candidate_pass']=r['min_gap_mm']>=-3 and max(r['digit_contact_mm'])<=3 and r['edge_stretch_max']<=4.5
 result[sd]=r;print(sd,json.dumps({k:v for k,v in r.items() if k!='finger_local'}),flush=True)
(P/'work/grip_pose.json').write_text(json.dumps(result,indent=2)+'\n')
assert all(np.isfinite(r['cost']) for r in result.values())
