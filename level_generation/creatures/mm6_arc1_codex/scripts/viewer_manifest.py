import json,struct,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];V=P/'review/viewer';raw=(V/'mm6_arc1_a.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+n]);dur={a['name']:max(d['accessors'][s['input']]['max'][0]for s in a['samplers'])for a in d['animations']}
provenance={'Standing':'Review 5: native upright rest; mirrored hanging arm, forward bow 18 degrees above horizontal, string toward the arm; flat soles; calm breathing','Walking':'Humanoid set 2HandBowWalk; relaxed side carry and rest boundary blends','Attack':'Mixamo Standing Draw Arrow + Standing Aim Recoil; fixed flat ankle anchors with reach-constrained pelvis; arrow release 0.800 s; Review 6 speed 1.5x','Cast':'Exact Attack bow shot copy; Fire Archer fireball replaces arrow; release 0.800 s; Review 6 speed 1.5x','Hit':'Humanoid set 2HandBowGetHitF1; full clip within native 0.625 s','Death':'Humanoid set 2HandBowDeath1; bow/hand ground clearance fitted','Dead':'Last Death pose held','Fidget':'Review 5: relaxed glance and small weight shift; planted soles; returns to rest'}
frames={'Standing':['arc1sta0','arc1sta2','arc1sta4'],'Walking':['arc1wka0','arc1wkb0','arc1wkc0'],'Attack':['arc1fia0','arc1atl','arc1atm','arc1atn','arc1ato','arc1atp'],'Cast':['arc1fia0','arc1atl','arc1atm','arc1atn','arc1ato','arc1atp'],'Hit':['arc1wif','arc1wig','arc1wih'],'Death':['arc1diq','arc1dir','arc1dis','arc1dit','arc1diu'],'Dead':['arc1div'],'Fidget':['arc1fia0','arc1fib0']}
m={'revision':'mm6_arc1_codex_review6','model':'mm6_arc1_a.glb','default_clip':'Standing','default_model':'arc1_a','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for tier,label in [('a','Archer — blue'),('b','Master Archer — red'),('c','Fire Archer — green')]:
 f=V/f'mm6_arc1_{tier}.glb';h=hashlib.sha256(f.read_bytes()).hexdigest();m['models'].append({'id':f'arc1_{tier}','label':label,'revision':m['revision'],'url':f.name+'?v='+h[:12],'sha256':h})
m['model_sha256']=m['models'][0]['sha256']
for name,seconds in dur.items():
 source=[f'../../../mm6_arc1/native/{f}.png'for f in frames[name]if(P.parent/'mm6_arc1/native'/f'{f}.png').exists()];assert source,name
 m['clips'][name]={'label':name,'duration':seconds,'mode':'loop'if name in ['Standing','Walking','Dead']else'once','provenance':provenance[name],'anchors':[{'time':0.,'label':name,'phase':provenance[name],'source_images':source}]}
(V/'manifest.json').write_text(json.dumps(m,indent=2));print('VIEWER clips',dur)
