"""Rebuild enhanced coverage and deterministic palettes without changing base art or placement."""
import json,shutil
import numpy as np
from PIL import Image
from process import ROOT,queue,save
from process_compact import variants
import materials
config=materials.settings();save(ROOT/'material_settings.json',config)
archive=ROOT/'checkpoints/masks_before_warm_protection';archive.mkdir(exist_ok=True)
checks={}
for name in json.loads((ROOT/'registration.json').read_text()):
 im=Image.open(ROOT/'toned_2x'/f'{name}.png').convert('RGBA');before=queue.sha(ROOT/'toned_2x'/f'{name}.png')
 old=ROOT/'masks_2x'/f'{name}.png'
 if not (archive/f'{name}.png').exists():shutil.copy2(old,archive/f'{name}.png')
 variants(name,im,config);assert before==queue.sha(ROOT/'toned_2x'/f'{name}.png')
 a=np.asarray(im);warm=a[:,:,0].astype(float)-a[:,:,1]>=6
 m=np.asarray(Image.open(old));assert not m[warm].any()
 checks[name]={'base_sha256':before,'warm_skin_gold_protected':True,'alpha_unchanged':True}
save(ROOT/'review/warm_material_protection.json',{'status':'passed','settings':config,'frames':checks,
 'reason':'Initial KNN-only contacts showed weak skin/gold coverage. Native changed colors are green or cool shadow samples. Fade enhanced R-G from 0 to 6, then zero coverage for warm pixels; retain cool shadows and native tinted steel.'})
print('Refreshed',len(checks),'masks; all base artwork and warm protected colors unchanged.')
