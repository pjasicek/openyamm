import json,struct,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer'
raw=(V/'mm8_pirate_a.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);dur={a['name']:max(d['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in d['animations']}
m={'revision':'mm8_pirate_v1','model':'mm8_pirate_a.glb','default_clip':'Standing','default_model':'pirate_a','models':[],'clips':{},'feedback':'feedback/user_feedback.json'}
for tier,color in [('a','Green'),('b','Blue'),('c','Red')]:
 f=V/f'mm8_pirate_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();m['models'].append({'id':f'pirate_{tier}','label':f'Pirate {tier.upper()} — {color}','url':f.name+'?v='+h[:12],'sha256':h,'revision':m['revision']})
m['model_sha256']=m['models'][0]['sha256']
for name,t in dur.items():m['clips'][name]={'label':name,'duration':t,'mode':'loop' if name in ['Standing','Walking','Running','Dead'] else 'once','provenance':'Fitted local library motion; native equipment and palettes.','anchors':[]}
refs={'Standing':'Sa','Walking':'Wa','Running':'Wa','Attack':'Aa','Hit':'Na','Death':'Da','Dead':'Df','Fidget':'Fa'}
for name,group in refs.items():
 images=['../../references/native_png/m412'+group+str(v)+'.png' for v in range(5) if (P/'references/native_png'/('m412'+group+str(v)+'.png')).exists()]
 m['clips'][name]['anchors']=[] if not images else [{'time':0,'label':'Original sprite','phase':'Native identity reference; the fitted animation keeps its authored timing.','source_images':images}]
(V/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
