import json,hashlib
from pathlib import Path
p=Path(__file__).resolve().parents[1];v=p/'review/viewer';f=v/'manifest.json';d=json.loads(f.read_text());info=json.loads((p/'export/export_info.json').read_text())
for model in d['models']:
 file=v/('mm6_'+model['id']+'.glb');sha=hashlib.sha256(file.read_bytes()).hexdigest();model.update(sha256=sha,url=file.name+'?v='+sha[:12])
d['model_sha256']=next(m['sha256'] for m in d['models'] if m['id']==d['default_model'])
for n,c in d['clips'].items():c['duration']=info['clips'][n]['duration']
d['revision']='mm6_mnk1_codex_review4'
for model in d['models']:model['revision']=d['revision']
updates={'Standing':'Review 4 rebake, preserved round 3: level folded forearms; tapered cloth sleeves, rounded overlapping hems and matched weave; hands enclosed.', 'Walking':'RelaxWalkForward with planted IK steps and 8.6 cm swing clearance; lower robe follows the thighs/shins; covered level fold retained.', 'Running':'Walking alias; covered level fold retained.', 'Fidget':'RelaxIdle hood glance with hands fully enclosed.', 'Hit':'UnarmedGetHitF1 torso reaction with the covered folded pose retained.', 'Death':'RelaxLaydownLayDown; library torso and timing retained; feet planted apart and back, smooth leg-driven robe and floor clearance.', 'Dead':'Exact final covered Death pose held.', 'Attack':'UnarmedCastDualAttack2; preserved palm release through forearm-following retracting cuff openings, sequential hand withdrawal and return into opposite sleeves.', 'Cast':'UnarmedCastDualAttack3; preserved palm release through the cuff openings and covered return.'}
for n,text in updates.items():
 d['clips'][n]['provenance']=text
 for anchor in d['clips'][n].get('anchors',[]):anchor['phase']=text
f.write_text(json.dumps(d,indent=2))

clipfile=p/"export/clip_manifest.json"
c=json.loads(clipfile.read_text());c["clips"]=info["clips"];c["revision"]=d["revision"];clipfile.write_text(json.dumps(c,indent=2))
