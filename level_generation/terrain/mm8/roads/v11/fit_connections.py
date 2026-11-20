"""Fit only diagonal endpoint artwork to immutable straight-road neighbours."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
from scipy.ndimage import gaussian_filter
b=json.loads((HERE/'build.json').read_text())
for r in b['tiles']:
 n=r['name']
 if n[4:] not in ['ne1','ne2','nw1','nw2']:continue
 im=read(HERE/'runtime'/(n+'.png'))
 for side,opened in r['topology'].items():
  if not opened:continue
  donor=read(HERE.parent/'v10/runtime'/(n[:4]+('ew' if side in 'EW' else 'ns')+'.png'))
  view=im.transpose(1,0,2) if side in 'EW' else im
  donor=donor.transpose(1,0,2) if side in 'EW' else donor
  if side in 'SE':view=view[::-1];donor=donor[::-1]
  # Both native straight endpoints already agree. Copy the actual inward
  # continuation, choosing ownership along low-error grout in the overlap.
  a=view[:32].transpose(1,0,2);d=donor[:32].transpose(1,0,2)
  am=(a[:,:,1]>.77*a[:,:,0])&(a[:,:,2]>.58*a[:,:,0]);dm=(d[:,:,1]>.77*d[:,:,0])&(d[:,:,2]>.58*d[:,:,0])
  costs=np.mean((a-d)**2,2)+20000*(am!=dm)
  cost=costs[:,6:30];dp=cost.copy();back=np.zeros(cost.shape,dtype=int)
  for y in range(1,256):
   for x in range(24):
    l=max(0,x-1);u=min(24,x+2);j=l+np.argmin(dp[y-1,l:u]);dp[y,x]+=dp[y-1,j];back[y,x]=j
  path=np.zeros(256,dtype=int);path[-1]=np.argmin(dp[-1])
  for y in range(254,-1,-1):path[y]=back[y+1,path[y+1]]
  for y,x in enumerate(path+6):a[y,:x]=d[y,:x]
  view[:32]=a.transpose(1,0,2)
 save(HERE/'runtime'/(n+'.png'),im);r['runtime_sha256']=sha(HERE/'runtime'/(n+'.png'))
(HERE/'build.json').write_text(json.dumps(b,indent=2)+'\n')
