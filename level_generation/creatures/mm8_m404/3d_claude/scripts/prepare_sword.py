"""Extract the generated sword silhouette and padded projection texture for its local mesh."""
from pathlib import Path
from PIL import Image
import numpy as np,json
p=Path(__file__).resolve().parents[1]
out=p/'textures/props';out.mkdir(parents=True,exist_ok=True)
im=Image.open(p/'references_props/sword.png').convert('RGBA');a=np.array(im);mask=a[:,:,3]>128
rows={str(y):[int(xs.min()),int(xs.max())] for y in range(im.height) if len(xs:=np.where(mask[y])[0])}
cols={str(x):[int(ys.min()+1060),int(ys.max()+1060)] for x in range(340,685) if len(ys:=np.where(mask[1060:1150,x])[0])}
profile={'rows':rows,'guard_columns':cols,'width':im.width,'height':im.height,'crop':[340,0,685,1536],'axis_x':512,'grip_row':1275,'length_m':1.65}
assert min(map(int,rows))<30 and max(map(int,rows))>1450
assert len(cols)>250
(out/'sword_profile.json').write_text(json.dumps(profile,indent=2)+'\n')
rgb=a[:,:,:3].astype(float);valid=mask.copy()
for _ in range(12):
 total=np.zeros_like(rgb);count=np.zeros(valid.shape)
 for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
  m=np.roll(np.roll(valid,dy,0),dx,1);total+=np.roll(np.roll(rgb,dy,0),dx,1)*m[:,:,None];count+=m
 fresh=(~valid)&(count>0);rgb[fresh]=total[fresh]/count[fresh,None];valid|=fresh
Image.fromarray(np.clip(rgb,30,243).astype('uint8')).crop(tuple(profile['crop'])).resize((256,1024),Image.Resampling.LANCZOS).save(out/'sword_base.png')
classes=np.full((1536,345),9,np.uint8);classes[1150:1410]=8
Image.fromarray(classes).resize((256,1024),Image.Resampling.NEAREST).save(out/'sword_material_classes.png')
orm=np.zeros((1536,345,3),np.uint8);orm[:]=[180,145,0];orm[1150:1410]=[35,220,0]
Image.fromarray(orm).resize((256,1024),Image.Resampling.NEAREST).save(out/'sword_orm.png')
print('Sword profile and 256x1024 padded textures ready.')
