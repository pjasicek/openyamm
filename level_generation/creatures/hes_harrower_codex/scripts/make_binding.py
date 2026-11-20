from pathlib import Path
import json,yaml,copy
P=Path(__file__).resolve().parents[1]
metrics=json.loads((P/'review/binding_metrics.json').read_text())
rows=[]
for suffix,label,scale in [('a','Harrower A',1),('b','Harrower B',1.05),('c','Harrower C',1.1),('boss','Huntmaster Vreth',1.35)]:
 prefix='hes_vreth' if suffix=='boss' else 'hes_harrower'
 items=[(prefix+'_blade_l','Blade_L'),(prefix+'_blade_r','Blade_R'),(prefix+'_crest','Harrower_Crest')]
 if suffix in ('b','boss'):items.append((prefix+'_trophies','Harrower_Trophies'))
 if suffix in ('c','boss'):items += [('hes_harrower_cap_'+s.lower(),'B_'+s+'_Pauldron') for s in 'LR']
 animation={'run':'Harrower_Running','stride_length':metrics['walk_stride_m'],'run_stride_length':metrics['run_stride_m'],'upper_body_root':'B_Spine','script_clips':{'frenzy':'Harrower_Roar','spent':'Harrower_Spent','charge_strike':'Harrower_ChargeStrike'},'events':{'attack_melee':{'impact':metrics['attack_impact_s']},'attack_ranged':{'impact':metrics['attack2_impact_s']}}}
 # Fixed head pose avoids adding unaudited additive look rotations to the crest and blade clearance gate.
 clips={k:'Harrower_'+v for k,v in {'standing':'Standing','walking':'Walking','attack_melee':'Attack','attack_ranged':'Attack2','hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}.items()}
 rows.append({'descriptor':label,'model':'worlds/hesper/models/hes_harrower.glb','skin':'hhw_'+suffix,'scale':round(104.8623316*scale,8),'yaw_offset':-1.570796327,'animation':animation,'clips':clips,'attachments':[{'model':'worlds/hesper/models/'+name+'.glb','node':node} for name,node in items]})
text='# Hesper Harrowers: shared thin body, skin-coloured sculpted harness and original tail.\n# Four region-ramp variants; twelve bound Harrower motions, eighteen unbound original compatibility clips.\n# Attack, Attack2 and the charge strike: local humanoid set clips (2026-10-24, scripts/run_cands.sh).\n# Run: local Mixamo Standard Run. Strides and impact times: review/binding_metrics.json.\n# Staging only; no assets_dev or installed MM6 modifications.\n'
(P/'integration/actors.yml').write_text(text+yaml.safe_dump(rows,sort_keys=False))
assert len(yaml.safe_load((P/'integration/actors.yml').read_text()))==4
