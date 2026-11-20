"""Append only this family's native-scale bindings; retain every unrelated actor entry."""
from pathlib import Path
import json,yaml,math,hashlib,shutil
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
measure=json.loads((P/'review/checks/assembly.json').read_text());height=measure['standing_body_height_m'];scale=197*1.299988/height
file=ROOT/'assets_dev/worlds/mm8/models/actors.yml';text=file.read_text() if file.exists() else 'actors:\n';existing=yaml.safe_load(text)['actors'];names={x['descriptor'] for x in existing};assert not names.intersection({'Salamander A','Salamander B','Salamander C'}),'Review existing bindings before replacing them'
entries=[]
for tier,speed in zip('ABC',[250,260,300]):
 entries.append({'descriptor':f'Salamander {tier}','model':'worlds/mm8/models/mm8_m568.glb','scale':scale,'yaw_offset':-math.pi/2,'skin':'m568_'+tier.lower(),'attachments':[{'model':'worlds/mm8/models/mm8_m568_polearm.glb','node':'Polearm'}], 'animation':{'cast':'Cast','run':'Running','stride_length':speed/scale,'run_stride_length':speed/scale*.75,'upper_body_root':'B_Pelvis','sockets':{'polearm_charge':{'node':'Polearm','offset':[0,.58,0]}},'events':{'attack_melee':{'impact':1.0},'attack_ranged':{'impact':1.0,'glow':['polearm_charge'],'release':'polearm_charge'},'cast':{'impact':1.0,'glow':['polearm_charge'],'release':'polearm_charge'}},'look':{'nodes':['B_Neck','B_Head'],'max_yaw_degrees':30,'max_pitch_degrees':20}},'clips':{'standing':'Standing','walking':'Walk','attack_melee':'Attack','attack_ranged':'Attack','hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}})
file.write_text(text.rstrip()+'\n\n# MM8 m568: native-sized serpent, fitted two-hand polearm and one-second release.\n'+yaml.safe_dump(entries,sort_keys=False))
assert len(yaml.safe_load(file.read_text())['actors'])==len(existing)+3
(P/'review/installed_bindings.json').write_text(json.dumps(entries,indent=2)+'\n')
for tier in 'abc':shutil.copyfile(P/f'review/viewer/mm8_m568_{tier}.glb',P/f'export/mm8_m568_portable_{tier}.glb')
print('BOUND',len(entries),'scale',scale,'native upright world height',197*1.299988)
