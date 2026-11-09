from pathlib import Path
import json
P=Path(__file__).resolve().parents[1];f=P.parents[2]/'assets_dev/worlds/mm6/models/actors.yml';s=f.read_text();assert '- descriptor: DragonCover A' not in s;scale=json.loads((P/'review/scale.json').read_text())['world_scale']
s+='\n# MM6 Red/Blue/Gold Dragon: native flight-area scale, separate 2K body/head/wings.\n# Burning death as the native dragon: recoil and thrash aloft, then the burning body collapses flat to the ground.\n'
for letter,tier in zip('ABC','abc'):
 s+=f'- descriptor: DragonCover {letter}\n  model: worlds/mm6/models/mm6_cdr1.glb\n  scale: {scale:.6f}\n  yaw_offset: -1.570796327\n  skin: cdr1_{tier}\n  death_effect: {{type: burn, start: 0.05, end: 1.75, char_width: 0.16, edge_width: 0.035, fire_width: 0.45, color: [1.0, 0.26, 0.03], brightness: 2.4, flames_per_second: 170, flame_size: 34, light: {{color: [255, 160, 70], radius: 650}}}}\n'
 if letter!='A':s+='  scale_reference: DragonCover A\n'
 s+='  animation:\n    cast: Cast\n    run: Running\n    stride_length: 1.0\n    upper_body_root: Spine1\n    blend_seconds: 0.25\n    death_blend_seconds: 0.2\n    sockets: {}\n    events:\n      attack_melee: {impact: 0.65625}\n      attack_ranged: {impact: 0.65625, launch_socket: Socket_Mouth}\n      cast: {impact: 0.65625, launch_socket: Socket_Mouth}\n  clips:\n    standing: Standing\n    walking: Walking\n    attack_melee: Attack\n    attack_ranged: Attack\n    hit: Hit\n    dying: Death\n    dead: Dead\n    fidget: Fidget\n'
f.write_text(s)
