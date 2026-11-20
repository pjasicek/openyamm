"""Reconstruct diagonals from one continuous sampling of accepted straight cobbles.

No independent generated RGB or legacy clipping masks are used for diagonals.
Both halves share phase at every diagonal-to-diagonal connection. Straight roads
remain immutable; a bend into a straight road retains an ordinary tile junction.
"""
import sys,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
from scipy.ndimage import map_coordinates,binary_closing,binary_fill_holes,gaussian_filter,distance_transform_edt,label
for folder in ['runtime','masks']:
 (HERE/folder).mkdir(exist_ok=True)
 for f in (HERE.parent/'v12'/folder).glob('*.png'):shutil.copy2(f,HERE/folder/f.name)
b=json.loads((HERE.parent/'v12/build.json').read_text())
# The accepted EW strip has broader stones along its travel direction. Its
# existing bevel, grout, colour and grain are all retained by this coordinate map.
donor=read(HERE.parent/'v7/runtime/drsrew.png').transpose(1,0,2)
coverage=(donor[:,:,1]>.77*donor[:,:,0])&(donor[:,:,2]>.58*donor[:,:,0])
coverage=binary_fill_holes(binary_closing(np.pad(coverage,8,mode='wrap'),iterations=4)[8:-8,8:-8])
labels,count=label(coverage);sizes=np.bincount(labels.ravel());sizes[0]=0
coverage=labels==sizes.argmax()
coverage=gaussian_filter(coverage.astype(float),.5)
shadow_distance=distance_transform_edt(np.pad(coverage<.5,256,mode='wrap'))[256:-256,256:-256]
donor_shadow=.2*np.exp(-shadow_distance/1.4)*(1-coverage)
y,x=np.indices((256,256),dtype=float)
x*=256/255;y*=256/255
for suffix in ['ne1','ne2','nw1','nw2']:
 xx=x if suffix.startswith('ne') else 256-x
 u=(xx-y+(256 if suffix.endswith('1') else 0)-128)*.8+128
 v=(xx+y)%256
 rgb=np.stack([map_coordinates(donor[:,:,c],[v,np.clip(u,0,255)],order=1,mode='grid-wrap') for c in range(3)],2)
 alpha=map_coordinates(coverage,[v,np.clip(u,0,255)],order=1,mode='grid-wrap')*(u>=0)*(u<=255)
 shade=map_coordinates(donor_shadow,[v,np.clip(u,0,255)],order=1,mode='grid-wrap')*(u>=0)*(u<=255)
 for prefix,material in [('drsr','dirt'),('gdrd','grey_dirt')]:
  n=prefix+suffix;dirt=read(M/'runtime'/(material+'.png'))
  out=rgb*alpha[:,:,None]+dirt*(1-shade[:,:,None])*(1-alpha[:,:,None])
  save(HERE/'runtime'/(n+'.png'),out)
  silhouette=binary_fill_holes(alpha>.5)
  Image.fromarray(np.uint8(silhouette)*255).resize((512,512),Image.LANCZOS).save(HERE/'masks'/(n+'.png'))
for r in b['tiles']:r['runtime_sha256']=sha(HERE/'runtime'/(r['name']+'.png'))
b['method']='All eight diagonal variants share accepted v7 EW cobble strip pixels and continuous phase; original straight roads unchanged.'
b['donor_sha256']=sha(HERE.parent/'v7/runtime/drsrew.png')
(HERE/'build.json').write_text(json.dumps(b,indent=2)+'\n')
