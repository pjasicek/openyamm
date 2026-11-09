"""Carry the retained body's skin detail continuously through the replacement neckline."""
from pathlib import Path
import numpy as np,json
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage
p=Path(__file__).resolve().parents[1];t=p/'textures';r=np.load(p/'work/uvraster_UVMap.npz');pos=r['pos'];a=np.array(Image.open(t/'ogr_basecolor_1k.png'),float)/255;c=np.array(Image.open(t/'ogr_material_classes.png'));mask=(r['piece']==0)&(c==1)&(pos[...,2]>1.29)&(pos[...,2]<1.385)&(abs(pos[...,0])<.17)
tree=cKDTree(pos[mask]);col=a[mask]
for prefix,layer in [('ogr','UVMap'),('ogr_head','HeadUV')]:
 r=np.load(p/f'work/uvraster_{layer}.npz');pos=r['pos'];h=pos[...,2]-.4*pos[...,1];c=np.array(Image.open(t/f'{prefix}_material_classes.png'));m=(r['piece']==0)&(c==1)&(h>1.39)&(h<1.55)
 q=pos[m].copy();q[:,2]=1.295+(h[m]-1.39)*.55;d,ids=tree.query(q,k=4);weights=1/np.maximum(d,.0001)**2;detail=(col[ids]*weights[...,None]).sum(1)/weights.sum(1)[:,None];luma=detail@np.array([.2126,.7152,.0722]);detail=np.array([.47843137,.36862745,.26666667])*np.clip(luma[:,None]/np.median(luma),.88,1.12)
 f=t/f'{prefix}_basecolor_1k.png';a=np.array(Image.open(f),float)/255;w=np.minimum(np.clip((h[m]-1.39)/.04,0,1),np.clip((1.55-h[m])/.03,0,1));w=w*w*(3-2*w);a[m]=a[m]*(1-w[:,None])+detail*w[:,None]
 _,(yy,xx)=ndimage.distance_transform_edt(r['piece']<0,return_indices=True);a=a[yy,xx];Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(f)
(p/'revision_02/neck_detail.json').write_text(json.dumps({'method':'Continuous world-space transfer of retained chest/back skin detail through the joined neck','donor_texels':int(mask.sum())},indent=2)+'\n')
