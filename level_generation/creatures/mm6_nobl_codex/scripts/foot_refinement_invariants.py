"""Confirm the final fall-cloak pass preserves the already checked body and foot animation."""
import sys,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];repo=p.parents[2];sys.path.insert(0,str(repo/'tools'))
from merge_head_material import read_glb,accessor_array
old,ob=read_glb(p/'review/feet_cloak_20261011/before_final_fall.glb');new,nb=read_glb(p/'export/mm6_nobl.glb')
def channels(d,b):
 result={}
 for a in d['animations']:
  for c in a['channels']:
   s=a['samplers'][c['sampler']];key=(a['name'],d['nodes'][c['target']['node']]['name'],c['target']['path'])
   result[key]=(accessor_array(d,b,s['input']),accessor_array(d,b,s['output']))
 return result
A=channels(old,ob);B=channels(new,nb);assert A.keys()==B.keys()
changed=[]
for key,(t,v) in A.items():
 nt,nv=B[key];assert np.array_equal(t,nt),key
 if not np.array_equal(v,nv):
  assert key[0] in ['Death','Dead'] and key[1].startswith('Cloak_'),key
  changed.append(key)
assert changed
report={'only_changed_channels':changed,'all_feet_root_body_and_other_clips_identical':True}
(p/'review/feet_cloak_20261011/final_channel_invariants.json').write_text(json.dumps(report,indent=1))
print('INVARIANTS',len(changed),'fall-cloak channels; all checked foot and body channels identical')
