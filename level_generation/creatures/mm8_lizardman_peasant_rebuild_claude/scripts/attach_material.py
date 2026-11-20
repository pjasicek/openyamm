#!/usr/bin/env python3
"""Give the clipped body GLB its material and runtime names: one material 'LizBase' (base colour 2K, metal/rough and
normal 1K from textures/, openyamm_specular 1 with the per-class mask in MR red, metallic 0, double-sided like the
installed model), node and mesh 'Lizardman_Body' (the name the regression and LOD tools use).
Usage: attach_material.py <in.glb> <out.glb>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb
HERE = Path(__file__).resolve().parents[1]
doc, binary = read_glb(Path(sys.argv[1])); binary = bytearray(binary)
def img(name, file):
    data = (HERE / 'textures' / file).read_bytes()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc.setdefault('bufferViews', []).append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    doc.setdefault('images', []).append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    doc.setdefault('textures', []).append({'source': len(doc['images']) - 1, 'sampler': 0})
    return len(doc['textures']) - 1
doc['samplers'] = [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 33071, 'wrapT': 33071}]
b, mr, n = img('liz_basecolor', 'liz_basecolor.png'), img('liz_metal_rough', 'liz_metal_rough.png'), img('liz_normal', 'liz_normal.png')
doc['materials'] = [{'name': 'LizBase', 'doubleSided': True,
                     'pbrMetallicRoughness': {'baseColorTexture': {'index': b}, 'metallicRoughnessTexture': {'index': mr},
                                              'metallicFactor': 0.0, 'roughnessFactor': 1.0},
                     'normalTexture': {'index': n},
                     'extras': {'openyamm_specular': 1.0, 'openyamm_specular_mask': True}}]
body = next(nd for nd in doc['nodes'] if 'mesh' in nd)
body['name'] = 'Lizardman_Body'; doc['meshes'][body['mesh']]['name'] = 'Lizardman_Body'
for p in doc['meshes'][body['mesh']]['primitives']:
    p['material'] = 0
    assert 'TEXCOORD_0' in p['attributes']
write_glb(Path(sys.argv[2]), doc, bytes(binary)); print('MATERIAL', sys.argv[2])
