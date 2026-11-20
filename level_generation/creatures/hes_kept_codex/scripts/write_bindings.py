"""Eight-state Kept bindings, with the actual measured source-rate strides and strikes."""
from pathlib import Path
import json,yaml
P=Path(__file__).resolve().parents[1];rows=[]
for descriptor,code,style,tier,armed,props in [('Kept Labourer','m','ragged','a',False,['collar']),('Kept Miner','m','ragged','b',True,['collar','pick']),('Kept Enforcer','m','enforcer','c',True,['collar','club']),('Freed Kept Male','m','freed',None,False,[]),('Freed Kept Female','f','freed',None,False,[])]:
 kind='male' if code=='m' else 'female';s=json.loads((P/'review'/kind/'stride.json').read_text());height=1.70082656 if code=='m' else 1.7012694
 def clip(role):return 'Kept_ClubAttack' if tier=='c' and role=='Attack' else 'Kept_'+('MaceAttack' if role=='Attack' else 'Armed'+role) if armed else 'Kept_'+role
 impact=.3166666667 if tier=='c' else .2833333333 if armed else .3333333333
 row={'descriptor':descriptor,'model':f'worlds/hesper/models/hes_kept_{code}_{style}.glb','scale':round((175 if code=='m' else 168)/height,7),'yaw_offset':-1.570796327,'animation':{'run':clip('Running'),'stride_length':s['Kept_Walking']['stride_m'],'run_stride_length':s['Kept_Running']['stride_m'],'upper_body_root':'B_Spine','events':{'attack_melee':{'impact':impact},'attack_ranged':{'impact':impact}}},'clips':{role:clip(c) for role,c in [('standing','Standing'),('walking','Walking'),('attack_melee','Attack'),('attack_ranged','Attack'),('hit','Hit'),('dying','Death'),('dead','Dead'),('fidget','Fidget')]}}
 if tier:row['skin']='kept_'+tier
 if props:row['attachments']=[{'model':f'worlds/hesper/models/hes_kept_{p}.glb','node':'Kept_'+p.capitalize()} for p in props]
 rows.append(row)
(P/'integration/actors.yml').write_text('# Kept production exports, staged only. Ranged role explicitly aliases melee; these rows have no ranged attack.\n'+yaml.safe_dump(rows,sort_keys=False))
