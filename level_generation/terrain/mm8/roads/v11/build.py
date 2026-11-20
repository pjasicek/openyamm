"""Calibrate only diagonal stone material against accepted straight cobbles."""
import sys,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
from scipy.ndimage import gaussian_filter,distance_transform_edt
for d in ['runtime','masks']:
 (HERE/d).mkdir(exist_ok=True)
 for f in (HERE.parent/'v10'/d).glob('*.png'):shutil.copy2(f,HERE/d/f.name)
b=json.loads((HERE.parent/'v10/build.json').read_text())
donor=read(HERE/'inputs/accepted_stones.png',512)
# A patch entirely inside a large accepted stone, sampled at runtime scale.
patch=donor[166:190,461:485]
patch=np.asarray(Image.fromarray(seams.byte(patch)).resize((12,12),Image.LANCZOS),float)
detail=patch-gaussian_filter(patch,(1.2,1.2,0),mode="wrap")
y,x=np.mgrid[:256,:256]
for r in b['tiles']:
 n=r['name']
 if n[4:] not in ['ne1','ne2','nw1','nw2']:continue
 old=read(HERE.parent/'v10/runtime'/(n+'.png'))
 alpha=read(HERE/'masks'/(n+'.png'),256)[:,:,0]/255
 smooth=gaussian_filter(old,(1.25,1.25,0))
 brightness=smooth.mean(2)
 gate=np.clip((brightness-42)/25,0,1)*np.clip((distance_transform_edt(alpha>.5)-1)/2,0,1)
 # Keep mortar boundaries/edge bevels crisp; substitute only the bright stone
 # surface grain. The actual accepted material provides all replacement detail.
 material=smooth+detail[(y+7)%12,(x+11)%12]*.8
 corrected=old+(material-old)*gate[:,:,None]
 # Keep exact installed connection pixels; feather only the material delta.
 edge=np.minimum.reduce([x,y,255-x,255-y]);w=np.clip(edge/5,0,1);w=w*w*(3-2*w)
 out=old+(corrected-old)*w[:,:,None]
 save(HERE/'runtime'/(n+'.png'),out)
 r['runtime_sha256']=sha(HERE/'runtime'/(n+'.png'))
b['method']='Diagonal surface grain calibrated to actual accepted straight-road pixels; immutable straight tiles and boundary RGB'
(HERE/'build.json').write_text(json.dumps(b,indent=2)+'\n')
