from pathlib import Path
import json,subprocess,sys
P=Path(__file__).resolve().parents[1];root=P.parents[2];f=root/'assets_dev/worlds/mm6/models/actors.yml';s=f.read_text();assert '- descriptor: ElemWater A' not in s
for name in ['mm6_wel','mm6_wel_trident']:
 subprocess.run([sys.executable,'tools/install_model.py',str(P/'export'/f'{name}.glb'),'--world','mm6'],check=True)
scale=json.loads((P/'export/export_info.json').read_text())['binding_scale'];s+='\n# MM6 Water Beast / Water Spirit / Water Elemental: 216 native visible pixels x 0.9.\n'
for letter,tier in zip('ABC','abc'):
 s+=f"- descriptor: ElemWater {letter}\n  model: worlds/mm6/models/mm6_wel.glb\n  scale: {scale:.7f}\n"
 if letter!='A':s+='  scale_reference: ElemWater A\n'
 s+=f"  yaw_offset: -1.570796327\n  skin: wel_{tier}\n  animation:\n    cast: Cast\n    run: Running\n    stride_length: 3.08\n    upper_body_root: B_Spine\n    look:\n      nodes: [B_Neck, B_Head]\n      max_yaw_degrees: 30\n      max_pitch_degrees: 18\n    sockets:\n      eye_left: Socket_Eye_Left\n      eye_right: Socket_Eye_Right\n      palm_left: Socket_Palm_Left\n      palm_right: Socket_Palm_Right\n    events:\n      attack_melee: {{impact: 1.02}}\n      attack_ranged: {{impact: 1.02, launch_socket: Socket_Trident_Head}}\n      cast: {{impact: 1.02, launch_socket: Socket_Trident_Head}}\n  clips:\n    standing: Standing\n    walking: Walking\n    attack_melee: Attack\n    attack_ranged: Attack\n    hit: Hit\n    dying: Death\n    dead: Dead\n    fidget: Fidget\n  attachments:\n  - model: worlds/mm6/models/mm6_wel_trident.glb\n    node: Trident\n"
f.write_text(s)
