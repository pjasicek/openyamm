"""Sparse screen-contour fitting; retain topology and weights, bound changes to 15 mm."""
import sys,json,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt,map_coordinates,gaussian_filter
from scipy.optimize import least_squares
from scipy.sparse import coo_matrix
D=Path(sys.argv[1]);z=np.load(D/'fit_input.npz');V=z['V'];edges=z['edges'];views=z['views'];basis=z['basis'];center=z['center'];fixed=z['fixed'];scale=float(z['scale']);N=len(V);free=np.where(~fixed)[0];remap=np.full(N,-1);remap[free]=np.arange(len(free));fields=[];grad=[]
for i in range(8):
 a=np.array(Image.open(Path(os.environ.get('FIGC_CONTOUR_REF',str(D.parent/'export_comparison/reference_lod3')))/f'{i}.png'))[:,:,3]/255;mask=a>.5;sd=distance_transform_edt(~mask)-distance_transform_edt(mask);sd=gaussian_filter(sd,.5);fields.append(sd);grad.append(np.gradient(sd))
t=np.linspace(.1,.9,7);a=np.repeat(edges[:,0],len(t));b=np.repeat(edges[:,1],len(t));view=np.repeat(views,len(t));t=np.tile(t,len(edges));A=basis[view];M=len(a);reg=.65

def evaluate(x,jac=False):
 pts=V.copy();pts[free]=x.reshape(-1,3);p=pts[a]*(1-t[:,None])+pts[b]*t[:,None];uv=np.einsum('nij,nj->ni',A,p-center)*scale+95.5;val=np.zeros(M);G=np.zeros((M,2))
 for i in range(8):
  take=np.where(view==i)[0];coords=np.array([uv[take,1],uv[take,0]]);val[take]=map_coordinates(fields[i],coords,order=1,mode='nearest')
  if jac:
   G[take,0]=map_coordinates(grad[i][1],coords,order=1,mode='nearest');G[take,1]=map_coordinates(grad[i][0],coords,order=1,mode='nearest')
 if not jac:return np.r_[val,((pts[free]-V[free])*scale*reg).ravel()]
 D3=np.einsum('ni,nij->nj',G,A)*scale;rows=[];cols=[];data=[]
 for endpoint,w in [(a,1-t),(b,t)]:
  take=np.where(remap[endpoint]>=0)[0]
  for k in range(3):rows.extend(take);cols.extend(remap[endpoint[take]]*3+k);data.extend(D3[take,k]*w[take])
 rr=np.arange(len(free)*3);rows.extend(M+rr);cols.extend(rr);data.extend(np.full(len(rr),scale*reg));return coo_matrix((data,(rows,cols)),shape=(M+len(rr),len(rr))).tocsr()
x=V[free].ravel();before=float(np.mean(evaluate(x)**2));lo=x-.010;hi=x+.010
feet=np.where(V[free,2]<.03)[0]*3+2;lo[feet]=x[feet]-1e-8;hi[feet]=x[feet]+1e-8
res=least_squares(evaluate,x,jac=lambda x:evaluate(x,True),bounds=(lo,hi),max_nfev=50,ftol=1e-5,xtol=1e-5,gtol=1e-5);after=float(np.mean(evaluate(res.x)**2));assert after<=before;out=V.copy();out[free]=res.x.reshape(-1,3);np.save(D/'fit_output.npy',out);(D/'fit_report.json').write_text(json.dumps({'vertices':N,'free_vertices':len(free),'contour_edges':len(edges),'loss_before':before,'loss_after':after,'maximum_displacement_mm':float(np.linalg.norm(out-V,axis=1).max()*1000),'solver_status':int(res.status)},indent=2));print('FIT',before,after,flush=True)
