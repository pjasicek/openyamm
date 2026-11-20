"""Prepare variants, attachment and merged material; validate and install the Thug family."""
from pathlib import Path
import subprocess,sys,json,hashlib,shutil
p=Path(__file__).resolve().parents[1];repo=p.parents[2];e=p/'export'
def run(*args):subprocess.run([sys.executable,*map(str,args)],check=True)
run(p/'scripts/shrink_shadow_lods.py',e/'mm6_fgt_lods.glb',e/'mm6_fgt_lods_shadowfix.glb')
run(p.parent/'claude_shared/region_variants.py',e/'mm6_fgt_lods_shadowfix.glb',e/'mm6_fgt.glb',p/'textures/fgt_ramps.json',
 '--extra','Thug','openyamm_specular=0.75','--extra','Thug','openyamm_specular_mask=true','--extra','Thug','pbr.metallicFactor=0',
 '--extra','Mace','openyamm_specular=0.75','--extra','Mace','openyamm_specular_mask=true','--extra','Mace','pbr.metallicFactor=0')
run(repo/'tools/split_attachment.py',e/'mm6_fgt.glb','--joint','Mace','--body',e/'mm6_fgt.glb','--attachment',e/'mm6_fgt_mace.glb')
run(repo/'tools/merge_head_material.py',e/'mm6_fgt.glb',e/'mm6_fgt.glb')
sys.path.insert(0,str(repo/'tools'))
from merge_head_material import read_glb,accessor_array
import numpy as np
report={}
for name in ('mm6_fgt','mm6_fgt_mace'):
 f=e/f'{name}.glb';d,bin=read_glb(f)
 assert [v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]==['fgt_a','fgt_b','fgt_c']
 for mesh in d['meshes']:
  for pr in mesh['primitives']:
   pos=accessor_array(d,bin,pr['attributes']['POSITION']);idx=accessor_array(d,bin,pr['indices']).ravel()
   assert np.isfinite(pos).all() and idx.max()<len(pos) and len(idx)%3==0
   area=np.linalg.norm(np.cross(pos[idx.reshape(-1,3)[:,1]]-pos[idx.reshape(-1,3)[:,0]],pos[idx.reshape(-1,3)[:,2]]-pos[idx.reshape(-1,3)[:,0]]),axis=1)
   assert (area>1e-12).all(),f'Degenerate triangles in {name}/{mesh.get("name")}'
 if name=='mm6_fgt':
  assert {a['name'] for a in d['animations']}=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
  assert any(n.get('name')=='Mace' for n in d['nodes'])
  mesh=next(m for m in d['meshes'] if 'openyamm_lods' in m.get('extras',{}));assert len(mesh['extras']['openyamm_lods'])==3
 report[name]={'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'images':len(d['images']),'materials':len(d['materials'])}
 target=repo/'assets_dev/worlds/mm6/models'/f.name;shutil.copy2(f,target);target.chmod(0o644)
 print('INSTALLED',target)
(p/'export/runtime_validation.json').write_text(json.dumps(report,indent=2))
run(p/'scripts/viewer_tiers.py')
f=p/'review/viewer/manifest.json';d=json.loads(f.read_text());d['revision']='mm6_fgt_review3'
for m in d['models']:
 file=f'mm6_{m["id"]}.glb';h=hashlib.sha256((f.parent/file).read_bytes()).hexdigest();m.update({'url':file+'?v='+h[:12],'sha256':h,'revision':d['revision']})
f.write_text(json.dumps(d,indent=2))
