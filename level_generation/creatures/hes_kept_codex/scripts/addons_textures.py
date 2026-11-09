"""Project the generated prop views using the humanoid playbook's HD prop route."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes, distance_transform_edt, gaussian_filter
P=Path(__file__).resolve().parents[1];out=P/'textures/props_v2';out.mkdir(exist_ok=True)
boxes={'pick':[(44,28,624,996),(682,28,1240,996)],'club':[(202,20,495,1000),(636,20,926,1000)],'plate':[(9,92,588,867),(612,92,1162,867)],'collar':[(8,290,520,637),(520,290,1008,637)]};meta={}
for name,crops in boxes.items():
 im=Image.open(P/'references_props_v2'/f'{name}.png').convert('RGB');atlas=[]
 for box in crops:
  a=np.array(im.crop(box));mask=np.ptp(a.astype(float),axis=2)>9;mask=binary_fill_holes(mask);_,inds=distance_transform_edt(~mask,return_indices=True);a=a[tuple(inds)];atlas.append(np.array(Image.fromarray(a).resize((512,1024),Image.Resampling.LANCZOS)))
 a=np.concatenate(atlas,axis=1);Image.fromarray(a).save(out/f'{name}_basecolor.png')
 # Fine detail relief only; large shaded forms stay in the model, not the normal map.
 lum=a.mean(2)/255;detail=lum-gaussian_filter(lum,2);dy,dx=np.gradient(gaussian_filter(detail,.6));v=np.stack([-dx*.45,dy*.45,np.ones_like(dx)],axis=2);v/=np.linalg.norm(v,axis=2,keepdims=True);Image.fromarray(np.uint8(np.clip(v*.5+.5,0,1)*255)).save(out/f'{name}_normal.png')
 orm=np.zeros_like(a);orm[:,:,0]=77 if name in ('pick','club','collar') else 45;orm[:,:,1]=np.uint8(np.clip(.78-detail*.12,.65,.9)*255);Image.fromarray(orm).save(out/f'{name}_metal_rough.png');meta[name]={'source':f'references_props_v2/{name}.png','boxes':crops,'size':[1024,1024],'projection':'front and rear halves; nearest opaque material bleed','roughness':.78,'metallic':0,'specular_mask_red':True}
(out/'projection.json').write_text(json.dumps(meta,indent=2)+'\n')
