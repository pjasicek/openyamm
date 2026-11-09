from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parents[1];v=P/'review/viewer';m=json.loads((P/'review/clay_manifest.json').read_text());info=json.loads((P/'export/export_info.json').read_text());models=[]
for tier,label in [('a','Dark Elven Warrior'),('b','Dark Elven Defender'),('c','Dark Elven Crusader')]:
 path=v/f'mm8_m432_{tier}.glb';h=hashlib.sha256(path.read_bytes()).hexdigest();models.append({'id':f'm432_{tier}','label':label,'revision':'m432_v1','url':path.name+'?v='+h[:12],'sha256':h})
m.update(revision='m432_v1',model='mm8_m432_a.glb',model_sha256=models[0]['sha256'],default_model='m432_a',models=models)
for name,c in m['clips'].items():c['duration']=info['clips'][name]
(v/'manifest.json').write_text(json.dumps(m,indent=1)+'\n')
