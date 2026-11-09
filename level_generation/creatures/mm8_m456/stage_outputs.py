"""Stage built-in tool results and exact request hashes. No service/API calls."""
import argparse,json,re,shutil
from process import ROOT,queue,save
p=argparse.ArgumentParser();p.add_argument('record');a=p.parse_args()
records=json.loads((ROOT/a.record).read_text());data=json.loads((ROOT/'compact_jobs.json').read_text())
for record in records:
 key=record['key'];job=data['jobs'][key]
 if 'error' in record:
  job.update(status='generation_failed',generation_error=record['error']);continue
 request=record['request'];version=record.get('version',1)
 if version>1:
  job.setdefault('rejected_versions',[]).append({'raw':job['selected_raw'],'prompt':job['prompt'],
   'tool_record':job.get('tool_record'),'reason':request['prompt'],'generation':job.get('generation')})
  for field in ['frozen_calibration','extraction_overrides','extraction_empty_seams','extraction_masks','reviewed_isolated_residue','seam_alpha_residue_max','boundary_alpha_residue_max','seam_review','boundary_review','minimum_horizontal_seam_width','minimum_vertical_seam_width','narrow_seam_review']:
   job.pop(field,None)
  job['prompt']=f'prompts/{key}_v{version}.txt'
  job['references']=[str(__import__('pathlib').Path(p).relative_to(ROOT)) for p in request['referenced_image_paths']]
 assert (ROOT/job['prompt']).read_text().strip()==request['prompt'].strip()
 if 'prompt_sha256' in request:assert queue.sha(ROOT/job['prompt'])==request['prompt_sha256']
 for path,digest in request.get('reference_hashes',{}).items():assert queue.sha(ROOT/path)==digest,path
 source=re.search(r' as (/\S+\.png) by default',record['output_hint']).group(1)
 assert '/.codex/generated_images/' in source
 target=ROOT/'raw'/f'{key}_v{version}.png';assert not target.exists(),target
 shutil.copy2(source,target)
 job.update(status='generated_unprocessed',selected_raw=str(target.relative_to(ROOT)),tool_record=a.record)
save(ROOT/'compact_jobs.json',data)
print({r['key']:data['jobs'][r['key']]['status'] for r in records})
