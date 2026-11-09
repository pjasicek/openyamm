"""Fit existing four-influence garment weights to bounded stretch across retained motions."""
import sys,json,numpy as np
from pathlib import Path
from scipy.optimize import minimize
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
g=G.Glb(P/'export/mm6_mer1.glb');level=int(sys.argv[1])if len(sys.argv)>1 else 0;m=G.load_meshes(g)[level];cfg=json.loads((P/'gates.json').read_text());ids=np.array(cfg['lod_regions'][m.label.split('/')[-1]]['shirt']['vertices']);_,first,inv=np.unique(np.round(m.rest[ids],7),axis=0,return_index=True,return_inverse=True);ids=ids[first];rest=m.rest[ids];j=m.joints[ids];w0=m.weights[ids];lookup={tuple(np.round(v,7)):i for i,v in enumerate(rest)};edges=[]
for a,b in m.edges:
 ia=lookup.get(tuple(np.round(m.rest[a],7)));ib=lookup.get(tuple(np.round(m.rest[b],7)))
 if ia is not None and ib is not None and ia!=ib:edges.append(sorted([ia,ib]))
edges=np.unique(edges,axis=0);a,b=edges.T;length=np.linalg.norm(rest[a]-rest[b],axis=1)
active=(abs(rest[:,0])>.12)&(abs(rest[:,0])<.42)&(rest[:,2]>1.06);var=np.where(active)[0]
Ds=[];samples=[]
for role,step in [('Attack',.07),('Death',.14),('Running',.08),('Standing',.3),('Fidget',.5)]:
 anim=next(x for x in g.doc['animations']if x['name']==role);duration=max(g.accessor(s['input']).max()for s in anim['samplers']);times=np.linspace(0,duration,int(duration/step)+2)
 for t,pose in zip(times,g.pose(anim,times)):
  mat=(pose[m.skin_nodes]@m.bind)[j];D=np.einsum('nkij,nj->nki',mat[:,:,:3,:3],m.vertices[ids])+mat[:,:,:3,3];Ds.append(D);samples.append([role,float(t)])
D=np.array(Ds);target=np.einsum('tvkc,vk->tvc',D,w0);shape=(len(var),4);x0=np.log(np.maximum(w0[var],.0001));calls=0
# Preserve each vertex's original influence support. This changes weights, never the motion or UVs.
def objective(x):
 global calls
 z=x.reshape(shape);exp=np.exp(z-z.max(1,keepdims=True));s=exp/exp.sum(1,keepdims=True);W=w0.copy();W[var]=s;pos=np.einsum('tvkc,vk->tvc',D,W);dif=pos[:,a]-pos[:,b];dist=np.maximum(np.linalg.norm(dif,axis=2),1e-9);ratio=dist/length;ex=np.maximum(ratio-1.78,0);compression=np.minimum(ratio-.25,0);pen=ex+compression
 value=np.mean(ex**2+compression**2);ge=2*pen[...,None]*dif/(dist*length)[...,None]/pen.size;gp=np.zeros_like(pos)
 for t in range(len(D)):np.add.at(gp[t],a,ge[t]);np.add.at(gp[t],b,-ge[t])
 delta=pos-target;value+=.04*np.mean(delta**2);gp+=.08*delta/delta.size;gw=np.einsum('tvc,tvkc->vk',gp,D);dw=W-w0;value+=.000015*np.mean(dw**2);gw+=.00003*dw/dw.size;grad=(gw[var]-(gw[var]*s).sum(1,keepdims=True))*s;calls+=1
 if calls%50==0:print('FIT',calls,float(value),flush=True)
 return value,grad.ravel()
result=minimize(objective,x0.ravel(),jac=True,method='L-BFGS-B',options={'maxiter':500,'ftol':1e-12,'gtol':1e-9,'maxls':30});z=result.x.reshape(shape);s=np.exp(z-z.max(1,keepdims=True));W=w0.copy();W[var]=s/s.sum(1,keepdims=True)
np.savez(P/f'work/round3/shirt_fit_lod{level}.npz',rest=rest,joints=j,weights=W,bones=np.array(m.bone_names));(P/f'review/round3/shirt_fit_lod{level}.json').write_text(json.dumps({'method':'Four existing joint influences per vertex; constrained blend-weight fit over retained library poses. No animation, vertex position, topology or UV change.','iterations':result.nit,'success':bool(result.success),'message':str(result.message),'objective':float(result.fun),'sample_count':len(D),'changed_vertices':len(var),'max_weight_change':float(abs(W-w0).max())},indent=2));print(result.message,flush=True)
