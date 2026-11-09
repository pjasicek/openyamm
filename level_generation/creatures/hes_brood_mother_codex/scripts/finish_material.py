"""Keep the authored specular channel: Blender's metallic/roughness exporter replaces unused red with white."""
import sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from normal_map_convention import read_glb,write_glb
path=P/'work/prepared_lod0.glb';doc,data=read_glb(path.read_bytes())
views=[data[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']] for v in doc['bufferViews']]
for mat in doc['materials']:
 tex=mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'];image=doc['images'][doc['textures'][tex]['source']]
 views[image['bufferView']]=(P/'textures/hbm_metal_rough.png').read_bytes();image['mimeType']='image/png';image['name']='hbm_metal_rough'
 mat.setdefault('extras',{})['openyamm_specular_mask']=True
path.write_bytes(write_glb(doc,views))
assert all(m['extras']['openyamm_specular_mask'] for m in read_glb(path.read_bytes())[0]['materials'])
