from pathlib import Path
import json,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw
p=Path('level_generation/creatures/mm8_m496_claude');d=json.loads(Path('level_generation/creatures/mm8_m496/sources.json').read_text())
for folder in ['scripts','native','review','work','textures','export','motion']:(p/folder).mkdir(exist_ok=True)
records={}
for name,src in d['sources'].items():
 path=Path(src['path']);assert hashlib.sha256(path.read_bytes()).hexdigest()==src['sha256'],str(path)
 im=Image.open(path);a=np.asarray(im);rgba=np.asarray(im.convert('RGBA')).copy();rgba[...,3]=np.where(a==src['transparent_index'],0,255)
 Image.fromarray(rgba).save(p/'native'/f'{name}.png');records[name]={**src,'png':f'native/{name}.png'}
(p/'native/inventory.json').write_text(json.dumps({'identity':'mm8:m496','sources':records,'bindings':d['bindings'],'orphan_images':d['orphan_images']},indent=2)+'\n')
for key,b in d['bindings'].items():
 print('BINDING',key,b['label'],b['native_descriptor'][:13])
 for role,a in b['actions'].items():
  seq=a['views'].get('0',[]);print(role,len(seq),sum(f['duration_ms'] for f in seq),[(f['frame'],f['palette'],f['scale']) for f in seq[:2]])
 if key!=next(iter(d['bindings'])):continue
 for role,a in b['actions'].items():
  seq=a['views'].get('0',[])
  if not seq:continue
  sheet=Image.new('RGB',(256*len(seq),280*5),'#333840');draw=ImageDraw.Draw(sheet)
  for view in range(5):
   row=a['views'].get(str(view),[])
   for index,f in enumerate(row):
    if f['frame'] is None:continue
    im=Image.open(p/'native'/f"{f['frame']}.png").convert('RGBA');sheet.paste(im,(index*256,view*280),im);draw.text((index*256+5,view*280+259),f['frame'],fill='white')
  sheet.save(p/'review'/f'native_{role}.png')
state=json.loads((p/'creature_3d_progress.json').read_text());state.update(scope='complete_production',stage='references_and_motion',status='in_progress',substep='Native action/view inventory and floating torso/Djinn motion references inspected.',user_direction='MM8 Fire Elemental m496: MM6 Fire elemental effects reference plus approved floating torso and Djinn casting motion; preserve visible humanoid torso.',required_components=[{'id':'humanoid_torso','required':True},{'id':'flame_body','required':True},{'id':'native_attack_discharge','required':True}],next_action={'owner':'codex','action':'Inspect native sheets, measure figure/flame proportions, then adapt the local effect-body workflow.'},acceptance={'technical':'in_progress','agent_visual':'in_progress','user_artistic':'not_recorded'})
state['reference_projects']={'fire':'../mm6_fie1_claude/README.md','motion':'../mm6_djn_claude/README.md','effect_torso':'../mm6_fie1_claude/README.md'}
(p/'creature_3d_progress.json').write_text(json.dumps(state,indent=2)+'\n')
print('NATIVE',len(records),'frames',len(d['orphan_images']),'orphan frames')
