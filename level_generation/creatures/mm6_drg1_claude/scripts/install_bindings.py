from pathlib import Path
import json
P=Path(__file__).resolve().parents[1];f=P.parents[2]/'assets_dev/worlds/mm6/models/actors.yml';s=f.read_text();assert '- descriptor: BDragonFly A' not in s;scale=json.loads((P/'review/scale.json').read_text())['world_scale']
s+='\n# MM6 Flying Drake: front-flight silhouette area fit; separate head/body/wing maps and shared tier ramps.\n'
for letter,tier in zip('ABC','abc'):
 s+=f'- descriptor: BDragonFly {letter}\n  model: worlds/mm6/models/mm6_drg1.glb\n  scale: {scale:.6f}\n  yaw_offset: -1.570796327\n  skin: drg1_{tier}\n  death_effect: {type: burn, start: 0.08, end: 1.5, char_width: 0.16, edge_width: 0.035, fire_width: 0.35, color: [1.0, 0.18, 0.02], brightness: 2.4, flames_per_second: 150, flame_size: 40, light: {color: [255, 150, 70], radius: 700}}\n'
 if letter!='A':s+='  scale_reference: BDragonFly A\n'
 s+='  animation:\n    cast: Cast\n    run: Running\n    stride_length: 1.0\n    upper_body_root: Spine1\n    blend_seconds: 0.4\n    death_blend_seconds: 0.3\n    sockets: {}\n    events:\n      attack_melee: {impact: 0.9375}\n      attack_ranged: {impact: 0.9375, launch_socket: Socket_Mouth}\n      cast: {impact: 0.9375, launch_socket: Socket_Mouth}\n  clips:\n    standing: Standing\n    walking: Walking\n    attack_melee: Attack\n    attack_ranged: Attack\n    hit: Hit\n    dying: Death\n    dead: Dead\n    fidget: Fidget\n'
f.write_text(s)
