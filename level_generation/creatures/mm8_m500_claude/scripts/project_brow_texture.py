"""Project the original blue brow paint onto the repaired continuous chart."""
from pathlib import Path
import json,numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';r=np.load(P/'work/uvraster_head.npz');patch=np.load(P/'work/brow_texture_patch.npz');co=r['pos'];cov=patch['coverage'];pos=patch['pos'];x,y=int(patch['x']),int(patch['y']);H,W=cov.shape
base=np.array(Image.open(T/'m500_head_basecolor_1k.png').convert('RGB'));hsv=np.array(Image.fromarray(base).convert('HSV'))
source=(r['piece']>=0)&(co[...,0]<-.04)&(co[...,2]>1.78)&(co[...,2]<1.86)&(co[...,1]>-.15)&(co[...,1]<-.05)&(hsv[...,0]>90)&(hsv[...,0]<205)
assert source.sum()>100
points=co[source];tree=cKDTree(points);distance,index=tree.query(pos[cov],k=12);weights=1/np.maximum(distance,.0008)**2
col=(base[source][index]*weights[...,None]).sum(1)/weights.sum(1)[:,None];rgb=np.zeros((H,W,3));rgb[cov]=col
nearest=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True);rgb=rgb[tuple(nearest)]
for suffix,value in [('basecolor_1k',rgb),('normal_1k',np.broadcast_to([128,128,255],(H,W,3))),('metal_rough_1k',np.broadcast_to([84,125,0],(H,W,3))),('region_mask',np.broadcast_to([255,0,0,0],(H,W,4)))]:
 f=T/f'm500_head_{suffix}.png';image=np.array(Image.open(f));image[y:y+H,x:x+W]=np.uint8(np.clip(value,0,255));Image.fromarray(image).save(f,optimize=True)
f=T/'m500_head_material_classes.png';image=np.array(Image.open(f));image[y:y+H,x:x+W]=1;Image.fromarray(image).save(f)
report={'source_texels':int(source.sum()),'new_chart_pixels':int(cov.sum()),'rectangle':[x,y,W,H],'maximum_projection_distance_m':float(distance[:,0].max()),'normal':'Neutral tangent normal on the small rebuilt patch; geometric normals retained.'};assert report['maximum_projection_distance_m']<.02,report
(P/'work/brow_texture_projection.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
