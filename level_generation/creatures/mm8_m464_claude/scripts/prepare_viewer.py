import runpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];runpy.run_path(str(P/'scripts/viewer_tiers.py'),run_name='__main__');durations=json.loads((P/'export/export_info.json').read_text())['durations'];models=[]
for v,label in zip('abc',['A · green / auburn','B · purple / blonde','C · red / black']):
 f=P/f'review/viewer/mm8_m464_{v}.glb';sha=hashlib.sha256(f.read_bytes()).hexdigest();models.append({'id':f'm464_{v}','label':label,'url':f.name+'?v='+sha[:12],'revision':'v2-arms','sha256':sha})
keys={'Standing':'s','Walking':'w','Running':'w','Hit':'n','Fidget':'f','Death':'d','Dead':'x'}
m={'revision':'v2-arms','model':'MM8 Vampire Female Peasant','default_clip':'Standing','default_model':'m464_a','feedback':'../feedback/user_feedback.json','models':models,'clips':{role:{'label':role,'duration':duration,'mode':'loop'if role in ['Standing','Walking','Running']else'once','provenance':'Accepted F3 rig/motion adapted to native unarmed peasant posture. Native attacks use Walking.','anchors':[{'time':0,'label':'Native','phase':'reference','source_images':[f'../../references/native_m465{keys[role]}.png']}]}for role,duration in durations.items()}}
(P/'review/viewer/manifest.json').write_text(json.dumps(m,indent=2))
