"""Composite repaired stone contours, without the obsolete native clipping mask."""
import sys,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
from scipy.ndimage import binary_closing,binary_fill_holes,gaussian_filter,distance_transform_edt,map_coordinates,label
for d in ['runtime','masks']:
 (HERE/d).mkdir(exist_ok=True)
 for f in (HERE.parent/'v11'/d).glob('*.png'):shutil.copy2(f,HERE/d/f.name)
b=json.loads((HERE.parent/'v11/build.json').read_text())
gen=np.asarray(Image.open(HERE/'raw/junction.png').convert('RGB').resize((512,256),Image.LANCZOS),float)[:,:256]
# Register the generated boundary grout rows to the immutable straight tile.
# This deforms only the last 48 pixels of the diagonal, not the straight donor.
yy,xx=np.indices((256,256));amount=np.clip((xx-208)/47,0,1);amount=amount*amount*(3-2*amount)
matched=np.interp(yy,[0,75,100,120,140,160,188,255],[0,75,100,120,136,168,188,255])
sample_y=yy+(matched-yy)*amount
gen=np.stack([map_coordinates(gen[:,:,c],[sample_y,xx],order=1,mode='nearest') for c in range(3)],axis=2)
candidate=(gen[:,:,1]>.77*gen[:,:,0])&(gen[:,:,2]>.58*gen[:,:,0])
mask=binary_fill_holes(binary_closing(np.pad(candidate,6,mode='edge'),iterations=3)[6:-6,6:-6])
alpha=gaussian_filter(mask.astype(float),.5)
yy,xx=np.indices((256,256));rim=np.minimum.reduce([xx,yy,255-yy])
gate=np.clip(rim/3,0,1);gate=gate*gate*(3-2*gate)
for n,material in [('drsrne2','dirt'),('gdrdne2','grey_dirt')]:
 old=read(HERE/'runtime'/(n+'.png'))
 old[:,-1]=read(HERE.parent/'v7/runtime'/('drsrew.png' if n=='drsrne2' else 'gdrdew.png'))[:,0]
 dirt=read(M/'runtime'/(material+'.png'))
 outside=distance_transform_edt(~mask);shade=.22*np.exp(-outside/1.4)*(1-alpha)
 source=gen*alpha[:,:,None]+dirt*(1-shade[:,:,None])*(1-alpha[:,:,None])
 result=old+(source-old)*gate[:,:,None]
 target=old[:,-1]
 correction=target-result[:,-1]
 result+=correction[:,None,:]*np.exp(-(255-xx)/1.25)[:,:,None]
 result[:,-1]=target
 save(HERE/'runtime'/(n+'.png'),result)
 oldmask=read(HERE/'masks'/(n+'.png'),256)[:,:,0]/255
 newmask=oldmask+(alpha-oldmask)*gate
 closed=binary_fill_holes(binary_closing(np.pad(newmask>.5,12,mode='edge'),iterations=6)[12:-12,12:-12])
 labels,count=label(closed);sizes=np.bincount(labels.ravel());sizes[0]=0
 silhouette=labels==sizes.argmax()
 Image.fromarray(np.uint8(silhouette)*255).resize((512,512),Image.LANCZOS).save(HERE/'masks'/(n+'.png'))
for r in b['tiles']:r['runtime_sha256']=sha(HERE/'runtime'/(r['name']+'.png'))
b['method']='NE2 complete edge stones repainted with neighbouring road context; fresh coverage and contact shadow over accepted dirt. North/south/west rim retained; east grout registered to immutable straight road and RGB endpoint matched.'
(HERE/'build.json').write_text(json.dumps(b,indent=2)+'\n')
