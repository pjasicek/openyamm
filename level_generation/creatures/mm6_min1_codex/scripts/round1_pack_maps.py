"""Embed the rebaked maps verbatim, preserving ORM red and the known +Y tangent normals."""
import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb
d,data=read_glb(P/'export/mm6_min1_lod0.glb');b=bytearray(data);report=[]
for mat in d['materials']:
 prefix={'Minotaur_A':'min1_body','MinotaurHead_A':'min1_head','MinotaurAxe':'axe'}[mat['name']]
 for suffix,owner,key in [('basecolor',mat['pbrMetallicRoughness'],'baseColorTexture'),('metal_rough',mat['pbrMetallicRoughness'],'metallicRoughnessTexture'),('normal',mat,'normalTexture')]:
  source=P/'textures/round1_rebaked'/f'{prefix}_{suffix}.png';payload=source.read_bytes();assert payload.startswith(b'\x89PNG')
  b.extend(b'\0'*(-len(b)%4));view=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(payload)});b.extend(payload)
  im=len(d['images']);d['images'].append({'bufferView':view,'mimeType':'image/png','name':source.stem});tex=len(d['textures']);d['textures'].append({'source':im});owner[key]={'index':tex};report.append(str(source.relative_to(P)))
 mat['pbrMetallicRoughness']['metallicFactor']=0
write_glb(P/'export/mm6_min1_runtime_lod0.glb',d,b)
(P/'review/round3/map_embedding.json').write_text(json.dumps({'normal_convention':'Cycles baked +Y tangent, no second flip','maps':report},indent=2))
