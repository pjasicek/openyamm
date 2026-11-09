"""Merge the measured levels, their baked materials, colour tiers and rigid attachment."""
import sys,copy,json,struct,subprocess,os
from pathlib import Path
sys.dont_write_bytecode=True;os.environ['PYTHONDONTWRITEBYTECODE']='1'
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor,merge_shadow
doc,payload=read_glb(P/'export/mm6_mfp_level0.glb');binary=bytearray(payload);node=next(n for n in doc['nodes']if n.get('name')=='PeasantF3');assert node['mesh']==0
joints=[doc['nodes'][i]['name']for i in doc['skins'][node['skin']]['joints']];binds=list(struct.iter_unpack('<16f',accessor_bytes(doc,binary,doc['skins'][node['skin']]['inverseBindMatrices'])))
def append_bytes(payload):
 binary.extend(b'\0'*(-len(binary)%4));index=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(payload)});binary.extend(payload);return index
def material_map(src,data):
 # Decimation retained UV islands: every LOD uses the same corrected body/head/knife set.
 import re
 names={m['name']:i for i,m in enumerate(doc['materials'])}
 return {i:names[re.sub(r'_LOD[1-3]', '',m['name'])] for i,m in enumerate(src['materials'])}
for level in range(1,4):
 src,data=read_glb(P/f'export/mm6_mfp_level{level}.glb');n=next(n for n in src['nodes']if n.get('name')=='PeasantF3');skin=src['skins'][n['skin']];remap=[joints.index(src['nodes'][i]['name'])for i in skin['joints']];matrices=list(struct.iter_unpack('<16f',accessor_bytes(src,data,skin['inverseBindMatrices'])));assert max(abs(a-b)for j,m in zip(remap,matrices)for a,b in zip(binds[j],m))<1e-4
 mmap=material_map(src,data);mesh={'name':f'PeasantF3_LOD{level}','primitives':[]}
 for p in src['meshes'][n['mesh']]['primitives']:
  attributes={}
  for semantic,index in p['attributes'].items():
   accessor=src['accessors'][index];packed=accessor_bytes(src,data,index)
   if semantic.startswith('JOINTS_'):
    code={5121:'B',5123:'H'}[accessor['componentType']];values=[remap[x[0]]for x in struct.iter_unpack('<'+code,packed)];packed=struct.pack('<'+code*len(values),*values)
   attributes[semantic]=append_accessor(doc,binary,accessor,packed)
  index=p['indices'];mesh['primitives'].append({'attributes':attributes,'indices':append_accessor(doc,binary,src['accessors'][index],accessor_bytes(src,data,index)),'material':mmap[p['material']]})
 doc['meshes'].append(mesh)
for mesh in doc['meshes'][:4]:doc['meshes'].append(merge_shadow(doc,binary,mesh))
doc['meshes'][0]['extras']={'openyamm_lods':[1,2,3],'openyamm_shadow_lods':[4,5,6,7]}
write_glb(P/'export/mm6_mfp_lods.glb',doc,binary)
selection=json.loads((P/'review/reduction_soft/selection.json').read_text());base=json.loads((P/'textures/mfp_ramps.json').read_text());cfg={'variants':base['variants'],'materials':[]}
for level in range(1):
 suffix=''if level==0 else f'_LOD{level}'
 for original,stem in zip(base['materials'],['mfp','mfp_head']):
  entry=copy.deepcopy(original);entry['prefix']+=suffix;entry['base']=entry['prefix']+'_A';entry['mask']=os.path.relpath(Path(selection[str(level)]['textures'])/f'{stem}_region_mask.png',P/'textures');cfg['materials'].append(entry)
(P/'textures/runtime_ramps.json').write_text(json.dumps(cfg,indent=2))
def run(path,args):subprocess.run([sys.executable,str(path),*map(str,args)],check=True)
run(P/'scripts/shrink_shadow_lods.py',[P/'export/mm6_mfp_lods.glb',P/'work/lods_shadow.glb'])
run(P.parent/'claude_shared/region_variants.py',[P/'work/lods_shadow.glb',P/'work/tiers_combined.glb',P/'textures/runtime_ramps.json','--extra','PeasantF3','openyamm_specular=1','--extra','PeasantF3','openyamm_specular_mask=true','--extra','PeasantF3','pbr.metallicFactor=0','--extra','Knife','openyamm_specular=1','--extra','Knife','openyamm_specular_mask=true','--extra','Knife','pbr.metallicFactor=0'])
run(ROOT/'tools/split_attachment.py',[P/'work/tiers_combined.glb','--joint','Knife','--body',P/'export/mm6_mfp.glb','--attachment',P/'export/mm6_mfp_knife.glb'])
run(P/'scripts/merge_head_lods.py',[P/'export/mm6_mfp.glb',P/'export/mm6_mfp.glb'])

run(P/'scripts/pack_prop_lods.py',[])
