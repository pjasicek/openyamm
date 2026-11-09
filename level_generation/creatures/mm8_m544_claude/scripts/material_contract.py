"""Preserve the engine's specular-in-red packing instead of Blender's optional glTF specular extension."""
import sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from normal_map_convention import read_glb,write_glb

def finish(path):
    document,binary=read_glb(path.read_bytes())
    views=[binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']] for v in document['bufferViews']]
    images=set()
    for material in document['materials']:
        extensions=material.get('extensions',{})
        extensions.pop('KHR_materials_specular',None)
        if not extensions:
            material.pop('extensions',None)
        if material['name']=='BreathCloud':
            material.setdefault('extensions',{})['KHR_materials_unlit']={}
            material['extras']={'openyamm_specular':0,'openyamm_edge_darkening':0}
            document.setdefault('extensionsUsed',[]).append('KHR_materials_unlit')
            continue
        material.setdefault('extras',{}).update(openyamm_specular=1,openyamm_specular_mask=True)
        index=material['pbrMetallicRoughness']['metallicRoughnessTexture']['index']
        images.add(document['textures'][index]['source'])
    assert len(images)==1
    for index in images:
        image=document['images'][index]
        views[image['bufferView']]=(P/'textures/unicorn_metal_rough_1k.png').read_bytes()
        image['mimeType']='image/png'
    for key in ['extensionsUsed','extensionsRequired']:
        if key in document:
            document[key]=[name for name in document[key] if name!='KHR_materials_specular']
            if not document[key]:document.pop(key)
    path.write_bytes(write_glb(document,views))
    print('MATERIAL CONTRACT',path.name)

if __name__=='__main__':
    for argument in sys.argv[1:]:
        finish(Path(argument))
