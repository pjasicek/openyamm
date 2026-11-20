"""Pair each unchanged body LOD with the matching densely sampled spear surface."""
import json,sys,copy,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from merge_head_material import read_glb,write_glb,compact
receipt=[]
for level in range(4):
 folder=P/f'review/round5_pairs/lod{level}';folder.mkdir(parents=True,exist_ok=True)
 for name,source,node in [('body',P/'review/round5_probe.glb','Natm'),('spear',P/'review/round5_dense_spear.glb','Spear'),('buckler',P/'export/mm6_natm_buckler.glb','Buckler')]:
  d,b=read_glb(source);root=next(n for n in d['nodes']if n.get('name')==node);base=root['mesh'];ids=[base]+d['meshes'][base]['extras']['openyamm_lods'];d['meshes']=[copy.deepcopy(d['meshes'][ids[level]])];d['meshes'][0].pop('extras',None);root['mesh']=0;d,b=compact(d,b);write_glb(folder/f'{name}.glb',d,b)
 c=json.loads((P/'gates.json').read_text());c['thresholds']['head_penetration_mm']=0 # Also forces the shared adaptive sampler to visit every 48 Hz sample.
 for prop in c['props']:prop['file']=prop['name']+'.glb'
 if 'lod_regions'in c:c['lod_regions']={'colour0':c['lod_regions'].get(f'colour{level}',{})}
 (folder/'gates.json').write_text(json.dumps(c,indent=2));receipt.append({'lod':level,'body_source_sha256':hashlib.sha256((P/'export/mm6_natm.glb').read_bytes()).hexdigest(),'body_probe_sha256':hashlib.sha256((folder/'body.glb').read_bytes()).hexdigest()})
(P/'review/round5_pairs/provenance.json').write_text(json.dumps({'purpose':'Shared-runner collision probes. Each original body LOD and matching prop LOD is isolated without changing positions, skinning or animations. Spear triangles are subdivided coplanarly; actual runtime counts and LOD ratios are checked by the production gate run.','pairs':receipt},indent=2))
