"""Native diagonal structure with bounded generated microdetail and separate contact shade."""
import sys, json, shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
from common import *
from scipy.ndimage import gaussian_filter, distance_transform_edt
from PIL import ImageDraw
NAMES=['drsrne1','drsrne2','drsrnw1','drsrnw2']
RAW=['exec-00cbe4ba-f23c-4e4c-8bfa-0c5c47044638.png','exec-70f2adbe-17ec-4543-85a7-a5eadabc84ce.png','exec-2fb2fb0b-1a89-4dcf-9ffd-2a13adfb61e9.png','exec-85766fb8-d319-484c-b304-686296bbee16.png']
for folder in ['runtime','masks','shading']: (HERE/folder).mkdir(exist_ok=True)
for folder in ['runtime','masks']:
    for f in (HERE.parent/'v7'/folder).glob('*.png'): shutil.copy2(f,HERE/folder/f.name)
records=[]
for name,raw in zip(NAMES,RAW):
    source=Path('/home/pjasicek/.codex/generated_images/01a07fff-d641-78c1-a58a-4501f7c594bd')/raw
    shutil.copy2(source,HERE/'raw'/f'{name}.png')
    native=read(P/'references'/f'{name}.png',512)
    mask=read(HERE/'inputs'/f'{name}_native_mask.png',512)[:,:,0]/255
    mask=np.clip(mask,0,1)
    generated=read(HERE/'raw'/f'{name}.png',512)
    detail=generated-gaussian_filter(generated,(2,2,0))
    # Native macro forms, grout and edge stones remain unwarped. Generated
    # texture contributes only bounded detail inside bright native stones.
    interior=distance_transform_edt(mask>.5)
    gate=np.clip((interior-3)/5,0,1)*np.clip((native.mean(2)-48)/35,0,1)
    stone=native+np.clip(native-gaussian_filter(native,(1.5,1.5,0)),-8,8)*.55
    stone+=np.clip(detail,-9,9)*gate[:,:,None]*.65
    # Contact shade is a separate field outside the recovered footprint.
    outside=distance_transform_edt(mask<.5)
    shade=.25*np.exp(-outside/3)*(1-mask)
    for prefix,material in [('drsr','dirt'),('gdrd','grey_dirt')]:
        target=prefix+name[4:]
        background=read(M/'materials'/f'{material}.png',512)
        result=background*(1-shade[:,:,None])*(1-mask[:,:,None])+stone*mask[:,:,None]
        save(HERE/'runtime'/f'{target}.png',np.asarray(Image.fromarray(seams.byte(result)).resize((256,256),Image.LANCZOS)))
        save(HERE/'masks'/f'{target}.png',mask*255)
        save(HERE/'shading'/f'{target}.png',shade*255)
    records.append(dict(name=name,input_sha256=sha(HERE/'inputs'/f'{name}_native_512.png'),raw_sha256=sha(HERE/'raw'/f'{name}.png'),original_generated_path=str(source)))
(HERE/'generation.json').write_text(json.dumps(dict(tool='built-in imagegen',calls=4,prompt_sha256=sha(HERE/'prompts/native_restoration.txt'),images=records),indent=2)+'\n')
build=json.loads((HERE.parent/'v7/build.json').read_text())
for r in build['tiles']: r['runtime_sha256']=sha(HERE/'runtime'/(r['name']+'.png'))
build['method']='native structure plus bounded generated microdetail; separate contact shading'
(HERE/'build.json').write_text(json.dumps(build,indent=2)+'\n')
