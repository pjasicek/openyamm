import json,hashlib,struct
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer';N=P.parent/'mm6_lch/native'
clips={
 'Standing':('loop','RelaxIdle; upright skeletal idle',['lchstda0','lchstda1','lchstda2']),
 'Walking':('loop','RelaxWalkForward; 5-degree shoulder clearance',[f'lchwlk{c}0' for c in 'abcdef']),
 'Attack':('once','DualAttack2; planted stance plus 20% discrete steps; right-palm release 0.729 s',[f'lchatk{c}0' for c in 'abcdef']),
 'Cast':('once','DualAttack1; open palms, discrete steps; left-palm release 0.625 s',[f'lchatk{c}0' for c in 'abcdef']),
 'Hit':('once','Front hit with upright planted legs; complete within the native 0.75 s',[f'lchwnc{c}0' for c in 'abcdef']),
 'Death':('once','Backward fall from UnarmedDeath1; crown stays attached',[f'lchdth{c}0' for c in 'abcde']),
 'Dead':('loop','Last Death pose held',['lchdthf0']),
 'Fidget':('once','RelaxDrink1 with open fingers: hand rises to the crown',[f'lchfgt{c}0' for c in 'abcdef'])}
raw=(V/'mm6_lch_a.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);dur={a['name']:max(doc['accessors'][s['input']]['max'][0] for s in a['samplers']) for a in doc['animations']}
m={'revision':'mm6_lch_codex_round2','model':'mm6_lch_a.glb','default_clip':'Standing','feedback':'feedback/user_feedback.json','default_model':'lch_a','models':[],'clips':{}}
for tier,label in [('a','Lich — silver-blue'),('b','Greater Lich — green'),('c','Power Lich — red')]:
 f=V/f'mm6_lch_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();m['models'].append({'id':f'lch_{tier}','label':label,'revision':m['revision'],'url':f.name+'?v='+h[:12],'sha256':h})
m['model_sha256']=m['models'][0]['sha256']
for name,(mode,provenance,frames) in clips.items():
 assert all((N/f'{f}.png').exists() for f in frames),(name,frames)
 m['clips'][name]={'label':name,'duration':dur[name],'mode':mode,'provenance':provenance,'anchors':[{'time':0.,'label':name,'phase':provenance,'source_images':[f'../../../mm6_lch/native/{f}.png' for f in frames]}]}
(V/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print('CLIPS',dur)
