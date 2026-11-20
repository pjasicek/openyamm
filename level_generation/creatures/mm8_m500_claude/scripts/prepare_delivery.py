from pathlib import Path
import json,yaml,runpy,copy
p=Path('level_generation/creatures/mm8_m500_claude').resolve();root=p.parents[2];review=p/'review/ingame';review.mkdir(exist_ok=True)
parity=json.loads((p/'review/export_parity.json').read_text());height=parity['Standing']['mean_height_m'];scales=[164*s/height for s in [1.099991,1.399994,1.75]]
rows=[]
for i,c in enumerate('ABC'):
 rows.append({'descriptor':f'Water Elemental {c}','model':'worlds/mm8/models/mm8_m500.glb','scale':scales[i],'yaw_offset':-1.570796327,'skin':'water_'+c.lower(),'animation':{'cast':'Cast','run':'Running','stride_length':2.5065,'run_stride_length':1.671,'upper_body_root':'Spine_00','sockets':{'mouth':'Socket_Mouth','palm_left':'Socket_PalmL','palm_right':'Socket_PalmR'},'events':{'attack_melee':{'impact':.875},'cast':{'impact':.875,'glow':['palm_left','palm_right']}},'look':{'nodes':['Neck','Head'],'max_yaw_degrees':20,'max_pitch_degrees':10}},'clips':{'standing':'Standing','walking':'Walk','attack_melee':'Attack','attack_ranged':'Attack','hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}})
f=root/'assets_dev/worlds/mm8/models/actors.yml';existing=yaml.safe_load(f.read_text())['actors'];own=[r for r in existing if r['descriptor'].startswith('Water Elemental ')]
if own:assert own==rows,'Existing Water Elemental binding differs'
else:
 with f.open('a') as stream:stream.write(yaml.safe_dump(rows,sort_keys=False))
(p/'review/runtime_bindings.json').write_text(json.dumps({'native_standing_pixels':164,'mean_height_m':height,'bindings':rows},indent=2)+'\n')
s=(p.parent/'mm8_m524_claude/scripts/prepare_indoor_fixture.py').read_text().replace('m524','m500').replace('Serpentman','Water Elemental').replace('94,95,96','76,77,78')
(p/'scripts/prepare_indoor_fixture.py').write_text(s);runpy.run_path(str(p/'scripts/prepare_indoor_fixture.py'))
for scene in ['indoor','outdoor']:
 for kind in ['sprites','models']:
  src=p.parent/'mm8_m524_claude/review/ingame'/f'{scene}_{kind}_locked.yml';tour=yaml.safe_load(src.read_text());name=f'{scene}_{kind}'
  tour['output_dir']=str(review/name)
  for shot in tour['shots']:
   shot['commands']=[c.replace('actor spawn 94 ','actor spawn 76 ').replace('actor spawn 95 ','actor spawn 77 ').replace('actor spawn 96 ','actor spawn 78 ') for c in shot.get('commands',[])]
  if kind=='models':
   close=copy.deepcopy(tour['shots'][1]);close['name']='close';close['position'][0]-=160;close['commands']=['render lod 0'];tour['shots'].append(close)
   dead=copy.deepcopy(tour['shots'][0]);dead['name']='corpse';dead['commands']=['actor kill 900','render lod 0'];tour['shots'].append(dead)
  (review/f'{name}.yml').write_text(yaml.safe_dump(tour,sort_keys=False))
print('SCALES',scales)
