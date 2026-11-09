"""Pack one texture set shared by all colour LODs, without resampling motion."""
import sys,json,copy,runpy,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'tools'))
from merge_head_material import read_glb,write_glb,compact
from build_actor_lods import accessor_bytes
runpy.run_path(str(P/'scripts/round3_pack_lods.py'),run_name='__main__')
metadata=json.loads((P/'review/rebake/round4_shared_bake.json').read_text());config=json.loads((P/'textures/lzd_ramps.json').read_text());entries=[]
for item in metadata.values():
 entry=copy.deepcopy(next(e for e in config['materials']if e['base']==item['base_material']));entry['base']=item['material'];entry['mask']=str(Path(item['paths']['regions']).relative_to('textures'));entries.append(entry)
config['materials']=entries;(P/'textures/rebake_lod0_ramps.json').write_text(json.dumps(config,indent=2))
runpy.run_path(str(P/'scripts/viewer_tiers.py'),run_name='__main__')
def run(path,args):
 sys.argv=[str(path),*map(str,args)];runpy.run_path(str(path),run_name='__main__')
run(P.parent/'claude_shared/region_variants.py',[P/'export/mm6_lzd_lods.glb',P/'export/mm6_lzd.glb',P/'textures/rebake_lod0_ramps.json','--extra','Lizard','openyamm_specular=1','--extra','Lizard','openyamm_specular_mask=true'])
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

receipt={}
for stem in ['mm6_lzd','mm6_lzd_bow']:
 path=P/f'export/{stem}.glb';d,b=read_glb(path);m=d['meshes'][0];levels=[0]+m['extras']['openyamm_lods'];counts=[sum(d['accessors'][p['indices']]['count']//3 for p in d['meshes'][i]['primitives'])for i in levels]
 materials=[sorted({p['material']for p in d['meshes'][i]['primitives']})for i in levels]
 assert all(x==materials[0]for x in materials),materials
 receipt[stem]={'triangles':counts,'image_count':len(d['images']),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'shared_lod_material_indices':materials}
 if stem=='mm6_lzd':
  clips={a['name']:a for a in d['animations']}
  def channels(a):
   return {(c['target']['node'],c['target']['path']):tuple(accessor_bytes(d,b,a['samplers'][c['sampler']][k])for k in ['input','output'])for c in a['channels']}
  assert channels(clips['Attack'])==channels(clips['Cast']),'Cast must remain an exact Attack copy'
(P/'review/round4/exports.json').write_text(json.dumps(receipt,indent=2))
(P/'export/lods.json').write_text(json.dumps({'body':receipt['mm6_lzd']['triangles'],'bow':receipt['mm6_lzd_bow']['triangles'],'method':'Protected geometry reduction; one shared 2048 body / 1024 head / 1024 bow texture set, 16 px dilation; four colour and shadow LODs.'},indent=2))
print(json.dumps(receipt,indent=2))
