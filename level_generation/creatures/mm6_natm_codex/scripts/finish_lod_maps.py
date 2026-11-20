"""Keep the runtime specular-mask packing and an ordinary AO/roughness/metal source artifact."""
import sys,numpy as np
from pathlib import Path
from PIL import Image
root=Path(sys.argv[1]);size=int(sys.argv[2])
for folder in [root/'body',root/'spear',root/'buckler']:
 for path in folder.glob('[01]_*.png'):
  if 'preview'in path.name:continue
  im=Image.open(path).convert('RGBA' if path.stem.endswith('basecolor') and (folder/'opacity.png').exists() else 'RGB')
  if path.name=='0_basecolor.png' and (folder/'opacity.png').exists():im.putalpha(Image.open(folder/'opacity.png').convert('L').resize(im.size))
  im=im.resize((size,size),Image.Resampling.LANCZOS)
  if path.stem.endswith('normal'):
   n=np.asarray(im,float)/127.5-1;n/=np.maximum(np.linalg.norm(n,axis=2,keepdims=True),1e-8);im=Image.fromarray(np.uint8(np.clip(n*.5+.5,0,1)*255+.5))
  elif path.stem.endswith('region_mask'):
   a=np.asarray(im).copy();a[:,:,2]=0;im=Image.fromarray(a)
  im.save(path)
 for path in folder.glob('[01]_metal_rough.png'):
  a=np.asarray(Image.open(path).convert('RGB')).copy();a[:,:,0]=np.asarray(Image.open(folder/f'{path.name[0]}_ao.png').convert('L'));Image.fromarray(a).save(folder/f'{path.name[0]}_orm.png')
assert all(Image.open(p).size==(size,size)for p in root.glob('*/[01]_basecolor.png'))
