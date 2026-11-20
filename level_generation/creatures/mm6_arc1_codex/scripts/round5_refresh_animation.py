import sys,shutil,runpy,copy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));sys.dont_write_bytecode=True
from merge_head_material import read_glb,write_glb,accessor_array,append_accessor,compact
p=P/'export/mm6_arc1.glb';d,b=read_glb(P/'work/round5/padded_before_foot.glb');raw,rb=read_glb(p)
def channels(d):
 return {(a['name'],d['nodes'][c['target']['node']]['name'],c['target']['path']):a['samplers'][c['sampler']] for a in d['animations'] for c in a['channels']}
d['animations']=copy.deepcopy(raw['animations']);cache={};nodes={n.get('name'):i for i,n in enumerate(d['nodes'])}
for animation in d['animations']:
 for c in animation['channels']:c['target']['node']=nodes[raw['nodes'][c['target']['node']]['name']]
 for sampler in animation['samplers']:
  for field in ['input','output']:
   ai=sampler[field]
   if ai not in cache:cache[ai]=append_accessor(d,b,accessor_array(raw,rb,ai),raw['accessors'][ai],None)
   sampler[field]=cache[ai]
for a in d['animations']:
 for s in a['samplers']:
  ai=s['input'];v=accessor_array(d,b,ai);d['accessors'][ai].update(min=v.min(0).tolist(),max=v.max(0).tolist())
d,b=compact(d,b)
for n in ['mm6_arc1.glb','mm6_arc1_bow.glb','mm6_arc1_arrow.glb']:shutil.copy2(P/'export'/n,P/'work/round5/runtime_unpadded'/n)
write_glb(p,d,b)
for n in ['mm6_arc1_bow.glb','mm6_arc1_arrow.glb']:shutil.copy2(P/'work/round5'/('padded_'+n),P/'export'/n)
runpy.run_path(str(P/'scripts/round5_arrow_export.py'),run_name='__main__');runpy.run_path(str(P/'scripts/round5_viewer.py'),run_name='__main__')
