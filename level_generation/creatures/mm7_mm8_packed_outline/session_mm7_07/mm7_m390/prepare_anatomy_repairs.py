import importlib.util,json,sys,re
from pathlib import Path
p=Path(__file__).with_name('session_pipeline.py'); s=importlib.util.spec_from_file_location('session',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
stem,action=sys.argv[1:3]; root=m.STAGE/('mm7_'+stem);out=root/'redo_2x';requests=[]
if stem=='m418':
 template=m.read(root/'repair_walk_requests.json')[0]['prompt'];material=out/'references/troglodyte_material_only_repair.png';reason='Native hand anatomy requires exactly three thin curved claws and narrow wrist; keep native occlusions, thin tail and dark olive material.'
else:
 template=m.read(m.STAGE/'mm7_m390/repair_batch9.json')[0]['prompt'];material=out/'references/spider_material_finish_v3.png';reason='Organic native chitin and small terminal hooks: remove metallic tube finish and oversized claw caps while retaining all eight native leg chains.'
run=m.read(out/'run.json')
ids=[j['id'] for j in run['jobs'] if j['action']==action]
for job_id in ids:
 run=m.read(out/'run.json');old=next(j for j in run['jobs'] if j['id']==job_id)
 for a in old['attempts']:
  if a.get('raw')==old.get('selected_raw') or a.get('path')==old.get('selected_raw') or a==old['attempts'][-1]:a.update(visual_status='rejected_visual',visual_reason=reason)
 m.save(out/'run.json',run);m.retry(stem,job_id,reason,8)
 run=m.read(out/'run.json');job=next(j for j in run['jobs'] if j['id']==job_id)
 prompt=template
 lines=prompt.splitlines()
 if stem=='m418':
  lines[1]=f'Return exactly ONE COMPLETE Troglodyte {action} animation for stored view {job["view"]}, ALL {len(job["frames"])} original steps together on ONE transparent RGBA sheet. Exactly {job["columns"]} columns by {job["rows"]} rows, chronological row-major order '+', '.join(job['frames'])+'; any unused final grid slot stays fully transparent. No added or omitted steps.'
  lines=[x.replace('all seven gait phases', 'all original animation phases') for x in lines]
  lines[-1]=f'Shared native-coordinate union crop {job["native_crop"]}, padded cell {job["cell_native_size"]} native pixels; eight native pixels transparent safety padding. Preserve exact relative placement and ONE scale throughout every frame. No per-cell recentering, zoom, silhouette fitting or limb distortion. Request {job["requested_master"][0]}x{job["requested_master"][1]} for >=2.2x generated detail where possible. One complete animation takes priority over sampling. Genuine transparent native gaps; no ground, shadow, text or scenery.'
 else:
  lines[1]=f'Use case: style-transfer. Restore ONE COMPLETE original Spider A {action} animation at stored rotation {job["view"]}. Exactly ALL {len(job["frames"])} native frames in ONE returned transparent RGBA sheet, {job["columns"]} columns by {job["rows"]} rows, row-major order: '+', '.join(job['frames'])+'. Leave unused slots transparent; no repeated, omitted or additional poses.'
  lines=[f'Use shared native crop {job["native_crop"]} and cell {job["cell_native_size"]} native pixels for every frame; eight native pixels transparent safety padding. Preserve exact native relative placement and one scale throughout; no independent zoom, centering or silhouette fitting.' if x.startswith('Use the same common') else x for x in lines]
  lines=[f'Request at least {job["requested_master"][0]}x{job["requested_master"][1]} pixels, aiming >=2.2x actual generated detail. ALL original steps on ONE complete returned sheet take priority over sampling. Never split.' if x.startswith('Request at least') else x for x in lines]
  if job['view']>=3:
   material=out/'references/spider_rear_material_only.png'
   lines.insert(3,'REAR OBLIQUE OR REAR VIEW: preserve native hidden-head occlusion. Do not show a frontal face, yellow eyes, mandibles, red cheeks or skull face when absent from Image 1. Green abdomen and all leg roots keep exact native projections. Appearance patches show material only.')
  else:material=out/'references/spider_material_finish_v3.png'
 prompt='\n'.join(lines).strip()+'\n';assert prompt.startswith(m.HEADER)
 refs=[str(m.REPO/Path(x)) for x in job['references'][:2]]+[str(material)]
 Path(job['prompt']).write_text(prompt);job['references']=refs
 job['appearance_source']=dict(path=str(material),sha256=m.sha(material),role='same_family_material_only_no_pose_authority')
 job['prepared_assets']=[dict(path=str(x),sha256=m.sha(Path(x))) for x in refs+[job['prompt']]]
 m.save(out/'run.json',run)
 requests.append(dict(family=stem,job_id=job_id,prompt=prompt,referenced_image_paths=refs,transparent_background=True))
m.save(root/('repair_'+action+'_requests.json'),requests)
print(json.dumps([dict(job=x['job_id'],refs=x['referenced_image_paths'][:2]) for x in requests]))
