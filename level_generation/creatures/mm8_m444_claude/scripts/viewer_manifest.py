from pathlib import Path
import json,hashlib,struct
p=Path(__file__).resolve().parents[1];v=p/'review/viewer';raw=(p/'export/mm8_m444_lod0.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);dur={a['name']:max(d['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in d['animations']}
prov={'Standing':'Mixamo Standard Idle; native ready arms and fitted sword grip','Walking':'Mixamo Walk; upright sword carry','Running':'Mixamo Standard Run; source ankle trajectories and fitted carry','Attack':'Mixamo Sword And Shield Slash; upright steps, 1.283 s impact','Cast':'ArmedCastLAttack1; ready lead-in, left-palm release at 1.1167 s','Hit':'UnarmedGetHitF1; 0.5 s upright flinch','Death':'Mixamo Standing React Death Backward; hand clearance and grounded fall','Dead':'Final Death pose held','Fidget':'Authored quiet native ready-stance adjustment'}
frames={'Standing':['sa'],'Walking':['w'+c for c in 'abcdefgh'],'Running':['w'+c for c in 'abcdefgh'],'Attack':['a'+c for c in 'abcdefgh'],'Cast':['a'+c for c in 'abcdefgh'],'Hit':['n'+c for c in 'abcde'],'Death':['na','nb','da','db','dc','dd'],'Dead':['xa'],'Fidget':['f'+c for c in 'abcde']}
m={'revision':'mm8_m444_claude_v1','model':'mm8_m444_a.glb','default_model':'m444_a','default_clip':'Standing','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for tier,label in [('a','Animalist — green'),('b','Shapeshifter — blue'),('c','Lycanthrope — burgundy')]:
 f=v/f'mm8_m444_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();m['models'].append({'id':'m444_'+tier,'label':label,'revision':m['revision'],'url':f.name+'?v='+h[:12],'sha256':h})
m['model_sha256']=m['models'][0]['sha256']
for name,seconds in dur.items():
 fs=frames[name];m['clips'][name]={'label':name,'duration':seconds,'mode':'loop' if name in ['Standing','Walking','Running','Dead'] else 'once','provenance':prov[name],'anchors':[{'time':i*seconds/max(1,len(fs)-1),'label':stem,'phase':prov[name],'source_images':[f'../../../mm8_m444/native_variants/m444{stem}{view}_445.png' for view in range(5)]} for i,stem in enumerate(fs)]}
(v/'manifest.json').write_text(json.dumps(m,indent=2));print('VIEWER clips',dur)
