from pathlib import Path
import numpy as np,json
from PIL import Image
p=Path(__file__).resolve().parents[1];shifts=json.loads((p/'work/head_uv_shifts.json').read_text());src=p/'meshy/head_retexture_v1';out=p/'work/head_uv_repaired';out.mkdir(exist_ok=True)
for f in src.glob('texture_urls_0_*.png'):
 im=Image.open(f);old=np.flipud(np.asarray(im));factor=old.shape[0]//1024;new=np.zeros((1280*factor,1280*factor,*old.shape[2:]),old.dtype);new[:old.shape[0],:old.shape[1]]=old;assert old.shape[0]==old.shape[1] and factor>=1
 for s in shifts:
  x,y=np.array(s['from'])*factor;tx,ty=np.array(s['to'])*factor;w,h=np.array(s['size'])*factor
  assert min(x,y,tx,ty)>=0 and x+w<=old.shape[1] and y+h<=old.shape[0] and tx+w<=new.shape[1] and ty+h<=new.shape[0]
  new[ty:ty+h,tx:tx+w]=old[y:y+h,x:x+w]
 Image.fromarray(np.flipud(new)).save(out/f.name)
print('Translated head base colour, normal, roughness and metallic tiles without rotation.')
