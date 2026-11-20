from pathlib import Path
import hashlib,json,numpy as np
from PIL import Image
p=Path(__file__).resolve().parents[1];v=p/'review/viewer';inventory=json.loads((p/'native/inventory.json').read_text());info=json.loads((p/'export/export_info.json').read_text())
for name,record in inventory['sources'].items():
 if not record['referenced']:continue
 image=Image.open(record['path']);indices=image.copy();image=image.convert('RGBA');alpha=Image.fromarray(np.where(np.asarray(indices)==0,0,255).astype('uint8'));image.putalpha(alpha);image.save(p/'native'/f'{name}.png')
models=[]
for tier,label in zip('abc',['Cyclops','Cyclops Hunter','Cyclops Warrior']):
 f=v/f'mm8_m520_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();models.append({'id':f'm520_{tier}','label':label,'revision':'m520_review_01','url':f'{f.name}?v={h[:12]}','sha256':h})
provenance={'Standing':'Standard Idle — fitted grounded stance','Walking':'Orc Walk — fitted heavy gait','Running':'Running (5) — heavy grounded run','Attack':'Throw In torso; native pickup, two-hand lift and release at 1.0 s','Hit':'Standing React Small From Front — additive relaxed recoil','Death':'Mutant Dying — grounded backward collapse','Dead':'Death endpoint','Fidget':'Orc Idle (1) — heavy idle variation'}
roles={'Standing':'standing','Walking':'walk','Running':'walk','Attack':'attack','Hit':'hit','Death':'death','Dead':'corpse','Fidget':'fidget'};clips={}
for name,bounds in info['clips'].items():
 duration=(bounds[1]-bounds[0])/info['fps'];role=roles.get(name);anchors=[]
 native=inventory['bindings']['91']['actions'].get(role,{}) if role else {}
 frames=native.get('views',{}).get('0',[])
 for i,row in enumerate(frames):
  seconds=duration*i/max(len(frames)-1,1)
  if name=='Attack':seconds=[0,.23,.38,.60,.82,.91,1.0,1.6][i]
  anchors.append({'time':seconds,'label':str(i+1),'phase':'Native pose reference; 3D timing is fitted','source_images':[f'../../native/{native["views"][str(view)][min(i,len(native["views"][str(view)])-1)]["frame"]}.png' for view in range(5) if str(view) in native['views']]})
 clips[name]={'label':name,'duration':duration,'mode':'loop' if name in ['Standing','Walking','Running','Dead'] else 'once','provenance':provenance[name],'anchors':anchors}
d={'revision':'m520_review_01','model':models[0]['url'],'default_model':'m520_a','default_clip':'Standing','model_sha256':models[0]['sha256'],'feedback':'feedback/user_feedback.json','models':models,'clips':clips}
(v/'manifest.json').write_text(json.dumps(d,indent=2)+'\n')
(v/'feedback').mkdir(exist_ok=True)
if not (v/'feedback/user_feedback.json').exists():(v/'feedback/user_feedback.json').write_text('{"findings": []}\n')
f=v/'index.html';s=f.read_text().replace('MM6 Cyclops','MM8 Cyclops').replace('Native armour and cleaver, eight animation roles, and three original palette variants.', 'Single-eye face study, heavy unarmed movement, native boulder throw and three palette variants.');f.write_text(s)
f=v/'review.js';s=f.read_text().replace('MM6 Ogre','MM8 Cyclops').replace('mm6:ogr','mm8:m520').replace('mm6_ogr_claude','mm8_m520_claude');f.write_text(s)
print('Viewer ready',len(models),len(clips))
