"""Bind the one native grey palette at the three measured sprite sizes; do not edit gameplay data."""
import copy,json,yaml
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
motion=json.loads((P/'work/animated_motion.json').read_text());height=sum(motion['Standing']['height_range'])/2;scale=163/height
bindings=[]
for tier in 'abc':
 entry={'descriptor':'Malevolent Boulder '+tier.upper(),'model':'worlds/mm8/models/mm8_m588.glb','scale':scale,'yaw_offset':-1.570796327,'skin':'boulder_'+tier}
 if tier!='a':entry['scale_reference']='Malevolent Boulder A'
 entry['animation']={'cast':'Cast','run':'Walking','stride_length':2.4,'run_stride_length':2.4,'upper_body_root':'Core','sockets':{'mouth':'Socket_Mouth'},'events':{'attack_melee':{'impact':1.0},'attack_ranged':{'impact':1.0,'glow':['mouth'],'release':'mouth','color':[255,231,165],'glow_scale':.7},'cast':{'impact':1.0,'glow':['mouth'],'release':'mouth','color':[255,231,165],'glow_scale':.85}}}
 entry['clips']={'standing':'Standing','walking':'Walking','attack_melee':'Attack','attack_ranged':'Attack','hit':'Hit','dying':'Death','dead':'Dead','fidget':'Standing'}
 bindings.append(entry)
text=yaml.safe_dump(bindings,sort_keys=False)
(P/'export/actor_bindings.yml').write_text(text)
path=R/'assets_dev/worlds/mm8/models/actors.yml';source=path.read_text()
assert not any(x['descriptor'].startswith('Malevolent Boulder') for x in yaml.safe_load(source)['actors'])
path.write_text(source.rstrip()+'\n# Malevolent Boulder m588: shared palette 588, native size tiers and mouth launch.\n'+text)
(P/'work/placement.json').write_text(json.dumps({'standing_pixels':163,'standing_width_pixels':210,'standing_height_m':height,'scale':scale,'tier_frame_scale':[1,1.299988,1.699997],'impact_seconds':1.0},indent=2)+'\n')
print('BOUND',scale)
