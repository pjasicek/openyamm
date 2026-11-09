#!/usr/bin/env python3
"""Review-only GLB: body GLB with the bow GLB's LOD0 mesh attached as a child of the body's Bow joint (the engine
attaches the bow model's node at that joint, so bow vertices are in the joint frame). Materials, textures and colour
variant mappings come along with remapped indices. Not a runtime asset. Usage: merge_bow_viewer.py <body> <bow> <out>"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

doc, binary = read_glb(Path(sys.argv[1])); binary = bytearray(binary)
bow, bbin = read_glb(Path(sys.argv[2]))
img0, tex0, smp0, mat0 = (len(doc.get(k, [])) for k in ('images', 'textures', 'samplers', 'materials'))
for im in bow['images']:
    v = bow['bufferViews'][im['bufferView']]; s = v.get('byteOffset', 0); data = bytes(bbin[s:s + v['byteLength']])
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
    doc['images'].append({**{k: x for k, x in im.items() if k != 'bufferView'}, 'bufferView': len(doc['bufferViews']) - 1})
doc.setdefault('samplers', []).extend(copy.deepcopy(bow.get('samplers', [])))
for t in bow['textures']:
    doc['textures'].append({'source': t['source'] + img0, **({'sampler': t['sampler'] + smp0} if 'sampler' in t else {})})


def remap_tex(x, key=''):
    if isinstance(x, dict):
        for k, v in x.items():
            if k == 'index' and (key.endswith('Texture') or key.endswith('mask')):
                x[k] = v + tex0
            else:
                remap_tex(v, k)
    elif isinstance(x, list):
        for v in x:
            remap_tex(v, key)


for m in bow['materials']:
    m = copy.deepcopy(m); remap_tex(m); doc['materials'].append(m)
bnode = next(n for n in bow['nodes'] if 'mesh' in n)
mesh = copy.deepcopy(bow['meshes'][bnode['mesh']]); mesh.pop('extras', None)
for p in mesh['primitives']:
    p['attributes'] = {k: append_accessor(doc, binary, bow['accessors'][i], accessor_bytes(bow, bbin, i)) for k, i in p['attributes'].items()}
    p['indices'] = append_accessor(doc, binary, bow['accessors'][p['indices']], accessor_bytes(bow, bbin, p['indices']))
    p['material'] += mat0
    for mp in p.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
        mp['material'] += mat0
doc['meshes'].append(mesh)
doc['nodes'].append({'name': 'BowModel', 'mesh': len(doc['meshes']) - 1,
                     **{k: bnode[k] for k in ('translation', 'rotation', 'scale') if k in bnode}})
joint = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == 'Bow')
doc['nodes'][joint].setdefault('children', []).append(len(doc['nodes']) - 1)
write_glb(Path(sys.argv[3]), doc, bytes(binary))
print('MERGED bow into', sys.argv[3])
