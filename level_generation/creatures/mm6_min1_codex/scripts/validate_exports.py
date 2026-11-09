"""Check staged runtime invariants, exact animation preservation, loader support and palette sharing."""
import json,sys,hashlib,subprocess,importlib.util
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];R=P.parents[2];E=P/'export'
spec=importlib.util.spec_from_file_location('glb',R/'tools/merge_head_material.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def digest_animations(d,b):
 out={}
 for a in d.get('animations',[]):
  rows={}
  for c in a['channels']:
   s=a['samplers'][c['sampler']];key=d['nodes'][c['target']['node']]['name']+':'+c['target']['path'];h=hashlib.sha256()
   for k in ['input','output']:h.update(g.accessor_array(d,b,s[k]).tobytes())
   rows[key]=h.hexdigest()
  out[a['name']]=rows
 return out
source,sb=g.read_glb(E/'mm6_min1_runtime_lod0.glb');animations=digest_animations(source,sb);report={}
for name in ['mm6_min1.glb','mm6_min1_axe.glb']:
 path=E/name;d,b=g.read_glb(path);variants=[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']];assert variants==['min1_a','min1_b','min1_c'];worst=0;levels=[]
 for mesh in d['meshes']:
  count=0
  for p in mesh['primitives']:
   xyz=g.accessor_array(d,b,p['attributes']['POSITION']);assert np.isfinite(xyz).all();count+=d['accessors'][p['indices']]['count']//3
   weights=[g.accessor_array(d,b,v).astype(float) for k,v in p['attributes'].items() if k.startswith('WEIGHTS_')]
   if weights:
    total=sum(x.sum(1) for x in weights);worst=max(worst,float(abs(total-1).max()));assert worst<1e-4,(name,mesh['name'],worst)
  levels.append({'name':mesh['name'],'triangles':count})
 allowed={'KHR_materials_variants','KHR_materials_emissive_strength','KHR_texture_transform'}
 for m in d['materials']:assert set(m.get('extensions',{}))<=allowed
 assert len(d['meshes'][0]['extras']['openyamm_lods'])==3
 # Every tier shares the exact same image payload; only the compact region ramps differ.
 for slot in ['baseColorTexture','metallicRoughnessTexture']:
  assert len({m['pbrMetallicRoughness'][slot]['index'] for m in d['materials']})==1
 if name=='mm6_min1.glb':
  assert set(animations)=={'Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget'}
  assert digest_animations(d,b)==animations,'Runtime postprocessing changed animation samples'
  assert 'Socket_Axe_Head' in {n.get('name') for n in d['nodes']};assert 'Axe' in {n.get('name') for n in d['nodes']};assert len(d['meshes'][0]['extras']['openyamm_shadow_lods'])==4
  assert animations['Attack']!=animations['Cast'],'Cast must be a distinct timed gesture'
 else:assert not d.get('skins') and not d.get('animations')
 report[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'variants':variants,'meshes':levels,'joints':len(d['skins'][0]['joints']) if d.get('skins') else 0,'weight_sum_max_error':worst,'animation_samples_unchanged':True if name=='mm6_min1.glb' else None,'pass':True}
res=subprocess.run([sys.executable,str(R/'output/codex_batch/check_weights.py'),*[str(E/n) for n in report]],capture_output=True,text=True);(P/'review/weights_check.txt').write_text(res.stdout+res.stderr);res.check_returncode();assert 'BAD' not in res.stdout
shared=json.loads((P/'review/round3/shared_gates/gates.json').read_text())
report['mm6_min1.glb']['shared_gate_status']=shared['status']
report['mm6_min1.glb']['validation_scope']='Loader, skin weights, variants, LOD structure and animation preservation only. See shared gates for motion verdict.'
(P/'review/export_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
