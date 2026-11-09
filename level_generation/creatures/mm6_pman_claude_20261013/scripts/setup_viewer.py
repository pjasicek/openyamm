from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parents[1];V=P/'review/viewer';info=json.loads((P/'export/export_info.json').read_text());revision='pman_v2_forearms_20261013'
models=[]
for tier,label in [('a','Peasant A · green'),('b','Peasant B · charcoal'),('c','Peasant C · red')]:
 f=V/f'mm6_pman_{tier}.glb';models.append({'id':f'pman_{tier}','label':label,'revision':revision,'url':f.name+'?v='+revision,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
provenance={'Standing':'Mixamo Standard Idle · relaxed breathing; 3 s','Walking':'Mixamo Standard Walk · upright civilian walk; also used for this slow civilian’s flee state','Hit':'Humanoid set UnarmedGetHitF1 · upper-body recoil fitted to the standing legs, with blended endpoints','Fidget':'Mixamo Neck Stretching · upright neck and shoulder stretch','Death':'Humanoid set UnarmedDeath1 · full-body fall with floor contact','Dead':'Held final Death pose'}
refs={'Standing':'standing','Walking':'walk_0','Hit':'hit','Fidget':'fidget','Death':'death_corpse','Dead':'death_corpse'}
clips={n:{'label':n,'duration':d,'mode':'loop' if n in ['Standing','Walking'] else 'once','provenance':provenance[n],'anchors':[{'time':0,'label':'Native reference','phase':n,'source_images':['../../../mm6_pman/references/'+refs[n]+'.png']}]} for n,d in info['clips'].items()}
(V/'manifest.json').write_text(json.dumps({'revision':revision,'model':models[0]['url'],'model_sha256':models[0]['sha256'],'default_model':'pman_a','default_clip':'Standing','models':models,'clips':clips,'feedback':'feedback/user_feedback.json'},indent=2))
f=V/'index.html';s=f.read_text().replace('value="48">48 fps','value="30">30 fps').replace('value="192">192 fps','value="120">120 fps');f.write_text(s)
f=V/'review.js';s=f.read_text().replace('model=gltf.scene;model.animations=', 'model=gltf.scene;model.traverse(o=>{if(o.isSkinnedMesh)o.frustumCulled=false;});model.animations=');f.write_text(s)
