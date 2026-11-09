"""Preserve rig/animation bytes while updating textures, applying tiers and splitting the runtime attachment."""
import sys,runpy
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(R/'tools'))
from merge_head_material import read_glb,write_glb,compact
for name in ['mm6_lzd_raw.glb','mm6_lzd_lod0.glb','mm6_lzd_lods.glb']:
 path=P/'export'/name;doc,binary=read_glb(path);binary=bytearray(binary);found=0
 for im in doc['images']:
  if im.get('name','').startswith('head_basecolor_1k'):
   raw=(P/'textures/head_basecolor_1k.png').read_bytes();binary.extend(b'\0'*(-len(binary)%4));im['bufferView']=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(raw)});binary.extend(raw);found+=1
 assert found==1,(name,found)
 write_glb(path,*compact(doc,binary))
runpy.run_path(str(P/'scripts/viewer_tiers.py'),run_name='__main__')
def run(path,args):
 sys.argv=[str(path),*map(str,args)];runpy.run_path(str(path),run_name='__main__')
run(P.parent/'claude_shared/region_variants.py',[P/'export/mm6_lzd_lods.glb',P/'export/mm6_lzd.glb',P/'textures/lzd_ramps.json','--extra','Lizard','openyamm_specular=1','--extra','Lizard','openyamm_specular_mask=true'])
run(R/'tools/split_attachment.py',[P/'export/mm6_lzd.glb','--joint','Bow','--body',P/'export/mm6_lzd.glb','--attachment',P/'export/mm6_lzd_bow.glb'])
# The shared head-atlas helper takes two primitives. Park the independently animated arrow/string primitive as
# a temporary mesh so its accessors survive compaction, then restore it; no shared helper changes are needed.
path=P/'export/mm6_lzd.glb';doc,binary=read_glb(path);reservoirs=[]
for i,mesh in enumerate(list(doc['meshes'])):
 if len(mesh['primitives'])!=3:continue
 props=[p for p in mesh['primitives']if 'Bow'in doc['materials'][p['material']]['name']];assert len(props)==1
 mesh['primitives'].remove(props[0]);reservoirs.append((i,len(doc['meshes'])));doc['meshes'].append({'name':f'AnimatedPropReservoir_{i}','primitives':props})
assert len(reservoirs)==4
write_glb(path,doc,binary);run(R/'tools/merge_head_material.py',[path,path]);doc,binary=read_glb(path)
for original,parked in reservoirs:doc['meshes'][original]['primitives']+=doc['meshes'][parked]['primitives']
for _,parked in reversed(reservoirs):assert parked==len(doc['meshes'])-1;doc['meshes'].pop()
write_glb(path,*compact(doc,binary))
runpy.run_path(str(P/'scripts/finalize_materials.py'),run_name='__main__')
print('PACKAGED runtime body, bow, three tiers, four colour and shadow LODs')
