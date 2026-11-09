from pathlib import Path
import json,yaml
p=Path('level_generation/creatures/mm8_m404/3d_claude')
info=json.loads((p/'export/export_info.json').read_text());walk=json.loads((p/'work/walk_fit.json').read_text())
scale=200/info['visible_standing_height_m']
entries=[]
for tier in 'ABC':
 entry={'descriptor':f'Lizardmen Warrior {tier}','model':'worlds/mm8/models/mm8_m404.glb','scale':scale,
        'yaw_offset':-1.570796327,'skin':'m404_'+tier.lower(),
        'attachments':[{'model':'worlds/mm8/models/mm8_m404_sword.glb','node':'Socket_Sword'}],
        'animation':{'run':'Walking','stride_length':walk['stride_length_m'],
            'run_stride_length':walk['stride_length_m'],'upper_body_root':'B_Spine',
            'sockets':{'palm_right':'B_R_Hand'},
            'events':{'attack_melee':{'impact':.6354166666666666},
                      'attack_ranged':{'impact':.6354166666666666,'release':'palm_right'}},
            'look':{'nodes':['B_Neck','B_Head'],'max_yaw_degrees':25,'max_pitch_degrees':15}},
        'clips':{'standing':'Standing','walking':'Walking','attack_melee':'Attack','attack_ranged':'Attack2',
                 'hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'}}
 entries.append(entry)
path=Path('assets_dev/worlds/mm8/models/actors.yml');existing=path.read_text();doc=yaml.safe_load(existing)
assert not {e['descriptor'] for e in entries}&{e['descriptor'] for e in doc['actors']}
addition='\n# MM8 m404: palettes 405/406/407 share native size, one rig and one rigid wavy sword.\n'
addition+=yaml.safe_dump(entries,sort_keys=False,width=110)
with path.open('a') as stream:stream.write(addition)
print('BOUND',scale,'stride',walk['stride_length_m'])
