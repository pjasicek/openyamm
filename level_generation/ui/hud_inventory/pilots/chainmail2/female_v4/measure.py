"""Actual female armor contour diagnostics; no automatic visual acceptance."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_erosion
P=Path(__file__).resolve().parent
HUD=P.parents[2]
sys.path.insert(0,str(HUD))
from freeze_targets import rendered
from finalize_classification import ROOT,digest
ims=[rendered(Image.open(ROOT/'assets_dev/engine/icons/6chain2v2.bmp'),'item').resize((134,492),Image.Resampling.NEAREST),Image.open(P/'6chain2v2.png').convert('RGBA')]
results=[]
for im in ims:
 a=np.array(im);m=a[:,:,3]>=128
 ys,xs=np.where(m[42:68,99:123]);maxx=xs.max();arm=[int(maxx+99),float(np.mean(ys[xs==maxx]+42))]
 gap=None
 for y in range(190,270):
  xs=np.where(m[y])[0]
  if len(xs)==0:continue
  holes=np.where(~m[y,xs.min():xs.max()+1])[0]+xs.min()
  if len(holes)>2:gap=[float(np.mean(holes)),y];break
 ys,xs=np.where(m[395:435,53:81]);bottom=ys.max();foot=[float(np.mean(xs[ys==bottom]+53)),int(bottom+395)]
 edge=(a[:,:,3]>0)&~binary_erosion(m,iterations=4);rgb=a[:,:,:3].astype(float);e=np.maximum(0,np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1])
 results.append(dict(underarm=arm,crotch_gap=gap,crossed_foot=foot,edge_magenta_max=float(e[edge].max()),edge_above2=int(((e>2)&edge).sum())))
record=dict(artifact_sha256=digest(P/'6chain2v2.png'),script_sha256=digest(Path(__file__)),method='Alpha128 rightmost underarm in x99..122,y42..67; first internal leg gap wider than2 pixels in y190..269; lowest crossed foot within x53..80,y395..434.',native=results[0],restored=results[1])
(P/'feature-measurements.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
