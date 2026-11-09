"""Prepare exact built-in-tool inputs; this script never calls a generation service."""
import argparse,json
from process import ROOT,queue,save
p=argparse.ArgumentParser();p.add_argument('jobs',nargs='+');a=p.parse_args()
data=json.loads((ROOT/'compact_jobs.json').read_text());requests=[]
for key in a.jobs:
 job=data['jobs'][key]
 assert job['status']=='pending', (key,job['status'])
 assert not (ROOT/'raw'/f'{key}_v1.png').exists(),key
 refs=[job['references'][0],'references/accepted_identity.png']
 if job['overlap_previous']:
  others=[(k,j) for k,j in data['jobs'].items() if k!=key and j['status'] in ['accepted_visual','accepted_identity'] and job['overlap_previous'][0] in j['frames']]
  assert others,('No accepted preceding overlap',key)
  previous=others[-1][1];refs.append(previous['selected_raw'])
 prompt=ROOT/job['prompt'];text=prompt.read_text()
 if 'Reference roles for this request:' not in text:
  text+='\nReference roles for this request: Input 1 is native pose/layout/color authority; Input 2 is accepted standing identity only.'
  if len(refs)>2:text+=' Input 3 is the accepted preceding chunk for identity and overlap continuity, without changing native pose order.'
  text+='\n';prompt.write_text(text)
 job['references']=refs
 requests.append({'key':key,'prompt':text,'referenced_image_paths':[str(ROOT/r) for r in refs],
                  'prompt_sha256':queue.sha(prompt),'reference_hashes':{r:queue.sha(ROOT/r) for r in refs}})
save(ROOT/'compact_jobs.json',data)
print(json.dumps(requests))
