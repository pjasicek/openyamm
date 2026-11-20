from pathlib import Path
import json,hashlib,shutil
P=Path('level_generation/creatures/mm8_m544_claude')
V=P/'review/viewer';V.mkdir(exist_ok=True)
(V/'feedback').mkdir(exist_ok=True)
if not (V/'feedback/user_feedback.json').exists():
    (V/'feedback/user_feedback.json').write_text('{"findings": []}\n')
template=P.parent/'mm8_m564_claude/review/viewer'
for name in ['index.html','review.js']:
    s=(template/name).read_text().replace('Gorgon','Unicorn').replace('gorgon','unicorn')
    s=s.replace('mm6:natm','mm8:m544').replace('mm6_natm_claude','mm8_m544_claude')
    s=s.replace('Brass, Bronze and Iron Unicorn. Eight animations with a planted four-beat walk and a heavy horn strike.',
                'Unicorn Foal, Unicorn and Herd Leader share this coat and rig, with increasing native size. Nine clips include gallop, rear, horn strike and breath.')
    s=s.replace('../ingame/out_sprites/front.png','../ingame/out_sprite/tiers.png')
    s=s.replace('../ingame/out_models/front.png','../ingame/out_3d/tiers.png')
    s=s.replace('../ingame/in_sprites/front.png','../ingame/in_sprite/tiers.png')
    s=s.replace('../ingame/in_models/front.png','../ingame/in_3d/tiers.png')
    s=s.replace('mm8-m564-claude','mm8-m544-claude')
    s=s.replace('body:[0,.22,0,1.65], head:[0,.30,.32,.65], arms:[0,.13,.18,.65], shoulders:[0,.3,.15,.8], skirt:[0,.23,-.2,.9], feet:[0,.055,0,1.3]',
                'body:[0,.40,0,2.05], head:[0,.56,.34,.95], arms:[0,.20,.18,.9], shoulders:[0,.38,.18,1], skirt:[0,.32,-.18,1], feet:[0,.055,0,1.5]')
    s=s.replace("${anchor.phase}${anchor.source_images.length===1 ? ' · Only a genuine front sprite exists.' : ''}",'complete native source sequence')
    (V/name).write_text(s)
import subprocess
subprocess.run(['python3',str(P/'scripts/viewer_tiers.py')],check=True)
model=V/'mm8_unicorn.glb';digest=hashlib.sha256(model.read_bytes()).hexdigest()
motion=json.loads((P/'work/animation_report.json').read_text())
native={'Standing':'standing','Walking':'walk','Running':'walk','Attack':'attack','Cast':'attack',
        'Hit':'hit','Fidget':'fidget','Death':'death','Dead':'corpse'}
manifest={'revision':'unicorn_v1','default_model':'unicorn_a','default_clip':'Standing',
          'feedback':'feedback/user_feedback.json','models':[], 'clips':{}}
for tier,label in zip('abc',['Unicorn Foal · size 1.2','Unicorn · size 1.4','Herd Leader · size 1.7']):
    manifest['models'].append({'id':'unicorn_'+tier,'label':label,'revision':'unicorn_v1',
                              'url':'mm8_unicorn.glb?v='+digest[:12],'sha256':digest})
for name,info in motion.items():
    manifest['clips'][name]={'label':name,'duration':info['duration'],'mode':'loop' if info['loop'] else 'once',
        'provenance':'Locally fitted equine rig and native-informed motion. Native tiers differ in size only; viewer frames the shared model.',
        'anchors':[{'time':0,'label':'Native sequence','phase':'native source study','source_images':['../../native/'+native[name]+'_side.png']}]}
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('VIEWER',V)
