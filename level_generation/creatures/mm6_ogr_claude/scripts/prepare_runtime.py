"""Restore the authored specular channel that Blender's glTF MR packing does not carry, then normalize maps."""
from pathlib import Path
import sys
from PIL import Image
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
sys.path.insert(0,str(repo/'tools'))
import merge_head_material as M
from prepare_actor_glb import prepare
src=p/'export/mm6_ogr_lod0.glb';d,b=M.read_glb(src)
for mat in d['materials']:
 name=mat['name'];prefix={'Ogre_A':'ogr','OgreHead_A':'ogr_head'}[name]
 info=mat['pbrMetallicRoughness']['metallicRoughnessTexture'];sampler=d['textures'][info['index']].get('sampler')
 info['index']=M.add_image(d,b,Image.open(p/'textures'/f'{prefix}_metal_rough_1k.png'),prefix+'_material_response',sampler)
 mat.setdefault('extras',{}).update(openyamm_specular=1,openyamm_specular_mask=True)
M.write_glb(src,d,b);prepare(src,p/'export/mm6_ogr_runtime_lod0.glb')
