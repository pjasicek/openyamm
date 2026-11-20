"""Tone and locally decontaminate the reviewed female repair, preserving measured alpha."""
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
source=P.with_name('female_v4')/'6chain2v2.png'
a=np.array(Image.open(source).convert('RGBA'))
m=a[:,:,3]>=128
rgb=a[:,:,:3].astype(float)
edge=(a[:,:,3]>0)&~binary_erosion(m,iterations=4)
excess=np.maximum(0,np.minimum(rgb[:,:,0],rgb[:,:,2])-rgb[:,:,1]-7)
fix=edge&(excess>0)
# Native warm browns/reds reach excess7: preserve that range and all interior colors.
rgb[:,:,0][fix]-=excess[fix]
rgb[:,:,2][fix]-=excess[fix]
a[:,:,:3]=np.clip(np.rint(rgb*.85),0,255).astype('uint8')
out=Image.fromarray(a)
out.save(P/'6chain2v2.png')
native=rendered(Image.open(ROOT/'assets_dev/engine/icons/6chain2v2.bmp'),'item').resize(out.size,Image.Resampling.NEAREST)
for label,color in [('light','#eeeeee'),('dark','#171717')]:
 proof=Image.new('RGB',(804,1476))
 for i,im in enumerate([native,out]):
  tile=Image.new('RGBA',im.size,color);tile.alpha_composite(im)
  proof.paste(tile.convert('RGB').resize((402,1476),Image.Resampling.NEAREST),(i*402,0))
 proof.save(P/('enlarged-'+label+'.png'))
record=dict(source_sha256=digest(source),script_sha256=digest(Path(__file__)),uniform_rgb_gain=.85,
            contour_corrected_pixels=int(fix.sum()),native_magenta_excess_allowance=7,
            alpha_unchanged=True,method='Four-pixel contour: remove only excess beyond native warm-color range from R/B; preserve alpha and interior. Then common RGB tone grade.')
(P/'processing.json').write_text(json.dumps(record,indent=2)+'\n')
