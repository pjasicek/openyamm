from pathlib import Path
import subprocess,json,hashlib
p=Path(__file__).resolve().parents[1];V=p/'review/viewer';V.mkdir(parents=True,exist_ok=True)
subprocess.run(['python3','tools/prepare_actor_glb.py',str(p/'export/mm8_m460_lod0.glb'),str(p/'export/mm8_m460_runtime_lod0.glb')],check=True)
subprocess.run(['python3',str(p/'scripts/viewer_tiers.py')],check=True)
info=json.loads((p/'export/export_info.json').read_text());inventory=json.loads((p/'native_inventory.json').read_text())
provenance={'Standing':'Local RelaxIdle with native upright staff carry.','Walking':'Local RelaxWalkForward with fitted robe and grounded stride.','Attack':'Mixamo Standing 2H Magic Attack 01: two-handed library casting at its original speed, fitted forward step, weight transfer and staff grip. Palm release at 1.20 s.','Cast':'Native spell alias of Attack; independent runtime role.','Hit':'Local UnarmedGetHitF1 fitted to the native 0.625-second hit window.','Death':'Local RelaxLaydownLayDown forward fall, fitted closed robe and released staff.','Dead':'Exact final Death pose held.','Fidget':'Native intent: body remains grounded while the head and staff settle.'}
actions={'Standing':'standing','Walking':'walk','Attack':'attack','Cast':'attack2','Hit':'hit','Death':'death','Dead':'corpse','Fidget':'fidget'}
# Source table names are authoritative, including repeated native holds and front-only corpse/fall views.
binding=inventory['bindings']['46']['actions'];print('NATIVE_ACTIONS',list(binding))
key_alias={'attack_melee':'attack1','attack_ranged':'attack2','dying':'death'}
manifest={'revision':'mm8_m460_two_hand_cast_step_v3','default_model':'m460_a','default_clip':'Standing','model':'mm8_m460_a.glb','feedback':'feedback/user_feedback.json','models':[],'clips':{}}
for tier,label in zip('abc',['Acolyte — black hair / green staff','Cleric — brown hair / blue staff','Priest — blond hair / red staff']):
 f=V/f'mm8_m460_{tier}.glb';sha=hashlib.sha256(f.read_bytes()).hexdigest();manifest['models'].append({'id':f'm460_{tier}','label':label,'revision':manifest['revision'],'url':f.name+'?v='+sha[:12],'sha256':sha})
manifest['model_sha256']=manifest['models'][0]['sha256']
for role,duration in info['clips'].items():
 key=actions[role]
 if key not in binding:key=key_alias.get(key,key)
 rows=binding[key]['views']['0'];total=sum(r['duration_ms'] for r in rows);clock=0.;anchors=[];span=1.20 if role in ['Attack','Cast'] else duration
 for index,r in enumerate(rows):
  images=['../../native/'+view_rows[index]['frame']+'_461.png' for view,view_rows in sorted(binding[key]['views'].items()) if index<len(view_rows)]
  images=list(dict.fromkeys(images))
  assert all((V/image).exists() for image in images)
  frame=r['frame'];anchors.append({'time':span*clock/total,'label':frame,'phase':'Native intent','source_images':images});clock+=r['duration_ms']
 manifest['clips'][role]={'label':role,'duration':duration,'mode':'loop' if role in ['Standing','Walking','Dead'] else 'once','provenance':provenance[role],'reference_note':'Native frames show intent; fitted 3D movement is not a frame trace.','anchors':anchors}
(V/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('VIEWER_MANIFEST',info['clips'])
