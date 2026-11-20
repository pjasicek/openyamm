"""Repair UV carry-over on the newly exposed neck, then compose the welded head strip."""
from pathlib import Path
import numpy as np,runpy,json
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage
p=Path(__file__).resolve().parents[1];t=p/'textures';r=np.load(p/'work/uvraster_UVMap.npz');pos=r['pos'];cov=r['piece']==0;c=np.array(Image.open(t/'ogr_material_classes.png'));a=np.array(Image.open(t/'ogr_basecolor_1k.png'),float)
# The old cut's pale, unpainted skin is now visible; extend verified nearby skin into that strip.
donor=cov&(c==1)&(pos[...,2]>1.33)&(pos[...,2]<1.415)&(abs(pos[...,0])<.14);target=cov&(pos[...,2]>1.415)&(pos[...,2]-.4*pos[...,1]<1.48)
assert donor.sum()>1000 and target.sum()>1000
query=pos[target].copy();query[:,2]-=.07;tree=cKDTree(pos[donor]);_,ix=tree.query(query,k=1);fade=np.clip((pos[target,2]-1.415)/.02,0,1);a[target]=a[target]*(1-fade[:,None])+a[donor][ix]*fade[:,None]
Image.fromarray(np.uint8(np.clip(a,0,255))).save(t/'ogr_basecolor_1k.png')
runpy.run_path(str(p/'scripts/review2_compose_head.py'),run_name='__main__')
n=np.array(Image.open(t/'ogr_head_normal_1k.png'),float);r=np.load(p/'work/uvraster_HeadUV.npz');valid=r['piece']>=0;bad=valid&(n[...,2]<128)
_,(yy,xx)=ndimage.distance_transform_edt(bad,return_indices=True);n[bad]=n[yy[bad],xx[bad]]
Image.fromarray(np.uint8(n)).save(t/'ogr_head_normal_1k.png')
(p/'revision_02/neck_texture_fit.json').write_text(json.dumps({'new_neck_texels':int(target.sum()),'invalid_head_normal_texels':int(bad.sum()),'method':'Extend nearby verified skin through exposed legacy cut UVs, then regenerate shared-edge head colour blend.'},indent=2)+'\n')
