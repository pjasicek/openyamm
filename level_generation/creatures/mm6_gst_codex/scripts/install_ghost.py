from pathlib import Path
import json,subprocess,sys
P=Path(__file__).resolve().parents[1];root=P.parents[2];f=root/'assets_dev/worlds/mm6/models/actors.yml';s=f.read_text();assert '- descriptor: BGhost A' not in s
subprocess.run([sys.executable,'tools/install_model.py',str(P/'export/mm6_gst.glb'),'--world','mm6'],check=True)
scale=json.loads((P/'export/export_info.json').read_text())['binding_scale'];s+='\n# MM6 Ghost: native 241 visible px x 0.7; shared tabard/bone/eye palette ramps.\n'
for letter,tier,color in zip('ABC','abc',[[165,248,99],[13,70,186],[248,1,0]]):
 s+=f"- descriptor: BGhost {letter}\n  model: worlds/mm6/models/mm6_gst.glb\n  scale: {scale:.7f}\n"
 if letter!='A':s+='  scale_reference: BGhost A\n'
 s+=f"  yaw_offset: -1.570796327\n  skin: gst_{tier}\n  animation:\n    cast: Attack\n    eye_color: {color}\n"
 s+='    run: Running\n    stride_length: 2.05\n    upper_body_root: B_Spine\n    look:\n      nodes: [B_Neck, B_Head]\n      max_yaw_degrees: 35\n      max_pitch_degrees: 25\n    sockets:\n      eye_left: Socket_Eye_Left\n      eye_right: Socket_Eye_Right\n      palm_left: Socket_Palm_Left\n      palm_right: Socket_Palm_Right\n    events:\n      attack_melee: {impact: 0.75}\n  clips:\n    standing: Standing\n    walking: Walking\n    attack_melee: Attack\n    attack_ranged: Attack\n    hit: Hit\n    dying: Death\n    dead: Dead\n    fidget: Fidget\n'
f.write_text(s)
