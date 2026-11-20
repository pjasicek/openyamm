from pathlib import Path
import numpy as np,json
from PIL import Image
p=Path(__file__).resolve().parents[1]
for name,job in [('UVMap','body_retexture_v2'),('HeadUV','head_retexture_v1')]:
 shifts=json.loads((p/f'work/uv_shifts_{name}.json').read_text());src=p/'meshy'/job;out=p/f'work/uv_repaired_{name}';out.mkdir(exist_ok=True)
 for f in src.glob('texture_urls_0_*.png'):
  old=np.flipud(np.asarray(Image.open(f)));new=old.copy();factor=old.shape[0]//1024;assert old.shape[0]==old.shape[1] and factor>=1
  for shift in shifts:
   x,y=np.array(shift['from'])*factor;tx,ty=np.array(shift['to'])*factor;w,h=np.array(shift['size'])*factor
   assert min(x,y,tx,ty)>=0 and max(x+w,tx+w)<=old.shape[1] and max(y+h,ty+h)<=old.shape[0]
   new[ty:ty+h,tx:tx+w]=old[y:y+h,x:x+w]
  Image.fromarray(np.flipud(new)).save(out/f.name)
 print('Translated maps',name,len(shifts))
