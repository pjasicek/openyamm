"""Install the selected model and append only its three descriptor bindings."""
from pathlib import Path
import json,yaml,subprocess,sys,hashlib
P=Path(__file__).resolve().parents[1];R=P.parents[2]
source=P/'export/mm8_m608.glb';assert json.loads((P/'work/export_audit.json').read_text())['export_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(R/'tools/install_model.py'),str(source),'--world','mm8'],check=True)
entries=[]
for tier in 'abc':
 entries.append({'descriptor':'Juggernaut '+tier.upper(),'model':'worlds/mm8/models/mm8_m608.glb','scale':398.0,'yaw_offset':-1.570796327,'skin':'m608_'+tier,'animation':{'run':'Walking','stride_length':1.11,'run_stride_length':1.11,'upper_body_root':'Waist','look':{'nodes':['Head'],'max_yaw_degrees':25,'max_pitch_degrees':15},'sockets':{'palm_left':'Socket_Palm_Left','palm_right':'Socket_Palm_Right','eye_left':'Socket_Eye_Left','eye_right':'Socket_Eye_Right'},'eye_color':[255,238,110],'events':{'attack_melee':{'impact':1.0}}},'clips':{'standing':'Standing','walking':'Walking','attack_melee':'Attack','attack_ranged':'Attack','hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}})
manifest=R/'assets_dev/worlds/mm8/models/actors.yml';original=manifest.read_text();before=yaml.safe_load(original);names={e['descriptor'] for e in entries};existing=[e for e in before['actors'] if e['descriptor'] in names]
if existing:
 assert existing==entries,'Existing Juggernaut bindings differ; review before replacing them'
else:
 with manifest.open('a') as stream:stream.write('\n'+yaml.safe_dump(entries,sort_keys=False))
after=yaml.safe_load(manifest.read_text());assert [e for e in after['actors'] if e['descriptor'] not in names]==[e for e in before['actors'] if e['descriptor'] not in names]
(P/'integration').mkdir(exist_ok=True);(P/'integration/actors.yml').write_text(yaml.safe_dump({'actors':entries},sort_keys=False))
paths=[source,R/'assets_source/worlds/mm8/models/mm8_m608.glb',R/'assets_dev/worlds/mm8/models/mm8_m608.glb']
(P/'integration/install_receipt.json').write_text(json.dumps([{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths],indent=2))
assert paths[0].read_bytes()==paths[1].read_bytes()
print('INSTALLED_JUGGERNAUT',flush=True)
