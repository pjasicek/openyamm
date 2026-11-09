"""Install the equal native-size Triton tiers without changing combat tables or other model bindings."""
from pathlib import Path
import json,yaml
P=Path(__file__).resolve().parents[1];repo=P.parents[2];path=repo/'assets_dev/worlds/mm8/models/actors.yml';doc=yaml.safe_load(path.read_text());scale=json.loads((P/'work/scale.json').read_text())['scale'];strides=json.loads((P/'work/stride_lengths.json').read_text());entries=doc['actors'] if isinstance(doc,dict) else doc
assert all(not e['descriptor'].startswith('Triton ') for e in entries),'Triton bindings already exist; inspect before updating'
rows=[]
for tier in 'abc':
 rows.append({'descriptor':'Triton '+tier.upper(),'model':'worlds/mm8/models/mm8_m576.glb','scale':scale,'yaw_offset':-1.570796327,'skin':'triton_'+tier,'attachments':[{'model':'worlds/mm8/models/mm8_m576_trident.glb','node':'Trident'}],'animation':{'run':'Running','stride_length':strides['Walking']['stride_m'],'run_stride_length':strides['Running']['stride_m'],'upper_body_root':'B_Spine','events':{'attack_melee':{'impact':1.0},'attack_ranged':{'impact':1.0}},'look':{'nodes':['B_Neck','B_Head'],'max_yaw_degrees':25,'max_pitch_degrees':15}},'clips':{'standing':'Standing','walking':'Walking','attack_melee':'Attack','attack_ranged':'Attack','hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}})
# Append this creature's entries to preserve the exact formatting of concurrent creature work.
text=yaml.safe_dump(rows,sort_keys=False,width=120);path.write_text(path.read_text().rstrip()+'\n'+text)
check=yaml.safe_load(path.read_text());entries=check['actors'] if isinstance(check,dict) else check
assert sum(e['descriptor'].startswith('Triton ') for e in entries)==3
(P/'review/runtime_bindings.json').write_text(json.dumps(rows,indent=2)+'\n')
