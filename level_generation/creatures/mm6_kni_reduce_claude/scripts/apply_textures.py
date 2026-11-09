#!/usr/bin/env python3
"""Set a GLB's material maps from PNG files: base colour, normal and metal/roughness (glTF ORM) per material name.
New images and textures are appended (the old ones become unreferenced; region_variants.py / prune_materials.py drop
them). The region mask and ramps are set later by claude_shared/region_variants.py.
Usage: apply_textures.py <in.glb> <out.glb> <maps.json>
maps.json: {"<material>": {"base": "<png>", "normal": "<png>", "mr": "<png>"}, ...} (paths relative to the json)"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

src, dst, cfg_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
cfg = json.loads(cfg_path.read_text())
doc, binary = read_glb(src); binary = bytearray(binary)
sampler = 0 if doc.get('samplers') else None


def add_image(path, name):
    data = (cfg_path.parent / path).read_bytes()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    doc['images'].append({'name': name, 'mimeType': 'image/png', 'bufferView': len(doc['bufferViews']) - 1})
    tex = {'source': len(doc['images']) - 1}
    if sampler is not None:
        tex['sampler'] = sampler
    doc['textures'].append(tex)
    return len(doc['textures']) - 1


for mat in doc['materials']:
    maps = cfg.get(mat['name'])
    if not maps:
        continue
    pbr = mat.setdefault('pbrMetallicRoughness', {})
    pbr['baseColorTexture'] = {'index': add_image(maps['base'], Path(maps['base']).stem)}
    pbr['metallicRoughnessTexture'] = {'index': add_image(maps['mr'], Path(maps['mr']).stem)}
    mat['normalTexture'] = {'index': add_image(maps['normal'], Path(maps['normal']).stem)}
    print('MAPS', mat['name'], maps)
doc['buffers'][0]['byteLength'] = len(binary)
write_glb(dst, doc, bytes(binary))
