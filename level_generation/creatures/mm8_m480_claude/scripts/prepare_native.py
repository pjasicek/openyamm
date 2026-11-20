from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil
import numpy as np
R=Path('/home/pjasicek/github/OpenYAMM');P=R/'level_generation/creatures/mm8_m480_claude';old=R/'level_generation/creatures/mm8_m480'
for d in ('references_native','references_hd','references_head','scripts','work','review','requests','export','textures'):(P/d).mkdir(exist_ok=True)
s=json.loads((old/'sources.json').read_text()); records={}
palpath=R/'assets_dev/worlds/mm8/textures/PAL481.act';pal=palpath.read_bytes();assert hashlib.sha256(pal).hexdigest()==s['palette_sources']['481']['sha256']
for n,r in s['sources'].items():
 p=R/r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],p
 im=Image.open(p);a=np.array(im);im.putpalette(pal[:768]);im=im.convert('RGBA');im.putalpha(Image.fromarray(np.where(a==0,0,255).astype('uint8')));im.save(P/'references_native'/f'{n}.png');records[n]=r
for action,b in s['bindings']['61']['actions'].items():
 fs=b['views']['0'];sheet=Image.new('RGB',(256*len(fs),280),(50,50,50));draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(fs):
  im=Image.open(P/'references_native'/f"{f['frame']}.png");sheet.paste(im,(256*i,24),im);draw.text((256*i+4,4),f"{f['frame']} {f['duration_ms']}ms",fill='white')
 sheet.save(P/'references_native'/f'{action}_0.png')
for action,frames in [('identity',[f'm480sa{i}' for i in range(5)]),('unused_attack',[f'm480a{c}0' for c in 'abcdefgh'])]:
 sheet=Image.new('RGB',(256*len(frames),280),(50,50,50));d=ImageDraw.Draw(sheet)
 for i,n in enumerate(frames):
  im=Image.open(P/'references_native'/f'{n}.png');sheet.paste(im,(256*i,24),im);d.text((256*i+4,4),n,fill='white')
 sheet.save(P/'references_native'/f'{action}.png')
(P/'references_native/source_inventory.json').write_text(json.dumps({'frames':records,'bindings':s['bindings'],'palette_sources':s['palette_sources'],'descriptor_table':s['descriptor_table']},indent=2)+'\n')
p=P/'creature_3d_progress.json';state=json.loads(p.read_text());state.update(requested_scope='complete_production',stage='references_and_motion',status='in_progress',user_artistic_acceptance='not_recorded',next_action={'owner':'agent','action':'Inspect native anatomy, generate five HD body masters and head references, select source motions before modelling.'});p.write_text(json.dumps(state,indent=2)+'\n')
shutil.copy2(__file__,P/'scripts/prepare_native.py')
print('Verified original frames',len(records))
for k,b in s['bindings'].items():print(k,b['label'],[(a,v['native_group'],sum(f['duration_ms'] for f in v['views']['0'])) for a,v in b['actions'].items()])
