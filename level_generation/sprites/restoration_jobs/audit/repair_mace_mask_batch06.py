import json,pathlib,hashlib
import numpy as np
from PIL import Image
from scipy import ndimage
p=pathlib.Path('/home/pjasicek/github/OpenYAMM/level_generation/sprites/restoration_jobs')
for ident in ['g00015_v0_s0']:
 statepath=p/'state'/f'{ident}.json';state=json.loads(statepath.read_text());d=p/state['output_dir']
 rgb=np.asarray(Image.open(d/'raw.png').convert('RGB'),dtype=float)
 bg=np.array([255.,0.,255.]);distance=np.linalg.norm(rgb-bg,axis=2)
 # This inspected mace has brown wood and dull steel material, never near-pure luminous magenta.
 # Infer the boundary from RGB itself so the shifted AI mask cannot move the blade.
 core=ndimage.binary_erosion(distance>130,iterations=2)
 _,nearest=ndimage.distance_transform_edt(~core,return_indices=True)
 fg=rgb[nearest[0],nearest[1]];v=fg-bg
 alpha=np.clip(np.sum((rgb-bg)*v,axis=2)/np.maximum(np.sum(v*v,axis=2),1),0,1)
 alpha[core]=1;alpha[distance<65]=0
 mask=d/'mask_boundary_repaired.png';Image.fromarray(np.uint8(np.round(alpha*255))).save(mask)
 state['mask']=str(mask.relative_to(p));state['mask_sha256']=hashlib.sha256(mask.read_bytes()).hexdigest()
 statepath.write_text(json.dumps(state,indent=2)+'\n')
 (d/'mask_repair.json').write_text(json.dumps({'method':'reviewed raw RGB boundary with nearest opaque color alpha projection','original_mask_preserved':None,'raw_sha256':hashlib.sha256((d/'raw.png').read_bytes()).hexdigest(),'core_distance':130,'core_erosion':2,'background_distance':65,'scope':'Only this visually inspected steel/brown mace master; not a general palette collision fallback.'},indent=2)+'\n')
 print(ident,d)
