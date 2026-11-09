"""Structural checks of the staged runtime asset; no engine launch."""
import sys,json,hashlib,io
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
f=P/'export/mm6_lch.glb';d,b=read_glb(f)
variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]
assert variants==['lch_a','lch_b','lch_c'],variants
node=next(n for n in d['nodes'] if n.get('name')=='Lich');skin=d['skins'][node['skin']]
joints=[d['nodes'][j]['name'] for j in skin['joints']]
assert all(n in joints for n in ['B_Neck','B_Head','B_Spine','Socket_Palm_Left','Socket_Palm_Right'])
lods=[node['mesh']]+d['meshes'][node['mesh']]['extras']['openyamm_lods']
shadows=d['meshes'][node['mesh']]['extras']['openyamm_shadow_lods'];assert len(lods)==4 and len(shadows)==4
tris=[]
for mi in lods+shadows:
 mesh=d['meshes'][mi];assert len(mesh['primitives'])==1
 total=0
 for p in mesh['primitives']:
  total+=d['accessors'][p['indices']]['count']//3
  a=p['attributes'];pos=accessor_array(d,b,a['POSITION']);assert np.isfinite(pos).all()
  weights=accessor_array(d,b,a['WEIGHTS_0'])
  if 'WEIGHTS_1' in a:weights=np.c_[weights,accessor_array(d,b,a['WEIGHTS_1'])]
  assert np.all(weights>=0) and np.all(abs(weights.sum(1)-1)<1e-4)
  for k in [k for k in a if k.startswith('JOINTS')]:assert accessor_array(d,b,a[k]).max()<len(joints)
  mappings=p['extensions']['KHR_materials_variants']['mappings']
  assert sorted(i for m in mappings for i in m['variants'])==[0,1,2]
 if mi in lods:tris.append(total)
assert all(a>b for a,b in zip(tris,tris[1:]))
clips={}
for a in d['animations']:
 times=[]
 for s in a['samplers']:
  t=accessor_array(d,b,s['input']).ravel();v=accessor_array(d,b,s['output'])
  assert np.isfinite(v).all() and np.all(np.diff(t)>0)
  times.append(float(t.max()))
 clips[a['name']]=max(times)
assert set(clips)=={'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget'}
assert clips['Hit']<=.75
images=[]
for im in d['images']:
 view=d['bufferViews'][im['bufferView']];off=view.get('byteOffset',0);pix=Image.open(io.BytesIO(b[off:off+view['byteLength']]))
 assert pix.size==(2080,1024);images.append({'name':im.get('name'),'size':pix.size})
assert len(images)==4
for mat in d['materials']:
 assert mat['extras']['openyamm_specular_mask'] and mat['pbrMetallicRoughness']['metallicFactor']==0
g=json.loads((P/'work/rig_gates.json').read_text());contacts=json.loads((P/'work/g6_contacts.json').read_text());trace=json.loads((P/'work/trace_export.json').read_text())
for c in clips:
 assert g[c]['g4_arm_edge_max']<1.01 and g[c]['g5_hand_edge_max']<1.01
 assert not trace[c]['flags']
 for part,value in contacts[c].items():
  if part.endswith('_cloth'):
   baseline=json.loads((P/'review/triangle_rebake/lod_baseline_contacts.json').read_text())
   assert value==baseline[c][part], 'Reduction worsened accepted cloth contact'
  else:assert value[0] <= (1.0 if part=='head' else .2)
assert json.loads((P/'work/trace_source.json').read_text())['sha256']==hashlib.sha256(f.read_bytes()).hexdigest()
report={'path':str(f.relative_to(P)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size,
 'joints':len(joints),'variants':variants,'triangles':tris,'colour_meshes':lods,'shadow_meshes':shadows,
 'clips_seconds':clips,'images':images,'rig_gate_status':'G4/G5 all LODs and exported rotation trace pass; absolute elbow/contact gates fail; see review/triangle_rebake/preservation.json', 'absolute_new_batch_gates':'fail; see review/triangle_rebake/anatomy.json and gate_summary.json; far silhouette and ratio targets also fail','runtime_tests':'not run: batch rules; integrator owns game checks'}
(P/'export/validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
