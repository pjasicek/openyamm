"""Append native-scale Thunder Lizard bindings without rewriting other families."""
from pathlib import Path
import json,yaml,math,shutil
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
height=json.loads((P/'review/checks/assembly.json').read_text())['standing_body_height_m'];scale=158/height
file=ROOT/'assets_dev/worlds/mm8/models/actors.yml';text=file.read_text();existing=yaml.safe_load(text)['actors'];names={x['descriptor'] for x in existing};assert not names.intersection({'Thunder Lizard A','Thunder Lizard B','Thunder Lizard C'})
entries=[]
for tier in 'ABC':
 entries.append({'descriptor':f'Thunder Lizard {tier}','model':'worlds/mm8/models/mm8_m516.glb','scale':scale,'yaw_offset':-math.pi/2,'skin':'m516_'+tier.lower(),'animation':{'cast':'Attack','run':'Running','stride_length':1.0,'run_stride_length':1.8,'upper_body_root':'Hips','events':{'attack_melee':{'impact':1.0},'attack_ranged':{'impact':1.0}},'look':{'nodes':['Neck1','Neck2','Head'],'max_yaw_degrees':25,'max_pitch_degrees':15}},'clips':{'standing':'Standing','walking':'Walking','attack_melee':'Attack','attack_ranged':'Attack','hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}})
file.write_text(text.rstrip()+'\n\n# MM8 m516: native-sized biped with grounded strides and tail counterbalance.\n'+yaml.safe_dump(entries,sort_keys=False));assert len(yaml.safe_load(file.read_text())['actors'])==len(existing)+3
(P/'review/installed_bindings.json').write_text(json.dumps(entries,indent=2)+'\n')
for tier in 'abc':shutil.copyfile(P/f'review/viewer/mm8_m516_{tier}.glb',P/f'export/mm8_m516_portable_{tier}.glb')
print('BOUND',len(entries),'scale',scale,'native upright world height',158)
