"""Paired silhouette and texture measurements; object ROI avoids background-inflated SSIM."""
import json,sys,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import uniform_filter

def ssim(a,b):
    a=a.astype(float)/255;b=b.astype(float)/255
    ma=uniform_filter(a,size=(7,7,1));mb=uniform_filter(b,size=(7,7,1))
    va=uniform_filter(a*a,size=(7,7,1))-ma*ma;vb=uniform_filter(b*b,size=(7,7,1))-mb*mb
    cov=uniform_filter(a*b,size=(7,7,1))-ma*mb
    v=((2*ma*mb+.01**2)*(2*cov+.03**2))/((ma*ma+mb*mb+.01**2)*(va+vb+.03**2))
    return float(v[3:-3,3:-3].mean())

def measure(ref,cur):
    a=np.array(Image.open(ref).convert('RGBA'));b=np.array(Image.open(cur).convert('RGBA'))
    assert a.shape==b.shape
    aa=a[:,:,3]/255.;bb=b[:,:,3]/255.;mask=(aa>.5)|(bb>.5)
    y,x=np.where(mask);margin=8
    ys=slice(max(0,y.min()-margin),min(a.shape[0],y.max()+margin+1));xs=slice(max(0,x.min()-margin),min(a.shape[1],x.max()+margin+1))
    # Neutral background is composited identically, retaining antialiased silhouette coverage.
    rgb=lambda im,alpha: (im[:,:,:3]*alpha[:,:,None]+128*(1-alpha[:,:,None]))[ys,xs]
    return {'intersection':int(((aa>.5)&(bb>.5)).sum()),'union':int(mask.sum()),'iou':float(((aa>.5)&(bb>.5)).sum()/mask.sum()),'coverage_iou':float(np.minimum(aa,bb).sum()/np.maximum(aa,bb).sum()),'ssim':ssim(rgb(a,aa),rgb(b,bb))}

if __name__=='__main__':
    p=Path(sys.argv[1]);base=Path(sys.argv[2]);rows=[measure(base/f'{i}.png',p/f'{i}.png')for i in range(8)]
    report={'views':rows,'min_iou':min(v['iou']for v in rows),'min_ssim':min(v['ssim']for v in rows),'min_coverage_iou':min(v['coverage_iou']for v in rows)}
    report['pooled_iou']=sum(v['intersection']for v in rows)/sum(v['union']for v in rows)
    report['iou_aggregation']=os.environ.get('LCH_IOU_AGGREGATION','minimum')
    report['pass']=(report['pooled_iou'] if report['iou_aggregation']=='pooled' else report['min_iou'])>=.995 and report['min_ssim']>=.98
    faults=[]
    for i in range(8):
        a=np.array(Image.open(base/f'{i}.png').convert('RGBA'));b=np.array(Image.open(p/f'{i}.png').convert('RGBA'))
        mask=(a[:,:,3]>127)!=(b[:,:,3]>127)
        if rows[i]['ssim']<.98:
            mask|=(np.abs(a[:,:,:3].astype(float)-b[:,:,:3]).max(2)>24)&(a[:,:,3]>127)&(b[:,:,3]>127)
        y,x=np.where(mask);stride=max(1,len(x)//600);faults.append(list(zip(x[::stride].tolist(),y[::stride].tolist())))
    (p/'bad_pixels.json').write_text(json.dumps(faults))
    (p/'metrics.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
