"""Assert skin, texture, animation and LOD contracts on every final primitive."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array
report={}
for name in ['mm6_mfp.glb','mm6_mfp_knife.glb']:
 path=P/'export'/name;doc,data=read_glb(path);row={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'joints':max([len(s['joints'])for s in doc.get('skins',[])]or[0]),'meshes':[],'extensions_used':doc.get('extensionsUsed',[]),'clips':[]};assert row['joints']<=128
 for mi,m in enumerate(doc['meshes']):
  mr={'name':m.get('name'),'triangles':0,'weight_error':0,'max_influences':0,'primitives':len(m['primitives'])}
  for p in m['primitives']:
   attrs=p['attributes'];mr['triangles']+=doc['accessors'][p['indices']]['count']//3
   for sem,index in attrs.items():assert np.isfinite(accessor_array(doc,data,index)).all(),(name,mi,sem)
   weights=[accessor_array(doc,data,index)for sem,index in attrs.items()if sem.startswith('WEIGHTS_')]
   if weights:
    w=np.concatenate(weights,axis=1);err=float(abs(w.sum(1)-1).max());mr['weight_error']=max(mr['weight_error'],err);mr['max_influences']=max(mr['max_influences'],int((w>0).sum(1).max()));assert err<=1e-4,(name,mi,err);assert mr['max_influences']<=8
  row['meshes'].append(mr)
 for mat in doc.get('materials',[]):
  assert not mat.get('extensions'),(name,mat.get('name'),mat.get('extensions'))
  e=mat.get('extras',{});ramps=e.get('openyamm_region_ramps')
  if ramps:
   assert 'openyamm_region_mask'in e and 1<=len(ramps)<=4
   assert all(len(x['colors'])==16 for x in ramps)
 for a in doc.get('animations',[]):
  assert all(s.get('interpolation','LINEAR')in['LINEAR','STEP']for s in a['samplers'])
  row['clips'].append(a['name'])
 if name=='mm6_mfp.glb':
  assert set(row['clips'])=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
  assert [x['name']for x in doc['extensions']['KHR_materials_variants']['variants']]==['mfp_a','mfp_b','mfp_c']
 base=next(n for n in doc['nodes']if 'mesh'in n);m=doc['meshes'][base['mesh']];extra=m['extras'];colour=[base['mesh']]+extra['openyamm_lods'];shadow=extra['openyamm_shadow_lods'];assert len(colour)==len(shadow)==4
 for kind,ids in [('colour',colour),('shadow',shadow)]:
  counts=[row['meshes'][i]['triangles']for i in ids];assert all(a>b for a,b in zip(counts,counts[1:])),(name,kind,counts);row[kind+'_triangles']=counts
 report[name]=row
(P/'review/runtime_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
