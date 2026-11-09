"""Restore each rebaked staff material after the shared attachment splitter selects LOD0's material."""
from pathlib import Path
import sys,copy,numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes
path=p/'export/mm6_sor1_staff.glb';d,b=read_glb(path);b=bytearray(b)
# The splitter crop covers the complete staff atlas: verify UVs against each original lower LOD.
for level in range(1,4):
 source,raw=read_glb(p/'export'/f'mm6_sor1_lod{level}.glb')
 src=next(pr for m in source['meshes'] for pr in m['primitives'] if 'Staff' in source['materials'][pr['material']]['name'])
 pr=d['meshes'][level]['primitives'][0]
 a=np.frombuffer(accessor_bytes(source,raw,src['attributes']['TEXCOORD_0']),'<f4')
 c=np.frombuffer(accessor_bytes(d,b,pr['attributes']['TEXCOORD_0']),'<f4')
 assert a.shape==c.shape and np.max(np.abs(a-c))<1e-6, 'Unexpected staff UV crop'
 mat=copy.deepcopy(d['materials'][0]);mat['name']=f'SorcererStaffLOD{level}'
 for channel,slot in [('basecolor',mat['pbrMetallicRoughness']['baseColorTexture']),('orm',mat['pbrMetallicRoughness']['metallicRoughnessTexture']),('normal',mat['normalTexture'])]:
  name=f'r3_lod{level}_SorcererStaff_{channel}';data=(p/'textures/round3'/f'{name}.png').read_bytes();b.extend(b'\0'*(-len(b)%4))
  d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(data)});b.extend(data)
  d['images'].append({'bufferView':len(d['bufferViews'])-1,'mimeType':'image/png','name':name})
  d['textures'].append({'source':len(d['images'])-1,'sampler':0});slot['index']=len(d['textures'])-1
 index=len(d['materials']);d['materials'].append(mat);pr['material']=index
 for mapping in pr.get('extensions',{}).get('KHR_materials_variants',{}).get('mappings',[]):mapping['material']=index
write_glb(path,d,b)
print('Staff LOD rebakes connected: 1024/512/256/128; geometry and LOD0 unchanged')
