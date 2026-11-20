"""Restore runtime alpha masks after opaque far-LOD processing; keep variant-aware body shadows."""
from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,write_glb,compact
report={}
for path in sorted((P/'export').glob('*.glb')):
 d,b=read_glb(path)
 for m in d['materials']:
  name=m.get('name','')
  if name.startswith(('HHW_Cloth','HHW_Mantle')):
   m['alphaMode']='MASK';m['alphaCutoff']=.5;m['doubleSided']=True
   factor=m.setdefault('pbrMetallicRoughness',{}).setdefault('baseColorFactor',[1,1,1,1])
   if name.startswith('HHW_Mantle'):factor[3]=int('_BOSS' in name)
  assert 'emissiveTexture' not in m
 if path.stem=='hes_harrower':
  for n in d['nodes']:
   if 'mesh' not in n:continue
   me=d['meshes'][n['mesh']];e=me.get('extras',{})
   # Omit the dedicated shadow chain: the renderer uses colour LODs, preserving variant alpha.
   e.pop('openyamm_shadow_lods',None)
 # Remove now-unreferenced merged shadows; preserve all render and LOD indices.
 used={n['mesh'] for n in d['nodes'] if 'mesh' in n}
 for i in list(used):
  ex=d['meshes'][i].get('extras',{});used.update(ex.get('openyamm_lods',[]));used.update(ex.get('openyamm_shadow_lods',[]))
 order=sorted(used);remap={v:i for i,v in enumerate(order)}
 d['meshes']=[d['meshes'][i] for i in order]
 for n in d['nodes']:
  if 'mesh' in n:n['mesh']=remap[n['mesh']]
 for m in d['meshes']:
  for key in ('openyamm_lods','openyamm_shadow_lods'):
   if key in m.get('extras',{}):m['extras'][key]=[remap[i] for i in m['extras'][key]]
 write_glb(path,*compact(d,b))
 report[path.name]={'mesh_triangles':{m.get('name',str(i)):sum(d['accessors'][pr['indices']]['count']//3 for pr in m['primitives']) for i,m in enumerate(d['meshes'])},'clips':[a['name'] for a in d.get('animations',[])],'variants':[v['name'] for v in d['extensions']['KHR_materials_variants']['variants']]}
(P/'review/runtime_exports.json').write_text(json.dumps(report,indent=2)+'\n')
