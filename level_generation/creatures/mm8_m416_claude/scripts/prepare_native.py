from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil
import numpy as np
R=Path('/home/pjasicek/github/OpenYAMM');P=R/'level_generation/creatures/mm8_m416_claude';old=R/'level_generation/creatures/mm8_m416'
for d in ('references_native','references_hd','scripts','work','review','requests','export','textures'):(P/d).mkdir(exist_ok=True)
sources=json.loads((old/'sources.json').read_text());anim=json.loads((old/'animations.json').read_text())
records={}
for n,r in sources['sources'].items():
 p=R/r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],p
 im=Image.open(p);arr=np.array(im);im.putpalette((R/'assets_dev/worlds/mm8/textures/pal417.act').read_bytes()[:768]);rgba=im.convert('RGBA');rgba.putalpha(Image.fromarray(np.where(arr==0,0,255).astype('uint8')));rgba.save(P/'references_native'/f'{n}.png');records[n]={'source':r['path'],'sha256':r['sha256'],'size':im.size}
for action,b in anim['animations']['13']['actions'].items():
 frames=b['views']['0'];sheet=Image.new('RGB',(256*len(frames),280),(50,50,50));draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(frames):
  im=Image.open(P/'references_native'/f"{f['frame']}.png");sheet.paste(im,(256*i,24),im);draw.text((256*i+4,4),f"{f['frame']} {f['duration_ms']}ms",fill='white')
 sheet.save(P/'references_native'/f'{action}_0.png')
sheet=Image.new('RGB',(256*5,280),(50,50,50));d=ImageDraw.Draw(sheet)
for i in range(5):
 im=Image.open(P/'references_native'/f'm416sa{i}.png');sheet.paste(im,(256*i,24),im);d.text((256*i+4,4),f'Native stored view {i}',fill='white')
sheet.save(P/'references_native/identity.png')
(P/'references_native/source_inventory.json').write_text(json.dumps({'frames':records,'animations':anim['animations']},indent=2)+'\n')
s=json.loads((P/'creature_3d_progress.json').read_text());s.update(requested_scope='complete_production',stage='references_and_motion',status='in_progress',required_components=[{'id':'body','required':True,'artifact_role':'body','source':'Original m416 BMPs; teal vest/bandanna, gray trousers, brown cuffed boots, red-brown sash, left leather gauntlet, right bare hand, red-brown hair.'},{'id':'crossbow','required':True,'artifact_role':'weapon','source':'Native raised one-hand idle and two-hand aimed fire; wood stock, transverse curved bow, string and bolt.'},{'id':'quiver','required':True,'artifact_role':'equipment','source':'Native anatomical right hip with pale bolt fletchings.'}],next_action={'owner':'agent','action':'Generate HD references and preview source crossbow motions before modelling.'})
(P/'creature_3d_progress.json').write_text(json.dumps(s,indent=2)+'\n')
shutil.copy2(__file__,P/'scripts/prepare_native.py')
print('Verified original files',len(records))
