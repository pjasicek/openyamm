"""Eight-view silhouette IoU and local 11-pixel Gaussian SSIM on the occupied body crop."""
from pathlib import Path
import numpy as np,json
from PIL import Image
from scipy.ndimage import gaussian_filter
p=Path(__file__).resolve().parents[1];out=p/'review/round2/reduction'
def similarity(a,b):
 ma=a[...,3]>.5;mb=b[...,3]>.5;union=ma|mb;ys,xs=np.where(union);assert len(xs)
 iou=float((ma&mb).sum()/union.sum());a=a[ys.min():ys.max()+1,xs.min():xs.max()+1];b=b[ys.min():ys.max()+1,xs.min():xs.max()+1]
 x=a[...,:3]*a[...,3:]+.5*(1-a[...,3:]);y=b[...,:3]*b[...,3:]+.5*(1-b[...,3:])
 filt=lambda z:gaussian_filter(z,sigma=(1.5,1.5,0),truncate=3.5)
 ux,uy=filt(x),filt(y);vx=filt(x*x)-ux*ux;vy=filt(y*y)-uy*uy;vxy=filt(x*y)-ux*uy
 sm=((2*ux*uy+.01**2)*(2*vxy+.03**2))/((ux**2+uy**2+.01**2)*(vx+vy+.03**2))
 return {'silhouette_iou':iou,'textured_ssim':float(sm[5:-5,5:-5].mean())}
rows=[]
for i in range(8):
 a=np.asarray(Image.open(out/f'reference_{i}.png').convert('RGBA'),float)/255;b=np.asarray(Image.open(out/f'candidate_90_{i}.png').convert('RGBA'),float)/255;r=similarity(a,b);r['view_degrees']=45*i;rows.append(r)
d=json.loads((out/'candidate.json').read_text());d.update(views=rows,min_iou=min(r['silhouette_iou'] for r in rows),min_ssim=min(r['textured_ssim'] for r in rows));d['visual_pass']=d['min_iou']>=.995 and d['min_ssim']>=.98
(out/'curve.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
