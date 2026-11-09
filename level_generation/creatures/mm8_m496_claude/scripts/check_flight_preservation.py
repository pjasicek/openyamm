"""The animation-only revision must preserve every mesh/map and every non-travel clip."""
from pathlib import Path
import json,sys,numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared/gates'))
from run_gates import Glb
old=Glb(p/'archive/pre_native_flight/export/mm8_m496.glb');new=Glb(p/'export/mm8_m496.glb')
for before in old.doc['meshes']:
 after=next(m for m in new.doc['meshes'] if m['name']==before['name'])
 assert len(before['primitives'])==len(after['primitives'])
 for a,b in zip(before['primitives'],after['primitives']):
  assert a['attributes'].keys()==b['attributes'].keys()
  for key in a['attributes']:
   np.testing.assert_allclose(old.accessor(a['attributes'][key]),new.accessor(b['attributes'][key]),atol=1e-7,rtol=0,err_msg=before['name']+'/'+key)
  np.testing.assert_array_equal(old.accessor(a['indices']),new.accessor(b['indices']))
for a,b in zip(old.doc['images'],new.doc['images']):
 def data(glb,image):
  view=glb.doc['bufferViews'][image['bufferView']];offset=view.get('byteOffset',0);return glb.data[offset:offset+view['byteLength']]
 assert data(old,a)==data(new,b),'Texture changed'
new_ids=[new.names[n['name']] for n in old.nodes];errors={}
for name,animation,start,end in old.clips():
 if name in ['Walking','Running']:continue
 after=next(a for a in new.doc['animations'] if a['name']==name);times=np.linspace(start,end,17)
 error=float(np.abs(old.pose(animation,times)-new.pose(after,times)[:,new_ids]).max());assert error<1e-5,(name,error);errors[name]=error
report={'old_sha256':old.sha256,'new_sha256':new.sha256,'geometry_and_maps':'unchanged including all skin weights','non_travel_pose_errors':errors}
(p/'work/flight_preservation.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
