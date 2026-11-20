"""Check cooked geometry, animation samples, texture files and row binding under a shared stage lock."""
import fcntl,json,sys
from pathlib import Path
import numpy as np
import yaml
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parent/'claude_shared/gates'));from run_gates import Glb,load_meshes
stage=R/'output/hesper_stage/assets_editor_dev';model=stage/'worlds/hesper/models/hes_brood_mother.glb'
def canonical(faces):
 out=np.take_along_axis(faces,(np.arange(3)[None,:]+faces.argmin(1)[:,None])%3,axis=1)
 return out[np.lexsort(out.T[::-1])]
with open(R/'output/hesper_stage/locks/stage.lock','a') as lock:
 fcntl.flock(lock,fcntl.LOCK_SH)
 a=Glb(P/'export/hes_brood_mother.glb');b=Glb(model);aa,bb=load_meshes(a),load_meshes(b);assert len(aa)==len(bb)==8
 for left,right in zip(aa,bb):
  assert np.array_equal(left.rest,right.rest)
  assert np.array_equal(canonical(left.faces),canonical(right.faces))
  assert np.array_equal(left.weights,right.weights) and np.array_equal(left.joints,right.joints)
 assert len(a.doc['animations'])==len(b.doc['animations'])==6
 for left,right in zip(a.doc['animations'],b.doc['animations']):
  assert left['name']==right['name'] and left['channels']==right['channels']
  for l,r in zip(left['samplers'],right['samplers']):
   for key in ('input','output'):assert np.array_equal(a.accessor(l[key]),b.accessor(r[key]))
 for image in b.doc['images']:assert (model.parent/image['uri']).is_file()
 own=yaml.safe_load((P/'integration/actors.yml').read_text())[0]
 actual=next(x for x in yaml.safe_load((model.parent/'actors.yml').read_text())['actors'] if x['descriptor']=='hes_brood_mother');assert own==actual
 report={'source_sha256':a.sha256,'staged_sha256':b.sha256,'all_colour_shadow_geometry_and_weights_preserved':True,'index_order':'cache-reordered, same oriented triangles','binding_matches':True,'animation_samples_match':True,'cooked_textures':len(b.doc['images']),'stage':str(stage.relative_to(R)),'row':10111,'status':'pass'}
(P/'review/staged_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
