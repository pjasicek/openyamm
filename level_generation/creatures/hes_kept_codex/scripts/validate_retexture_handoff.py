"""Validate the five concrete Meshy handoffs and bind checks to exact retained revisions."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((P/p).read_text())
def record(p):return {'path':str(p),'sha256':sha(P/p)}
progress=read('creature_3d_progress.json');manifest=read('meshy/job_manifest.json');prior=progress['meshy']['jobs'];immutable=[]
for j in prior.values():
 for r in [*j.get('inputs',[]),*j.get('downloads',{}).values()]:
  assert sha(P/r['path'])==r['sha256'],r['path'];immutable.append(r['path'])
assert sum(j.get('consumed_credits',0)for j in prior.values())==20
bodies={};evidence=[]
for sex,code in [('male','m'),('female','f')]:
 rig=f'work/{sex}/rig_final_done.blend';master=f'work/{sex}/rig_texturing.blend';rh=sha(P/rig);mh=sha(P/master)
 joint=read(f'review/{sex}/joint_gate.json');stretch=read(f'review/{sex}/pilot_probe.json');contacts=read(f'review/{sex}/final_deformation.json');jerk=read(f'review/{sex}/jerk_comparison.json');inv=read(f'review/{sex}/master_invariance.json');upload=read(f'review/{sex}/texture_upload_validation.json');exp=read(f'texturing/kept_{code}_export.json')
 for d in (joint,stretch,contacts,jerk):assert d['source_sha256']==rh
 assert joint['rest_frame_error_deg']==0 and all(not s['outside']for s in joint['finger_samples'])
 assert stretch['bones']==56 and stretch['max_influences']<=8 and all(c['arm_p99_pass']and c['hand_max_pass']for c in stretch['clips'].values())
 assert contacts['pass'] and jerk['pass'] and inv['pass'] and upload['pass']
 assert inv['checked_rig_sha256']==rh and inv['texturing_master_sha256']==mh and exp['master_sha256']==mh
 assert exp['head_uv_overlap_pixels_2048']==0
 for row in upload['uploads']:assert sha(P/row['upload'])==row['sha256']
 for row in exp['uploads']:assert sha(P/row['path'])==row['sha256']
 bodies[sex]={'rig':record(rig),'master':record(master),'body_triangles':exp['body_triangles'],'head_triangles':exp['head_triangles'],'bones':56,'max_influences':stretch['max_influences'],'clips':len(stretch['clips']),'half_frame_samples':sum(r['frames_sampled']for r in stretch['clips'].values()),'max_arm_p99_stretch':max(v['p99']for r in stretch['clips'].values()for k,v in r['regions'].items()if k.endswith('arm')),'max_hand_edge_stretch':max(v['max']for r in stretch['clips'].values()for k,v in r['regions'].items()if k.endswith('hand')),'max_wrist_swing_deg':max(v for r in contacts['clips'].values()for v in r['wrist_swing_deg'].values()),'max_wrist_twist_deg':max(abs(v)for r in contacts['clips'].values()for pair in r['wrist_twist_deg'].values()for v in pair),'skin_penetrations':0,'unexpected_cloth_contacts':0,'jerk_pass':True,'head_uv_coverage_1k':upload['uploads'][1]['head_uv_coverage']}
 for name in ('joint_gate','pilot_probe','final_deformation','jerk_comparison','master_invariance','texture_upload_validation'):evidence.append(record(f'review/{sex}/{name}.json'))
 for file in (f'texturing/kept_{code}_correspondence.npz',f'texturing/kept_{code}_export.json',f'review/{sex}/final_poses.png',f'review/{sex}/final_fists.png'):evidence.append(record(file))
winding=read('review/texture_upload_winding.json');assert winding['pass'] and len(winding['uploads'])==4
for r in winding['uploads']:assert sha(P/r['path'])==r['sha256'] and r['inverted_closed_parts']==0
jobs=[]
for j in manifest['jobs']:
 if j['kind']!='retexture':continue
 req=read(j['request_file']);assert req['ai_model']=='meshy-7' and req['enable_pbr'] and req['texture_resolution']=='2k' and req['target_formats']==['glb']
 assert req['enable_original_uv']==('_head_'in j['id']) and len(req['multiview_image_urls'])==4
 inputs=[]
 for s in [req['model_url'],*req['multiview_image_urls']]:
  assert s.startswith('@file:');inputs.append(record(s.removeprefix('@file:')))
 jobs.append({'id':j['id'],'request':record(j['request_file']),'inputs':inputs,'estimated_credits':10,'target_file':j['target_file']})
assert {j['id']for j in jobs}=={'kept_m_ragged_v1','kept_m_freed_v1','kept_f_freed_v1','kept_m_head_v1','kept_f_head_v1'}
male=[j['inputs'][0]for j in jobs if j['id']in ('kept_m_ragged_v1','kept_m_freed_v1')];assert male[0]==male[1]
report={'pass':True,'scope':'Agent pretexture body/head handoff; equipped runtime and G7 remain pending','bodies':bodies,'jobs':jobs,'evidence':evidence,'immutable_paid_inputs_and_downloads_checked':sorted(set(immutable)),'spent_credits':20,'planned_credits':50,'working_cap':100,'runtime_installed':False,'staged_rows':[]}
(P/'review/retexture_handoff.json').write_text(json.dumps(report,indent=2)+'\n');print('HANDOFF_PASS',len(jobs),'ready jobs; 20 spent + 50 planned / 100')
