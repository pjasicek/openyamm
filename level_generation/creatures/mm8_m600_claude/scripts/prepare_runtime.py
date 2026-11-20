from pathlib import Path
import sys,json
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
import prepare_actor_glb as prep,merge_head_material as G
src=P/'export/mm8_m600_lod0.glb';out=P/'export/mm8_m600_prepared.glb';prep.prepare(src,out)
d,b=G.read_glb(out)
assert len(d['materials'])==1 and d['materials'][0]['name']=='Nightmare'
m=d['materials'][0]
# Keep the specular mask in R; Blender's metallic/roughness packing treats R as unused.
ti=m['pbrMetallicRoughness']['metallicRoughnessTexture']['index'];im=d['images'][d['textures'][ti]['source']];raw=(P/'textures/body_orm.png').read_bytes();b.extend(b'\0'*(-len(b)%4));im['bufferView']=len(d['bufferViews']);im['mimeType']='image/png';d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(raw)});b.extend(raw)
G.write_glb(out,d,b)
