#!/usr/bin/env python3
"""Drop materials no primitive or colour-variant mapping uses, then the textures and images only they used, and
compact the buffer. The Knight's old per-LOD materials (KnightPlate_*_LOD1-3) and their LOD normal maps stay in the
file after build_actor_lods.py points every new LOD at the LOD0 material. Usage: prune_materials.py <glb> (in place)"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

path = Path(sys.argv[1])
doc, binary = read_glb(path)
prims = [p for m in doc['meshes'] for p in m['primitives']]
used_mat = sorted({p['material'] for p in prims if 'material' in p} |
                  {mp['material'] for p in prims for mp in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])})
mat_map = {old: new for new, old in enumerate(used_mat)}
dropped = [m['name'] for i, m in enumerate(doc['materials']) if i not in mat_map]
doc['materials'] = [doc['materials'][i] for i in used_mat]
for p in prims:
    if 'material' in p:
        p['material'] = mat_map[p['material']]
    for mp in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
        mp['material'] = mat_map[mp['material']]


def texture_infos(node):
    # every textureInfo object in a material, extensions and extras included
    if isinstance(node, dict):
        for key, value in node.items():
            # standard slots (*Texture) and engine extras (openyamm_region_mask, openyamm_burn_map): materials hold no
            # other {"index": n} objects
            if isinstance(value, dict) and isinstance(value.get('index'), int):
                yield value
            else:
                yield from texture_infos(value)
    elif isinstance(node, list):
        for value in node:
            yield from texture_infos(value)


infos = list(texture_infos(doc['materials']))
used_tex = sorted({t['index'] for t in infos}); tex_map = {old: new for new, old in enumerate(used_tex)}
for t in infos:
    t['index'] = tex_map[t['index']]
doc['textures'] = [doc['textures'][i] for i in used_tex]
used_img = sorted({t['source'] for t in doc['textures']}); img_map = {old: new for new, old in enumerate(used_img)}
for t in doc['textures']:
    t['source'] = img_map[t['source']]
dropped_img = [im.get('name') for i, im in enumerate(doc['images']) if i not in img_map]
doc['images'] = [doc['images'][i] for i in used_img]

used_views = sorted({a['bufferView'] for a in doc['accessors'] if 'bufferView' in a} |
                    {im['bufferView'] for im in doc['images'] if 'bufferView' in im})
view_map, newbin, views = {}, bytearray(), []
for new, old in enumerate(used_views):
    v = copy.deepcopy(doc['bufferViews'][old]); start = v.get('byteOffset', 0)
    newbin.extend(b'\0' * (-len(newbin) % 4)); v['byteOffset'] = len(newbin)
    newbin.extend(binary[start:start + v['byteLength']]); views.append(v); view_map[old] = new
doc['bufferViews'] = views
for item in doc['accessors'] + doc['images']:
    if 'bufferView' in item:
        item['bufferView'] = view_map[item['bufferView']]
doc['buffers'][0]['byteLength'] = len(newbin)
write_glb(path, doc, bytes(newbin))
print('PRUNED materials', dropped, 'images', dropped_img, f'{len(binary) / 1e6:.1f} -> {len(newbin) / 1e6:.1f} MB')
