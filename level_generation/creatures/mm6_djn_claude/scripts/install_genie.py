from pathlib import Path
import shutil,json
P=Path(__file__).resolve().parents[1];root=P.parents[2];dest=root/'assets_dev/worlds/mm6/models';shutil.copy2(P/'export/mm6_djn.glb',dest/'mm6_djn.glb');f=dest/'actors.yml';s=f.read_text();assert '- descriptor: BGenie A' not in s
s+='\n# MM6 Genie: native 199 px stand x 0.8 / 2.208 m; shared palette ramps and floating vortex.\n'
for letter,tier in zip('ABC','abc'):
 s+=f"- descriptor: BGenie {letter}\n  model: worlds/mm6/models/mm6_djn.glb\n  scale: 72.1\n"
 if letter!='A':s+='  scale_reference: BGenie A\n'
 s+=f"  yaw_offset: -1.570796327\n  skin: djn_{tier}\n"
 s+='  animation:\n    cast: Cast\n    cast_color: [235, 245, 255]\n    cast_glow_scale: 0.3\n    cast_focus_socket: Socket_Palm_Right\n    cast_focus_glow_scale: 0.3\n    run: Running\n    stride_length: 1.65\n    upper_body_root: B_Pelvis\n    look:\n      nodes: [B_Neck, B_Head]\n      max_yaw_degrees: 35\n      max_pitch_degrees: 25\n    sockets:\n      eye_left: Socket_Eye_Left\n      eye_right: Socket_Eye_Right\n      palm_left: Socket_Palm_Left\n      palm_right: Socket_Palm_Right\n    ranged_hand_effects:\n      Water: openyamm:fx/creature_air_staff\n      Air: openyamm:fx/creature_air_staff\n      Fire: openyamm:fx/creature_air_staff\n    ranged_hand_sockets: [Socket_Palm_Left, Socket_Palm_Right]\n    events:\n      attack_melee: {impact: 0.78}\n      attack_ranged: {impact: 0.78, launch_socket: Socket_Palm_Right}\n      cast: {impact: 0.78, launch_socket: Socket_Palm_Right}\n  clips:\n    standing: Standing\n    walking: Walking\n    attack_melee: Attack\n    attack_ranged: Attack\n    hit: Hit\n    dying: Death\n    dead: Dead\n    fidget: Fidget\n'
f.write_text(s)
