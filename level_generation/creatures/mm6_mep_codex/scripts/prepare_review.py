import json,hashlib,yaml
from pathlib import Path
p=Path(__file__).resolve().parents[1];v=p/'review/viewer';info=json.loads((p/'export/export_info.json').read_text());revision=info['review_revision'];models=[]
for tier,label in [('a','Follower of Baa'),('b','Mystic of Baa'),('c','Fanatic of Baa')]:
 name=f'mm6_mep_{tier}.glb';sha=hashlib.sha256((v/name).read_bytes()).hexdigest();models.append({'id':f'mep_{tier}','label':label,'url':name+'?v='+sha[:12],'sha256':sha,'revision':revision})
provenance={'Standing':'RelaxIdle; upright native stance and relaxed free palm.','Walking':'RelaxWalkForward; 8.4 cm foot lift and planted stance phase.','Running':'RelaxRunForward; 0.60 s jog cycle, wider arm swing and 0.958182 m planted stride fitted to the runtime 1.55 multiplier.','Fidget':'RelaxIdle with native head glance, moving arms, staff and knees.','Attack':'StaffAttack1 local torso motion; native one-handed wind-up, full forward shaft swing, planted step and follow-through. Review 1 shoulder weights and continuous wrist transitions.','Cast':'Exact copy of Attack (user review 2); distinct clip name for Mystic, identical staff-head launch impact at 0.84375 s.','Hit':'UnarmedGetHitF1; enlarged backward torso and head recoil, both arms and staff follow, then recover.','Death':f"Mixamo Standing React Death Backward; fitted supine fall, 2x timing in review 3; fingers open and staff releases at {info['clips']['Death'].get('staff_release',.15)} s.",'Dead':'Exact final Death pose held, including the released staff.'}
prefix={'Standing':'sta','Walking':'wal','Running':'wal','Attack':'att','Cast':'att','Fidget':'fid','Hit':'win','Death':'dyi','Dead':'dyi'};clips={}
for role,entry in info['clips'].items():
 anchors=[];frames=[''] if role=='Standing' else ['f'] if role=='Dead' else list('abcdef')
 for i,letter in enumerate(frames):
  images=[f'../../../mm6_mep/native/mep{prefix[role]}{letter}{view}.png' for view in range(5 if role in ['Standing','Walking','Running'] else 1)]
  for image in images:assert (v/image).resolve().exists(),image
  anchors.append({'time':entry['duration']*i/max(len(frames),1),'label':'Native phase reference','phase':'Native appearance and pose reference; library timing is adapted.','source_images':images})
 clips[role]={k:entry[k] for k in ['duration','mode']};clips[role].update(label=role,provenance=provenance[role],anchors=anchors)
manifest={'revision':revision,'model':models[0]['url'],'model_sha256':models[0]['sha256'],'default_model':'mep_a','default_clip':'Standing','feedback':'feedback/user_feedback.json','models':models,'clips':clips};(v/'manifest.json').write_text(json.dumps(manifest,indent=2))
entries=[];scale=175/info['standing_height_m']
for tier in 'ABC':
 e={'descriptor':f'PeasantM3 {tier}','model':'worlds/mm6/models/mm6_mep.glb','scale':round(scale,6),'yaw_offset':-1.570796327,'skin':'mep_'+tier.lower()}
 if tier!='A':e['scale_reference']='PeasantM3 A'
 e['animation']={'cast':'Cast','run':'Running','stride_length':.618182,'upper_body_root':'B_Spine','cast_focus_socket':'Socket_Staff_Head','cast_focus_glow_scale':.6,'look':{'nodes':['B_Neck','B_Head'],'max_yaw_degrees':60,'max_pitch_degrees':35},'sockets':{'eye_left':'Socket_Eye_Left','eye_right':'Socket_Eye_Right','palm_left':'Socket_Palm_Left','palm_right':'Socket_Palm_Right'},'events':{'attack_melee':{'impact':info['clips']['Attack']['impact']},'attack_ranged':{'impact':info['clips']['Attack']['impact'],'launch_socket':'Socket_Staff_Head'},'cast':{'impact':info['clips']['Cast']['impact'],'launch_socket':'Socket_Staff_Head'}}}
 e['clips']={'standing':'Standing','walking':'Walking','attack_melee':'Attack','attack_ranged':'Attack','hit':'Hit','dying':'Death','dead':'Dead','fidget':'Fidget'};e['attachments']=[{'model':'worlds/mm6/models/mm6_mep_staff.glb','node':'Staff'}];entries.append(e)
(p/'integration').mkdir(exist_ok=True);(p/'integration/actors.yml').write_text('# Staged only; orchestrator merges these exact descriptor blocks.\n'+yaml.safe_dump(entries,sort_keys=False));print('REVIEW_AND_BINDINGS',scale)
