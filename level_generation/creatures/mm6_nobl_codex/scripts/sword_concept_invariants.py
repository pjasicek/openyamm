"""Confirm the final fall-cloak pass preserves the already checked body and foot animation."""
import sys,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];repo=p.parents[2];sys.path.insert(0,str(repo/'tools'))
from merge_head_material import read_glb,accessor_array
old,ob=read_glb(p/'review/sword_concept_20261011/before/mm6_nobl.glb');new,nb=read_glb(p/'export/mm6_nobl.glb')
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
  changed.append(key)
assert not changed,changed
report={'only_changed_channels':changed,'all_animation_channels_identical':True}
(p/'review/sword_concept_20261011/channel_invariants.json').write_text(json.dumps(report,indent=1))
print('INVARIANTS',len(changed),'changed channels; all animation channels identical')

# LOD0 body remains byte-identical at every vertex; only the attachment is revised.
pa=old['meshes'][0]['primitives'][0];pb=new['meshes'][0]['primitives'][0]
for k in pa['attributes']:
 assert np.array_equal(accessor_array(old,ob,pa['attributes'][k]),accessor_array(new,nb,pb['attributes'][k])),k
assert np.array_equal(accessor_array(old,ob,pa['indices']),accessor_array(new,nb,pb['indices']))
print('BODY_LOD0_UNCHANGED',list(pa['attributes']))
