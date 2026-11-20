"""Join clean endpoint artwork along minimum-error seams, never blend different stones."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *

def stitch(image, donor):
    # Dynamic-programming seam through a48px overlap, selected independently
    # along the edge. A hard material ownership boundary avoids ghost stones.
    a=image.transpose(1,0,2);b=donor.transpose(1,0,2)
    cost=np.mean((a[:,1:9]-b[:,1:9])**2,axis=2)
    dp=cost.copy();back=np.zeros(cost.shape,dtype=int)
    for y in range(1,256):
        for x in range(8):
            left=max(0,x-1);right=min(8,x+2);prev=left+np.argmin(dp[y-1,left:right])
            dp[y,x]+=dp[y-1,prev];back[y,x]=prev
    path=np.zeros(256,dtype=int);path[-1]=np.argmin(dp[-1])
    for y in range(254,-1,-1):path[y]=back[y+1,path[y+1]]
    for y,x in enumerate(path+1):a[y,:x]=b[y,:x]
    return a.transpose(1,0,2)

build=json.loads((HERE/'build.json').read_text())
for r in build['tiles']:
 n=r['name']
 if n[4:] not in ['ne1','ne2','nw1','nw2']:continue
 # v9 interior retained; discard the previous endpoint colour blends by
 # restoring artwork from full generated material over the native substrate.
 old=read(HERE/'inputs'/(n+'.png'))
 gen=read(HERE.parent/'v9/raw'/('drsr'+n[4:]+'.png'),256)
 from scipy.ndimage import distance_transform_edt
 alpha=read(HERE.parent/'v8/masks'/(n+'.png'),256)[:,:,0]/255
 coverage=np.clip((distance_transform_edt(alpha>.5)-.5)/1.5,0,1)*alpha
 image=old+(gen-old)*coverage[:,:,None]
 for side,opened in r['topology'].items():
  if not opened:continue
  donor=read(HERE.parent/'v7/runtime'/(n[:4]+('ew' if side in 'EW' else 'ns')+'.png'))
  view=image.transpose(1,0,2) if side in 'EW' else image
  donor=donor.transpose(1,0,2) if side in 'EW' else donor
  if side in 'SE':view=view[::-1];donor=donor[::-1]
  view[:]=stitch(view,donor)
 save(HERE/'runtime'/(n+'.png'),image)
 r['runtime_sha256']=sha(HERE/'runtime'/(n+'.png'))
build['method']='Clean v7 roads restored; v9 diagonal interiors meet clean straight endpoint artwork via minimum-error overlap seams, without RGB averaging.'
(HERE/'build.json').write_text(json.dumps(build,indent=2)+'\n')
