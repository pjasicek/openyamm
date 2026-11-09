from pathlib import Path
import json,struct,hashlib
p=Path(__file__).resolve().parents[1];v=p/'review/viewer';native=p.parent/'mm6_sor1/native'
raw=(v/'mm6_sor1_c.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);dur={a['name']:max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
patterns={'Standing':['sor1sta'],'Walking':['sor1wk'+a for a in 'abcdef'],'Attack':['sor1at'+a for a in 'abcdef'],'Cast':['sor1at'+a for a in 'abcdef'],'Hit':['sor1wi'+a for a in 'abcdef'],'Death':['sor1dy'+a for a in 'abcdef'],'Dead':['sor1dyf'],'Fidget':['sor1fi'+a for a in 'abcdef']}
provenance={'Standing':'Upright Relax idle; relaxed free arm beside the body and retained right-hand staff grip.','Walking':'Relax forward walk; anatomically hinged free arm and narrowed robe drape.','Attack':'Spear Attack1 torso motion with fitted opposing grips, smoothed poles, a planted 280 mm step and forward weight transfer; staff-head projectile release.','Cast':'Whole-body staff cast based on Mixamo Standing 2H Magic Attack 01; discrete step, free-hand gesture, staff-head launch.','Hit':'Full-body recoil: staff and both arms react, knees bend and the hem follows; 0.75 seconds.','Death':'Adapted backward fall, retained staff; robe drapes over the shoes.','Dead':'Final Death pose held. Native corpse is more tightly curled.','Fidget':'Left hand to chin, staff tilts and settles, with a small weight shift; adapted from Relax drink without a cup.'}
m={'revision':'mm6_sor1_codex_review4','default_model':'sor1_c','default_clip':'Standing','model':'mm6_sor1_c.glb','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for tier,label in [('a','Sorcerer A — black / olive'),('b','Magician B — red'),('c','Warlock C — purple')]:
 f=v/f'mm6_sor1_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();m['models'].append({'id':f'sor1_{tier}','label':label,'revision':m['revision'],'url':f.name+'?v='+h[:12],'sha256':h})
m['model_sha256']=m['models'][2]['sha256']
for name,patterns_ in patterns.items():
 anchors=[]
 for i,pat in enumerate(patterns_):
  images=[f'../../../mm6_sor1/native/{pat}{j}.png' for j in range(5) if (native/f'{pat}{j}.png').exists()]
  assert images,(name,pat)
  anchors.append({'time':dur[name]*i/max(1,len(patterns_)-1),'label':pat,'phase':'Native pose reference; adapted 3D timing','source_images':images})
 m['clips'][name]={'label':name,'duration':dur[name],'mode':'loop' if name in ['Standing','Walking','Dead'] else 'once','provenance':provenance[name],'anchors':anchors}
(v/'manifest.json').write_text(json.dumps(m,indent=2));print('MANIFEST',dur)
