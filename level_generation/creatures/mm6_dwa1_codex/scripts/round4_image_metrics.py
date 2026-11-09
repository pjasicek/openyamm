"""Gaussian-window RGB SSIM on the foreground crop; alpha silhouette IoU on every view."""
import sys,json,numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import gaussian_filter,binary_dilation

def compare(reference,candidate):
 a=np.asarray(Image.open(reference).convert('RGBA'),np.float64)/255;b=np.asarray(Image.open(candidate).convert('RGBA'),np.float64)/255
 assert a.shape==b.shape
 ma=a[:,:,3]>.5;mb=b[:,:,3]>.5;assert ma.any()
 iou=float((ma&mb).sum()/(ma|mb).sum())
 # Composite both onto the same neutral background, then score only the foreground plus a 5-pixel border.
 x=a[:,:,:3]*a[:,:,3:]+.32*(1-a[:,:,3:]);y=b[:,:,:3]*b[:,:,3:]+.32*(1-b[:,:,3:]);mask=binary_dilation(ma|mb,iterations=5)
 ux=gaussian_filter(x,(1.5,1.5,0),truncate=3.5);uy=gaussian_filter(y,(1.5,1.5,0),truncate=3.5)
 vx=gaussian_filter(x*x,(1.5,1.5,0),truncate=3.5)-ux*ux;vy=gaussian_filter(y*y,(1.5,1.5,0),truncate=3.5)-uy*uy;cov=gaussian_filter(x*y,(1.5,1.5,0),truncate=3.5)-ux*uy
 score=((2*ux*uy+.01**2)*(2*cov+.03**2))/((ux*ux+uy*uy+.01**2)*(vx+vy+.03**2))
 return {'iou':iou,'ssim':float(score[mask].mean()),'reference_pixels':int(ma.sum()),'candidate_pixels':int(mb.sum())}
if __name__=='__main__':
 ref,cur=map(Path,sys.argv[1:]);rows={f.name:compare(ref/f.name,f)for f in sorted(cur.glob('*.png'))};assert len(rows)>=8
 report={'views':rows,'min_iou':min(r['iou']for r in rows.values()),'min_ssim':min(r['ssim']for r in rows.values())};report['pass']=report['min_iou']>=.995 and report['min_ssim']>=.98
 # Self-check catches channel/alpha mistakes before accepting a reduction.
 first=next(iter(cur.glob('*.png')));same=compare(first,first);assert same['iou']==1 and abs(same['ssim']-1)<1e-12
 print(json.dumps(report))
