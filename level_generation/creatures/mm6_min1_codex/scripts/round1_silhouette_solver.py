"""Fit only visible coarse boundary edges to the unreduced eight-view outline."""
import sys,json,math
import numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import binary_erosion
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import lsqr
path=Path(sys.argv[1]);d=json.loads(path.read_text());P=path.parents[3];R=P/'review/round1/reduction';xyz=np.array(d['positions']);trees=[]
scale=1.852535*1024/88;ppm=1024/scale
for k in range(8):
 alpha=np.asarray(Image.open(R/f'L3_combined_reference/a_{k}.png'))[:,:,3]/255.;points=[]
 for dim in [0,1]:
  low=alpha[:-1,:] if dim==0 else alpha[:,:-1];high=alpha[1:,:] if dim==0 else alpha[:,1:]
  yy,xx=np.where((low>.5)!=(high>.5));fraction=(.5-low[yy,xx])/(high[yy,xx]-low[yy,xx]);x=xx+.5+(fraction if dim==1 else 0);y=yy+.5+(fraction if dim==0 else 0);points.extend(np.c_[(x-512)/ppm,(512-y)/ppm+.93])
 trees.append(cKDTree(points))
rows=[];cols=[];values=[];rhs=[];row=0
for k,i,j in d['edges']:
 theta=k*math.pi/4;axis=np.array([math.cos(theta),math.sin(theta),0.]);vertical=np.array([0.,0.,1.])
 for u in [.15,.5,.85]:
  p=xyz[i]*(1-u)+xyz[j]*u;uv=np.array([p@axis,p[2]]);distance,index=trees[k].query(uv)
  if distance>.07:continue
  delta=trees[k].data[index]-uv
  for ax,error in zip([axis,vertical],delta):
   for vertex,weight in [(i,1-u),(j,u)]:
    for component in range(3):
     rows.append(row);cols.append(vertex*3+component);values.append(weight*ax[component])
   rhs.append(error);row+=1
A=coo_matrix((values,(rows,cols)),shape=(row,len(xyz)*3)).tocsr();delta=lsqr(A,np.array(rhs),damp=.4,atol=1e-7,btol=1e-7)[0].reshape(-1,3);length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.025/np.maximum(length,1e-9))[:,None]
assert np.isfinite(delta).all() and row>100
path.with_suffix('.delta.json').write_text(json.dumps(delta.tolist()));print('SILHOUETTE FIT',row,float(length.max()),flush=True)
