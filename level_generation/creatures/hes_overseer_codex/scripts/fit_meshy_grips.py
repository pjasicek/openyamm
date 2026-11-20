"""Coupled skin solve: shared web vertices move with all fingers together, not one digit at a time."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.interpolate import RegularGridInterpolator
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree,ConvexHull
P=Path(__file__).resolve().parents[1];OUTPUT=P/'work';fit=json.loads((P/'work/finger_fit.json').read_text());a=np.load(P/'work/finger_skin.npz')
co=a['positions'];W=a['weights'];names=a['bone_names'].tolist();edges=a['edges'];result={}
def surface(vertices,faces,closed=True):
 tri=vertices[faces];centres=tri.mean(1);tree=cKDTree(centres)
 normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
 def query(points):
  _,index=tree.query(points,k=min(16,len(tri)));t=tri[index];q=points[:,None,:];a,b,c=t[:,:,0],t[:,:,1],t[:,:,2];ab=b-a;ac=c-a;ap=q-a
  aa=np.sum(ab*ab,2);bb=np.sum(ab*ac,2);cc=np.sum(ac*ac,2);d=np.sum(ap*ab,2);e=np.sum(ap*ac,2);det=aa*cc-bb*bb
  v=(cc*d-bb*e)/np.maximum(det,1e-15);w=(aa*e-bb*d)/np.maximum(det,1e-15);inside=(v>=0)&(w>=0)&(v+w<=1)
  proj=a+ab*v[:,:,None]+ac*w[:,:,None];candidates=[np.where(inside[:,:,None],proj,a)]
  for x,y in [(a,b),(b,c),(c,a)]:
   edge=y-x;u=np.clip(np.sum((q-x)*edge,2)/np.maximum(np.sum(edge*edge,2),1e-15),0,1);candidates.append(x+edge*u[:,:,None])
  cand=np.stack(candidates,2);delta=q[:,:,None,:]-cand;dist2=np.sum(delta*delta,3);best=dist2.reshape(len(points),-1).argmin(1);ti=best//4;ci=best%4
  delta=delta[np.arange(len(points)),ti,ci];dist=np.sqrt(dist2[np.arange(len(points)),ti,ci])
  return dist

 return query
for sd,sg,radius in [('L',1,.025),('R',-1,.032)]:
 part='pulse_pistol' if sd=='L' else 'collar_rod';prop=np.load(P/'work/weapons'/f'{part}_grip_mesh.npz');grip_surface=surface(prop['vertices'],prop['faces'][prop['grip']],False)
 hullverts=prop['vertices'][np.unique(prop['faces'][prop['grip']])]
 if sd=='R':
  # The round fitted handle spans ±17 cm; sparse grip-face vertices must not shorten its collision hull.
  angle=np.linspace(0,2*np.pi,65)[:-1];hullverts=np.array([[.032*np.cos(t),.032*np.sin(t),z] for z in [-.17,.17] for t in angle])
 full_surface=None
 if sd=='L':
  sdf=np.load(P/'work/weapons/pulse_pistol_sdf.npz');full_surface=RegularGridInterpolator(tuple(sdf[k] for k in ['x','y','z']),sdf['distance'],bounds_error=False,fill_value=.05)
 hull=ConvexHull(hullverts);planes=hull.equations
 base_rotation=Rotation.from_euler('x',90,degrees=True).as_matrix()

 chains=[fit['hands'][sd][str(d)]['bones'] for d in range(6)];indices=[names.index(n) for ch in chains for n in ch]
 rest=np.array([fit['rest'][n] for ch in chains for n in ch]);weight=W[:,indices];handweight=a['hand_weights'][:,0 if sd=='L' else 1];mask=weight.sum(1)+handweight>.3
 ids=np.flatnonzero(mask);lookup={int(v):i for i,v in enumerate(ids)};xyz=co[ids];ww=weight[ids]
 # Identical UV seam copies contribute once to fitting, with the same exported skin weights.
 _,take,back=np.unique(np.round(np.c_[xyz,ww],7),axis=0,return_index=True,return_inverse=True);lookup={int(v):int(back[i]) for i,v in enumerate(ids)};ids=ids[take];xyz=co[ids];ww=weight[ids];fixed=xyz*(1-ww.sum(1))[:,None];hom=np.c_[xyz,np.ones(len(xyz))]

 ee=np.array([(lookup[int(x)],lookup[int(y)]) for x,y in edges if int(x) in lookup and int(y) in lookup]);lens=np.linalg.norm(xyz[ee[:,1]]-xyz[ee[:,0]],axis=1);ee=ee[lens>1e-5];lens=lens[lens>1e-5]
 triangles=np.array([[lookup[int(v)] for v in f] for f in a['faces'] if all(int(v) in lookup for v in f)]);bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3]);assert len(triangles)>0
 digitweight=ww.reshape(len(ids),6,3).sum(2);sampleweight=np.einsum('sk,tkj->tsj',bary,np.c_[digitweight,handweight[ids]][triangles]).reshape(-1,7)
 samplekey=np.einsum('sk,tkj->tsj',bary,np.c_[xyz,ww,handweight[ids]][triangles]).reshape(-1,22)
 _,sample_take=np.unique(np.round(samplekey,7),axis=0,return_index=True);sampleweight=sampleweight[sample_take];regions=[sampleweight[:,d]>.3 for d in range(7)];assert all(m.any() for m in regions)
 print('SAMPLES',sd,len(sample_take),flush=True)

 extra_surface=None
 if sd=='R':
  other=np.load(P/'work/weapons/arc_maul_grip_mesh.npz');extra_surface=surface(other['vertices'],other['faces'][other['grip']],False)
 def samples(pos):return np.einsum('sk,tkj->tsj',bary,pos[triangles]).reshape(-1,3)[sample_take]
 def evaluate(params):
  angles=params[:18].reshape(6,3);center=np.array([sg*params[18],params[20],params[19]]);pos=fixed.copy();trans=[]
  for d in range(6):
   parent=np.eye(4)
   for j in range(3):
    idx=d*3+j;pivot=(parent@rest[idx])[:3,3];R=Rotation.from_rotvec([params[24+d] if j==0 else 0,sg*angles[d,j],params[30+d] if j==0 else 0]).as_matrix();turn=np.eye(4);turn[:3,:3]=R;turn[:3,3]=pivot-R@pivot;parent=turn@parent
    pos+=(parent@hom.T).T[:,:3]*ww[:,idx,None];trans.append(parent)
  return pos,center,trans
 def gaps(points,center,params,grip=False):
  rotation=Rotation.from_rotvec(params[21:24]).as_matrix()@base_rotation
  local=(points-center)@rotation
  return grip_surface(local) if grip else (local@planes[:,:3].T+planes[:,3]).max(1)
 def residual(params):
  pos,c,trans=evaluate(params);gap=gaps(pos,c,params);midgap=gaps((pos[ee[:,0]]+pos[ee[:,1]])*.5,c,params)
  sp=samples(pos);facegap=gaps(sp,c,params);gripgap=gaps(sp,c,params,True);contact=np.array([np.min(np.abs(gripgap[m])) for m in regions]);stretch=np.linalg.norm(pos[ee[:,1]]-pos[ee[:,0]],axis=1)/lens
  extra=[]
  if extra_surface is not None:
   rotation=Rotation.from_rotvec(params[21:24]).as_matrix()@base_rotation;eg=extra_surface((sp-c)@rotation);extra=[np.min(eg[m]) for m in regions]
  full=[];index_target=[]
  if full_surface is not None:
   rotation=Rotation.from_rotvec(params[21:24]).as_matrix()@base_rotation;full=np.minimum(full_surface((sp-c)@rotation)-.0005,0)*120
   tip=(trans[5]@np.r_[fit['hands'][sd]['1']['points'][-1],1])[:3];index_target=((tip-c)@rotation-np.array([-.025,-.07,.07]))*8
  return np.r_[full,index_target,np.minimum(facegap-.0005,0)*65,np.maximum(np.array(extra)-.001,0)*35,np.minimum(gap-.0005,0)*65,np.minimum(midgap-.0005,0)*65,np.maximum(contact-(.0015 if sd=='L' else .001),0)*(100 if sd=='L' else 35),np.maximum(stretch-(1.8 if sd=='L' else 2.8),0)*(.3 if sd=='L' else .2),params[:18]*(.08 if sd=='L' else .001),params[24:]*(.08 if sd=='L' else .001)]
 bounds=(np.r_[np.full(18,-1.2),.255,.46,-.29,[-.5]*3,[-.35]*12],np.r_[np.full(18,1.7),.35,.615,-.16,[.5]*3,[.35]*12])
 seeds=[np.load(OUTPUT/f'grip_solution_{sd}.npy')]
 if sd=='L':
  # Seat the trigger over the index claw; preserve the native curved fingers instead of chasing contact with large bends.
  bounds[0][:18]=-1.0;bounds[1][:18]=1.0
  bounds[0][18:21]=[.25,.49,-.23];bounds[1][18:21]=[.33,.56,-.18]
  bounds[0][24:]=-.8;bounds[1][24:]=.8
  reference=np.array([0.03468008173379402, -0.5211158116325947, -0.1426078337014659]);bounds[0][21:24]=reference-.15;bounds[1][21:24]=reference+.15
 if sd=='R':
  mirror=np.load(OUTPUT/'grip_solution_L.npy').copy();mirror[18:24]=[.30,.52,-.238,0,0,0];mirror[30:]*=-1
  seeds=[np.load(OUTPUT/f'grip_solution_{sd}.npy'),mirror,np.r_[np.radians([0,0,0]+[10,15,0]*5),.30,.52,-.238,[0]*15]]

 best=None
 for seed in seeds:
  sol=least_squares(residual,seed,bounds=bounds,max_nfev=160,diff_step=1e-4 if sd=='L' else None,verbose=2,ftol=1e-6,xtol=1e-7,gtol=1e-3)
  print('SEED',sd,sol.cost,flush=True)
  if best is None or np.sum(sol.fun**2)<np.sum(best.fun**2):best=sol
  if sol.cost<1e-3:break
 np.save(OUTPUT/f'grip_solution_{sd}.npy',best.x)
 pos,c,trans=evaluate(best.x);gap=gaps(pos,c,best.x);midgap=gaps((pos[ee[:,0]]+pos[ee[:,1]])*.5,c,best.x);stretch=np.linalg.norm(pos[ee[:,1]]-pos[ee[:,0]],axis=1)/lens
 local={}
 for d,ch in enumerate(chains):
  for j,n in enumerate(ch):
   idx=d*3+j;target=trans[idx]@rest[idx];basis=np.linalg.inv(rest[idx])@target if j==0 else np.linalg.inv(rest[idx])@rest[idx-1]@np.linalg.inv(trans[idx-1]@rest[idx-1])@target
   q=Rotation.from_matrix(basis[:3,:3]).as_quat();local[n]=[float(q[3]),*map(float,q[:3])]
 r={'center_bind':c.tolist(),'rotation_bind':(Rotation.from_rotvec(best.x[21:24]).as_matrix()@base_rotation).tolist(),'surface':'full-length fitted handle envelope; shared gates verify actual Meshy surfaces','axis_bind':(Rotation.from_rotvec(best.x[21:24]).as_matrix()@base_rotation)[:,2].tolist(),'radius_m':radius,'finger_local':local,'angles_degrees':np.degrees(best.x[:18]).reshape(6,3).tolist(),'min_gap_mm':float(min(gap.min(),midgap.min(),gaps(samples(pos),c,best.x).min())*1000),'digit_contact_mm':[float(np.min(np.abs(gaps(samples(pos),c,best.x,True)[m]))*1000) for m in regions],'edge_stretch_max':float(stretch.max()),'edge_stretch_p99':float(np.percentile(stretch,99)),'cost':float(np.sum(best.fun**2))}
 r['full_weapon_clearance_mm']=float(full_surface((samples(pos)-c)@np.array(r['rotation_bind'])).min()*1000) if full_surface is not None else None
 r['candidate_pass']=(r['full_weapon_clearance_mm'] is None or r['full_weapon_clearance_mm']>=-2) and r['min_gap_mm']>=-3 and max(r['digit_contact_mm'])<=3 and r['edge_stretch_max']<=4.5
 result[sd]=r;print(sd,json.dumps({k:v for k,v in r.items() if k!='finger_local'}),flush=True)
(OUTPUT/'grip_pose.json').write_text(json.dumps(result,indent=2)+'\n')
assert all(np.isfinite(r['cost']) for r in result.values())
