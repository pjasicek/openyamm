import json,struct,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer'
raw=(V/'mm8_dragon_hunter_a.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);dur={a['name']:max(d['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in d['animations']}
m={'revision':'mm8_dragon_hunter_v1','model':'mm8_dragon_hunter_a.glb','default_clip':'Standing','default_model':'dragon_hunter_a','models':[],'clips':{},'feedback':'feedback/user_feedback.json'}
for tier,color,label in [('a','Green','Dragon Hunter'),('b','Blue','Crusader'),('c','Burgundy','Dragonslayer')]:
 f=V/f'mm8_dragon_hunter_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();m['models'].append({'id':f'dragon_hunter_{tier}','label':f'{label} — {color}','url':f.name+'?v='+h[:12],'sha256':h,'revision':m['revision']})
m['model_sha256']=m['models'][0]['sha256']
for name,t in dur.items():m['clips'][name]={'label':name,'duration':t,'mode':'loop' if name in ['Standing','Walking','Running','Dead'] else 'once','provenance':'Fitted local library motion; native equipment and palettes.','anchors':[]}
(V/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
