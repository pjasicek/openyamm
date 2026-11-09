"""Raster-check the frozen UV triangles for unintended overlap before the paid texture handoff."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

PROJECT=Path(__file__).resolve().parents[1]
data=np.load(PROJECT/'work/uv3d.npz');size=1024;counts=np.zeros((size,size),np.uint16);owner=np.full((size,size),-1,np.int32);bad=set()
for index,triangle in enumerate(data['uv']):
    p=triangle*np.array([size,-size])+np.array([0,size])
    lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),size-1)
    x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
    a,b,c=p;d=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(d)<1e-12:continue
    w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/d
    w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/d
    inside=(w0>1e-6)&(w1>1e-6)&(1-w0-w1>1e-6)
    tile=owner[lo[1]:hi[1]+1,lo[0]:hi[0]+1];previous=tile[inside&(tile>=0)]
    if len(previous):bad.add(index);bad.update(previous.tolist())
    tile[inside]=index
    counts[lo[1]:hi[1]+1,lo[0]:hi[0]+1]+=inside.astype(np.uint16)
ratio=float((counts>1).sum()/max(1,(counts>0).sum()))
report={'resolution':size,'coverage':float((counts>0).mean()),'overlap_fraction':ratio,
        'overlap_pixels':int((counts>1).sum()),'checker_review':['review/checker_side.png','review/checker_front.png','review/checker_head.png']}
(PROJECT/'work/uv_overlap.json').write_text(json.dumps(report,indent=2)+'\n')
Image.fromarray(np.where(counts>1,255,np.where(counts>0,128,0)).astype(np.uint8)).save(PROJECT/'review/uv_coverage.png')
(PROJECT/'work/uv_overlap_faces.json').write_text(json.dumps(sorted(bad))+'\n')
print(json.dumps(report));assert ratio<.001,'Unexpected UV overlap'
