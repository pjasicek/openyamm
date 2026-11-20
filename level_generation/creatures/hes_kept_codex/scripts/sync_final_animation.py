"""Copy the final 60 Hz samples to the existing repaired geometry without touching its maps or LODs."""
import sys,copy,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor
from merge_head_material import compact
src,sbin=read_glb(P/'export/hes_kept_m_ragged_lod0.glb');report={}
def geometry(d,b):return hashlib.sha256(b''.join(accessor_bytes(d,b,i) for m in d['meshes'] for p in m['primitives'] for i in [p['indices'],*p['attributes'].values()])).hexdigest()
for stem in ('hes_kept_m_ragged','hes_kept_m_ragged_near'):
 path=P/'export'/f'{stem}.glb';d,raw=read_glb(path);binary=bytearray(raw);before=geometry(d,binary);names={n.get('name'):i for i,n in enumerate(d['nodes'])};cache={};animations=copy.deepcopy(src['animations'])
 for a in animations:
  for sampler in a['samplers']:
   for key in ('input','output'):
    i=sampler[key]
    if i not in cache:cache[i]=append_accessor(d,binary,src['accessors'][i],accessor_bytes(src,sbin,i))
    sampler[key]=cache[i]
  for c in a['channels']:c['target']['node']=names[src['nodes'][c['target']['node']]['name']]
 d['animations']=animations;d,binary=compact(d,binary);assert geometry(d,binary)==before;write_glb(path,d,binary);report[stem]={'unchanged_geometry_sha256':before,'bake_hz':60,'durations_unchanged':True}
(P/'review/final_animation_transfer.json').write_text(json.dumps(report,indent=2)+'\n');print('ANIMATION_TRANSFER',report)
