import json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
P=Path(__file__).resolve().parents[1];selection=json.loads((P/'review/reduction/selection.json').read_text());rows=[]
for level,entry in enumerate([{'textures':'textures'}]+selection['body']):
 folder=P/entry['textures'];polys=json.loads((P/f'work/review1/hand_uv_{level}.json').read_text());files=([folder/'mer1_body_basecolor_1k.png',folder/'mer1_body_normal_1k.png']+list(folder.glob('mer1_?_preview.png')))if level==0 else([folder/'0_basecolor.png',folder/'0_normal.png']+list(folder.glob('mer1_?_preview.png')))
 for path in files:
  if not path.exists():continue
  backup=path.with_name(path.stem+'_before_review1.png')
  if not backup.exists():shutil.copyfile(path,backup)
  im=Image.open(backup).convert('RGB');a=np.asarray(im).copy();w,h=im.size;mask=Image.new('L',(w,h));draw=ImageDraw.Draw(mask)
  for poly in polys:draw.polygon([(u*w,(1-v)*h)for u,v in poly],fill=255)
  mask=np.asarray(mask.filter(ImageFilter.MaxFilter(9)))>0
  if 'normal'in path.name:
   values=a.astype(float);values[...,:2]=128+(values[...,:2]-128)*.18;values[...,2]=250+(values[...,2]-250)*.18;a[mask]=np.uint8(np.clip(values[mask],0,255))
  else:
   # Broad, low-amplitude skin variation preserves shading without the incorrect brown islands.
   blur=np.asarray(im.filter(ImageFilter.GaussianBlur(8)),float)/255;lum=blur@np.array([.2126,.7152,.0722]);variation=np.clip(lum-np.median(lum[mask]),-.15,.15)*.09
   linear=np.array([.62,.415,.28])+variation[...,None];rgb=np.where(linear<=.0031308,12.92*linear,1.055*linear**(1/2.4)-.055);a[mask]=np.uint8(np.clip(rgb[mask]*255+.5,0,255))
   rows.append({'file':str(path.relative_to(P)),'hand_texels':int(mask.sum()),'target_linear_mean':float(np.array([.62,.415,.28])@np.array([.2126,.7152,.0722]))})
  Image.fromarray(a).save(path)
(P/'review/review1_skin.json').write_text(json.dumps(rows,indent=2))
