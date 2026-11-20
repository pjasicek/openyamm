"""Rusted ivory, rivets and forged edge wear in the existing shell atlas layout."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
P=Path(__file__).resolve().parents[1] if 'scripts' in str(Path(__file__).parent) else Path('level_generation/creatures/hes_lancer_codex')
L=json.loads((P/'work/armour_layout.json').read_text());N=L['atlas'];rng=np.random.default_rng(20424)
base=np.full((N,N,3),[33,26,23],dtype=float);height=np.zeros((N,N));rough=np.full((N,N),.65);metal=np.full((N,N),.7);mask=np.zeros((N,N,3));classes=np.full((N,N),9,dtype=np.uint8)
for name,p in L['plates'].items():
 x,y,w,h=p['rect'];yy,xx=np.mgrid[:h,:w];s=(xx+.5)/w;t=(yy+.5)/h
 edge=np.minimum.reduce([s,1-s,t,1-t]);noise=gaussian_filter(rng.random((h,w)),max(2,min(w,h)/45));noise=(noise-noise.min())/max(np.ptp(noise),1e-6)
 fine=rng.random((h,w));rust=np.clip((noise-.52)*4,0,1);rust=np.maximum(rust,np.clip((.018-edge)*45,0,1)*(noise>.4));chip=(fine>.94)&(noise>.61)
 ivory=np.array([218,207,183]);col=ivory*(.89+.16*noise[...,None]);rc=np.array([104,59,28])*(.7+.55*noise[...,None]);col=col*(1-rust[...,None])+rc*rust[...,None]
 col[chip]=[72,55,40];rim=edge<.025;black=(edge>=.025)&(edge<.052);col[rim]=np.array([136,93,42])*(.8+.35*noise[rim,None]);col[black]=np.array([36,30,26])*(.8+.35*noise[black,None])
 hh=-.16*rust-.08*chip+.2*rim-.2*black;rr=.52+.32*rust;mm=np.full((h,w),.3);mm[rim]=.85;mm[black]=.7
 # Rivet heads and their inset sockets are painted into base/normal, not micro meshes.
 for cx,cy in [(u,v) for u in (.073,.927) for v in (.09,.32,.55,.78,.91)]:
  rad=np.hypot((s-cx)*w,(t-cy)*h);r=max(3,min(w,h)*.016);socket=rad<r*1.3;head=rad<r
  col[socket]=[36,28,22];col[head]=np.array([148,112,63])*(.9+.25*(cy-t[head])/(r/h))[:,None];hh[socket]=-.25;hh[head]=np.sqrt(np.maximum(0,1-(rad[head]/r)**2))*.75;rr[head]=.42;mm[head]=.85
 sl=np.s_[y:y+h,x:x+w];base[sl]=col;height[sl]=hh;rough[sl]=rr;metal[sl]=mm;mask[sl+(0,)]=np.clip(1-rust*6,0,1)*(~rim)*(~black)*(~chip);mask[sl+(1,)]=rim
# Existing mask ramps use the same ivory/gold zones; exposed rust and iron remain uncoloured.
dy,dx=np.gradient(gaussian_filter(height,.6));normal=np.dstack([-dx*2.2,dy*2.2,np.ones_like(dx)]);normal/=np.linalg.norm(normal,axis=2)[...,None]
for suffix,im in [('basecolor',base),('normal',(normal*.5+.5)*255),('metal_rough',np.dstack([np.ones_like(rough),rough,metal])*255),('region_mask',mask*255),('material_classes',classes)]:
 for p in L['plates'].values():
  x,y,w,h=p['rect'];pad=min(4,x,y,N-x-w,N-y-h)
  if pad:im[y-pad:y+h+pad,x-pad:x+w+pad]=np.pad(im[y:y+h,x:x+w],((pad,pad),(pad,pad))+((0,0),)*(im.ndim-2),mode='edge')
 image=Image.fromarray(np.uint8(np.clip(im,0,255)))
 if suffix!='basecolor':image=image.resize((1024,1024),Image.Resampling.LANCZOS if suffix!='material_classes' else Image.Resampling.NEAREST)
 image.save(P/f'textures/forge_armour_{suffix}.png')
j=json.loads((P/'textures/lancer_ramps.json').read_text())
for m in j['materials']:
 if m['base']=='HKR_Plate':m['mask']='forge_armour_region_mask.png'
(P/'textures/forge_ramps.json').write_text(json.dumps(j,indent=2)+'\n')
assert np.isfinite(normal).all() and rust.max()>0
print('FORGE_TEXTURES',N)
