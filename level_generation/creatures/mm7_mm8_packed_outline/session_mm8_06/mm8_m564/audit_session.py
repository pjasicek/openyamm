import json,pathlib,hashlib,numpy as np,yaml
from PIL import Image
from scipy import ndimage
b=pathlib.Path('level_generation/creatures/mm7_mm8_packed_outline/session_mm8_06').resolve()
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
table_cache={};verified_native_groups=set();reconciliation=read(b/'mm8_m564/CURRENT_NATIVE_TABLE_RECONCILIATION.json')
def current_group(name):
 p=pathlib.Path('assets_dev/engine/rendering/sprite_frames/monsters')/(name[:-1]+'.yml') if name.startswith('m') else pathlib.Path('assets_dev/engine/rendering/sprite_frame_data_common.yml')
 if p not in table_cache:table_cache[p]={x['sprite_name']:x for x in yaml.load(p.read_text(),Loader=yaml.CSafeLoader)['sprites']}
 return table_cache[p].get(name)
header='TASK CONTEXT — MM8 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration of an EXISTING Might and Magic VIII (MM8) fantasy role-playing game sprite asset, using the supplied original animation bitmaps. Restore the existing fantasy-game character and its original animation; preserve its native costume, material coverage, anatomy and poses. The request is game-art restoration.'
expected={564:(35,155,0,[124,125,126]),568:(35,160,20,[127,128,129]),572:(30,125,22,[130,131,132]),576:(35,160,0,[133,134,135]),580:(30,135,0,[136,137,138]),584:(30,140,10,[139,140,141]),588:(26,95,53,[142,143,144]),592:(40,160,49,[145,146,147,196,197,198])}
rows=[];checked_outlines=set();submission_count=0;failed_services=[];bootstrap=[];historical_prompt_paths=[]
for number,(jobs,frames,unused,ids) in expected.items():
 r=b/f'mm8_m{number}';o=r/'redo_2x';s=read(r/'sources.json');run=read(o/'run.json');m=read(o/'manifest.json');v=read(o/'validation.json');reg=read(o/'registration.json');ac=read(o/'review/acceptance.json');dec=read(o/'review/decision.json')
 assert ac['status']=='accepted' and ac['reviewed_frames']==frames and not ac['installed']
 assert len(run['jobs'])==jobs and all(j.get('selected_raw') for j in run['jobs'])
 assert set(reg)==set(s['sources'])==set(m['frames']) and len(reg)==frames
 assert [int(x) for x in s['bindings']]==ids and m['native_descriptor_bindings']==s['bindings']
 assert m['animations_by_descriptor'].keys()==s['bindings'].keys()
 for binding in s['bindings'].values():
  for action in binding['actions'].values():
   name=action.get('native_group');native_record=action.get('native_group_record')
   assert (current_group(name) if name else None)==native_record,(r.name,name,'current native group changed')
   if name and name.startswith('m'):verified_native_groups.add(name)
 assert len(s['orphan_images'])==unused and m['orphan_images']==s['orphan_images']
 played={step['frame'] for d in m['animations_by_descriptor'].values() for a in d.values() for steps in a['views'].values() for step in steps}
 assert not (set(s['orphan_images']) & played)
 assert all(not x['raw_clip'] for x in reg.values()) and v['visual_review_complete']
 technical_keys=['source_hashes_unchanged','palette_hashes_unchanged','raw_cells_unclipped','generation_provenance_hashes_verified','exact_crop_reconstruction','exact_atlas_extraction','variant_alpha_unchanged','zero_mask_unchanged','base_bypass_exact','per_palette_native_sequences_preserved','exact_descriptor_bindings_preserved','unused_art_excluded_from_playback','mandatory_outline_attachments_verified']
 assert all(v[k] is True for k in technical_keys),(r.name,'technical checks')
 local_status=read(r/'session_status.json')
 assert local_status['accepted'] and not local_status['installed'] and local_status['selected_returned_jobs']==jobs and local_status['acceptance_sha256']==sha(o/'review/acceptance.json'),(r.name,'local status')
 for name,h in ac['artifact_hashes'].items():assert sha(o/name)==h,(r.name,name,'frozen artifact')
 for name,h in dec['evidence_artifacts'].items():assert sha(o/name)==h,(r.name,name,'evidence')
 assert sha(pathlib.Path(s['descriptor_table']['path']))==s['descriptor_table']['sha256']
 for rec in s['sources'].values():assert sha(pathlib.Path(rec['path']))==rec['sha256']
 for pal,rec in s['palette_sources'].items():
  assert sha(pathlib.Path(rec['path']))==rec['sha256']==sha(o/f'palettes/pal{pal}.act')
 for j in run['jobs']:
  assert j['frames'] and j['columns']*j['rows']>=len(j['frames'])
  selected=next(a for a in j['attempts'] if a['raw']==j['selected_raw'])
  assert sha(pathlib.Path(selected['raw']))==selected['sha256']
  assert sha(pathlib.Path(selected['prompt']))==selected['prompt_sha256'],(r.name,j['id'],'selected prompt')
  for a in j['attempts']:
   assert sha(pathlib.Path(a['raw']))==a['sha256']
   if sha(pathlib.Path(a['prompt']))!=a['prompt_sha256']:
    assert a['raw']!=j['selected_raw']
    historical_prompt_paths.append(dict(family=r.name,job=j['id'],rejected_raw=a['raw'],historical_prompt_sha256=a['prompt_sha256'],superseded_prompt_file=a['prompt'],current_file_sha256=sha(pathlib.Path(a['prompt'])),authority='The immutable actual_tool_arguments.prompt text in the matching submission preserves the exact historical submitted prompt. The rejected attempt prompt path points to a later prompt version.'))
   assert pathlib.Path(a['prompt']).read_text().startswith(header)
   matching=[z for z in j['submissions'] if z.get('raw')==a['raw'] and z['prompt_sha256']==a['prompt_sha256']]
   assert len(matching)==1,(r.name,j['id'],'submission provenance')
   assert a['actual_submitted_inputs']==matching[0]['input_assets']
   if sha(pathlib.Path(a['prompt']))!=a['prompt_sha256']:
    archived=r/'submission_provenance_audit'/j['id']/(pathlib.Path(a['raw']).stem+'_actual_prompt.txt');archived.parent.mkdir(parents=True,exist_ok=True)
    actual_prompt=matching[0]['actual_tool_arguments']['prompt']
    assert hashlib.sha256(actual_prompt.encode()).hexdigest()==a['prompt_sha256']
    if archived.exists():assert sha(archived)==a['prompt_sha256']
    else:archived.write_text(actual_prompt)
    historical_prompt_paths[-1]['archived_submitted_prompt']=str(archived);historical_prompt_paths[-1]['archived_prompt_sha256']=sha(archived)
  for z in j['submissions']:
   submission_count+=1;args=z['actual_tool_arguments'];inputs=z['input_assets']
   assert hashlib.sha256(args['prompt'].encode()).hexdigest()==z['prompt_sha256'],(r.name,j['id'],'actual submitted prompt hash')
   assert args['prompt'].startswith(header) and args['transparent_background']
   assert args['referenced_image_paths']==[x['path'] for x in inputs]
   assert len(inputs)==3 or (len(inputs)==2 and z['bootstrap_exception'])
   assert inputs[0]['role']=='untouched_native_complete_animation'
   assert inputs[1]['role']=='matching_outline_only_geometry_no_shading'
   assert pathlib.Path(inputs[1]['path']).name==j['id']+'_outline.png'
   for rec in inputs:
    p=pathlib.Path(rec['path']);assert p.is_absolute() and p.is_relative_to(r) and sha(p)==rec['sha256']
   key=(inputs[0]['sha256'],inputs[1]['sha256'])
   if key not in checked_outlines:
    color=Image.open(inputs[0]['path']).convert('RGBA');outline=Image.open(inputs[1]['path']).convert('RGB');assert color.size==outline.size
    inside=np.array(color.getchannel('A'))[::2,::2]>0;edge=inside & ~ndimage.binary_erosion(inside,structure=np.ones((3,3),bool));expected_outline=np.full((*inside.shape,3),255,np.uint8);expected_outline[edge]=0
    assert np.array_equal(np.array(Image.fromarray(expected_outline).resize(color.size,Image.Resampling.NEAREST)),np.array(outline)),(r.name,j['id'],'pure outline geometry')
    checked_outlines.add(key)
   if z.get('bootstrap_exception'):bootstrap.append({'family':r.name,'job':j['id'],'prompt_sha256':z['prompt_sha256']})
   if z['status']=='failed_imagegen':failed_services.append({'family':r.name,'job':j['id'],'error':z['error'],'resolved':bool(j['selected_raw'])})
 rows.append(dict(family=s['label'],project=r.name,descriptor_ids=ids,jobs=jobs,native_files=frames,unused_files=unused,palettes=list(s['palette_sources']),aliases=len(s['pixel_aliases']),generated_minimum=ac['generated_minimum'],below_2x_frames=len(ac['below_target_frames']),below_2x_frame_names=ac['below_target_frames'],physical_scale=2,acceptance_sha256=sha(o/'review/acceptance.json'),frozen_artifact_count=len(ac['artifact_hashes']),failed_return_attempts=sum(a['raw']!=j['selected_raw'] for j in run['jobs'] for a in j['attempts']),acceptance_record=f'../{r.name}/redo_2x/review/acceptance.json'))
assert sum(x['jobs'] for x in rows)==261 and sum(x['native_files'] for x in rows)==1130 and sum(x['unused_files'] for x in rows)==154 and sum(len(x['palettes']) for x in rows)==22
assert verified_native_groups==set(reconciliation['verified_native_group_names']) and len(verified_native_groups)==168
assert sum(x['below_2x_frames'] for x in rows)==90
record=dict(status='complete_validated_staged',families=rows,whole_animation_jobs=261,native_files=1130,unused_files=154,native_palettes=22,actual_submissions=submission_count,verified_matching_outline_pairs=len(checked_outlines),bootstrap_exceptions=bootstrap,failed_imagegen_services=failed_services,historical_prompt_path_reconciliation=historical_prompt_paths,current_native_groups_verified=len(verified_native_groups),native_table_reconciliation={'path':str(b/'mm8_m564/CURRENT_NATIVE_TABLE_RECONCILIATION.json'),'sha256':sha(b/'mm8_m564/CURRENT_NATIVE_TABLE_RECONCILIATION.json')},current_relevant_table_hashes={str(p):sha(p) for p in table_cache},below_2x_native_frames=90,failed_return_attempts=sum(x['failed_return_attempts'] for x in rows),installed=False,scope='All authored artifacts remain under session_mm8_06/<family>/.')
(b/'mm8_m564/SESSION_AUDIT.json').write_text(json.dumps(record,indent=2)+'\n')
lines=['All eight families are complete and locally accepted: 261 complete animation/view sheets, 1,130 native files, 22 native palettes and 154 unused native files retained outside playback. No gameplay installation.','', '| Family | Descriptor IDs | Sheets | Native files | Unused | Palettes | Lowest generated detail | Frames below 2× | Acceptance |','|---|---|---:|---:|---:|---|---:|---:|---|']
for x in rows:lines.append('| '+ ' | '.join([x['family'],', '.join(map(str,x['descriptor_ids'])),str(x['jobs']),str(x['native_files']),str(x['unused_files']),', '.join(x['palettes']),f"{x['generated_minimum']:.3f}×",str(x['below_2x_frames']),f"[frozen record]({x['acceptance_record']})"])+' |')
lines.extend(['','Every returned sheet used the complete untouched native-colour view and its matching separate pure outline PNG as actual imagegen attachments. Selected same-family detail was also attached, with five individually recorded bootstrap submissions while no adequate same-family detail was available. Every submission and retry preserves absolute input paths, roles, prompt and SHA-256 hashes. The final audit rechecked all attachments, pure outline construction, native file/palette hashes, descriptor bindings and frozen artifacts.','', 'All physical masters are 2×. Generated-detail measurements use one shared anatomical scale per complete sheet and remain separate from export scale. Below-2× frames were visually reviewed under the authorized whole-cycle policy; none were split or retried solely for that shortfall. Exact native sequences, holds, aliases, mirrors, raw timing, fractional placement and Plane Guardian/Wimpy scales are preserved in each package manifest.','', 'Each package contains aligned masters, base and R8 mask atlases, native ACT files, animation/placement metadata, full-pose placement contacts, palette/mask contacts, unresized material and alpha checks, review notes and frozen acceptance hashes. Failed visual attempts and service errors remain recorded alongside their successful replacements.','', f"Audit: {submission_count} actual submissions; {len(checked_outlines)} distinct native/outline pairs; {len(bootstrap)} logged bootstrap submissions; {len(failed_services)} resolved imagegen service errors.",'', 'The final audit also compared all 168 requested native animation groups against current YAML field by field. Two unrelated discovery-wide tables changed externally during the run; the requested bindings remain identical. See [current native reconciliation](CURRENT_NATIVE_TABLE_RECONCILIATION.json).','', 'Six rejected attempts have historical prompt paths that point to later versions. Their exact submitted prompt texts and hashes remain preserved in the immutable actual-tool-argument records and supplemental submission_provenance_audit archives; selected prompts all match their files. Frozen acceptance packages remain unchanged.','', '[Machine-readable audit](SESSION_AUDIT.json)'])
(b/'mm8_m564/SESSION_COMPLETION.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ['families','historical_prompt_path_reconciliation','current_relevant_table_hashes','failed_imagegen_services','bootstrap_exceptions']},indent=2))
print('Historical rejected prompt path reconciliations:',len(historical_prompt_paths))
for x in rows:print(x['project'],x['jobs'],x['native_files'],x['generated_minimum'],x['below_2x_frames'],x['frozen_artifact_count'])
