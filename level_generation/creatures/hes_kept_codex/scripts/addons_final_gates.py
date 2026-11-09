from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parents[1]
read=lambda p:json.loads((P/p).read_text())
contacts=read('review/addons_v2/contact_probe.json');stretch=read('review/addons_v2/attack_stretch.json');joints=read('review/addons_v2/joint_gate.json');jerk=read('review/addons_v2/jerk.json');deform=read('review/addons_v2/attack_deformation.json')
assert len(contacts)==17
assert all(d['skin_depth_m']<.0001 for r in contacts.values()for d in r['props'].values())
assert all(r['arm_p99_pass'] and r['hand_max_pass']for r in stretch['clips'].values())
assert joints['pass'] and jerk['pass'] and deform['pass']
report={'pass':True,'source':'work/addons_v2/equipped.blend','source_sha256':hashlib.sha256((P/'work/addons_v2/equipped.blend').read_bytes()).hexdigest(),'selected_attack':'Kept_ClubR1 / local MaceAttackR1; exported as Kept_ClubAttack','impact_seconds':9.5/30,'clip_count':17,'closed_skin_penetration_max_m':max(d['skin_depth_m']for r in contacts.values()for d in r['props'].values()),'contact_test':'half-frame full props: vertices, edge midpoints, face centroids; closed topology asserted, three ray directions and solid-angle confirmation','open_shirt_proximity':'Recorded separately; plate and straps intentionally cover the open shirt. Front/back/attack/fall CPU renders required.','arm_p99_max':max(v['p99']for r in stretch['clips'].values()for n,v in r['regions'].items()if n.endswith('arm')),'hand_stretch_max':max(v['max']for r in stretch['clips'].values()for n,v in r['regions'].items()if n.endswith('hand')),'joints':joints['pass'],'new_attack_jerk':jerk['pass'],'new_attack_deformation':deform['pass'],'freed_exports_unchanged':{}}
for stem in ('hes_kept_m_freed','hes_kept_f_freed'):
 before=hashlib.sha256((P/'work/addons_v2/baseline'/f'{stem}.glb').read_bytes()).hexdigest();after=hashlib.sha256((P/'export'/f'{stem}.glb').read_bytes()).hexdigest();assert before==after;report['freed_exports_unchanged'][stem]=after
(P/'review/addons_v2/final_gates.json').write_text(json.dumps(report,indent=2)+'\n');print('FINAL_GATES',report)
