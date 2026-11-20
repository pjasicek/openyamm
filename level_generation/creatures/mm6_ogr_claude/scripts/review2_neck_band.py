from pathlib import Path
import numpy as np,json
from PIL import Image
p=Path('level_generation/creatures/mm6_ogr_claude')
for name in ['export_runtime.py','review2_gates.py','review2_dense_check.py']:
 f=p/'scripts'/name;f.write_text(f.read_text().replace('rig_v14.blend','rig_v15.blend'))
# Match the two independently textured neck surfaces through one world-space colour band.
r=np.load(p/'work/uvraster_UVMap.npz');pos=r['pos'];a=np.asarray(Image.open(p/'textures/ogr_basecolor_1k.png'),float)/255;c=np.array(Image.open(p/'textures/ogr_material_classes.png'));donor=(r['piece']==0)&(c==1)&(pos[...,2]>1.33)&(pos[...,2]<1.4)&(abs(pos[...,0])<.14);colour=np.median(a[donor],axis=0)
for prefix,layer in [('ogr','UVMap'),('ogr_head','HeadUV')]:
 r=np.load(p/f'work/uvraster_{layer}.npz');pos=r['pos'];c=np.array(Image.open(p/f'textures/{prefix}_material_classes.png'));h=pos[...,2]-.4*pos[...,1];mask=(r['piece']==0)&(c==1)
 w=np.clip((h-1.39)/.04,0,1)*np.clip((1.55-h)/.03,0,1);w=w*w*(3-2*w);w*=mask
 for kind,target in [('basecolor',colour),('normal',np.array([.5,.5,1]))]:
  path=p/f'textures/{prefix}_{kind}_1k.png';a=np.array(Image.open(path),float)/255;a=a*(1-w[...,None])+target*w[...,None];Image.fromarray(np.uint8(a*255+.5)).save(path)
print('NECK_BAND_COLOUR',colour)
