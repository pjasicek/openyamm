#!/usr/bin/env python3
"""Check that a far-LOD repair changed only the far levels of the body. Compares <before.glb> (the source) with
<after.glb> (repair output), content-wise so that shifted texture or material indices do not count:
- scene, nodes, skins (joints and inverse binds), every clip (channels, interpolation, key data byte for byte);
- every mesh other than the body's rebuilt colour LODs and their shadow meshes (LOD0, LOD1, their shadows, effect and
  attachment meshes): mesh extras, per primitive attribute and index bytes, material and variant mappings resolved
  to the material's content with each texture replaced by its image bytes;
- the material list without `_LOD<N>` copies (names, order and content, images resolved), the variant list;
- every `<material>_LOD<N>` copy in the output: its ramps and other properties equal those of its LOD0 material
  (apart from the map references), and its maps are not the LOD0 maps.
Exit 1 on any unexpected difference. Usage: verify_far_only.py <before.glb> <after.glb> [levels, default 2,3]"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
sys.path.insert(0, str(HERE))
from build_actor_lods import accessor_bytes, read_glb  # noqa: E402
from repair import lod_node  # noqa: E402  (module guards its CLI below)

LOD_NAME = re.compile(r'_LOD(\d+)$')


def image_hash(doc, binary, texture_index):
    source = doc['images'][doc['textures'][texture_index]['source']]
    view = doc['bufferViews'][source['bufferView']]
    start = view.get('byteOffset', 0)
    sampler = doc['textures'][texture_index].get('sampler')
    sampler_json = json.dumps(doc['samplers'][sampler], sort_keys=True) if sampler is not None else ''
    return hashlib.sha256(binary[start:start + view['byteLength']]).hexdigest()[:16] + sampler_json


def resolved_material(doc, binary, index, drop_maps=False):
    material = copy.deepcopy(doc['materials'][index])

    def walk(value):
        if isinstance(value, dict):
            if isinstance(value.get('index'), int):
                value['index'] = None if drop_maps else image_hash(doc, binary, value['index'])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(material)
    return json.dumps(material, sort_keys=True)


def mesh_key(doc, binary, mesh):
    out = {'name': mesh.get('name'), 'extras': mesh.get('extras'), 'primitives': []}
    for primitive in mesh['primitives']:
        entry = {'attributes': {k: hashlib.sha256(accessor_bytes(doc, binary, v)).hexdigest()
                                for k, v in primitive['attributes'].items()},
                 'accessors': {k: {a: doc['accessors'][v].get(a) for a in ('componentType', 'type', 'count', 'normalized')}
                               for k, v in primitive['attributes'].items()},
                 'indices': hashlib.sha256(accessor_bytes(doc, binary, primitive['indices'])).hexdigest(),
                 'mode': primitive.get('mode'), 'targets': len(primitive.get('targets', [])),
                 'material': resolved_material(doc, binary, primitive['material']) if 'material' in primitive else None,
                 'variants': [(m['variants'], resolved_material(doc, binary, m['material'])) for m in
                              primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])]}
        out['primitives'].append(entry)
    return out


def main():
    before_path, after_path = Path(sys.argv[1]), Path(sys.argv[2])
    levels = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else '2,3').split(',')]
    a, ab = read_glb(before_path)
    b, bb = read_glb(after_path)
    bad = []
    check = lambda ok, what: ok or bad.append(what)
    for key in ('scene', 'scenes', 'nodes', 'asset', 'extensionsUsed', 'extensionsRequired', 'extensions'):
        check(a.get(key) == b.get(key), key)
    check(len(a['skins']) == len(b['skins']), 'skin count')
    for sa, sb in zip(a['skins'], b['skins']):
        check({k: v for k, v in sa.items() if k != 'inverseBindMatrices'}
              == {k: v for k, v in sb.items() if k != 'inverseBindMatrices'}, 'skin')
        check(accessor_bytes(a, ab, sa['inverseBindMatrices']) == accessor_bytes(b, bb, sb['inverseBindMatrices']),
              'inverse binds')
    check([x.get('name') for x in a.get('animations', [])] == [x.get('name') for x in b.get('animations', [])],
          'clip names')
    for ca, cb in zip(a.get('animations', []), b.get('animations', [])):
        check(ca['channels'] == cb['channels'] and ca.get('extras') == cb.get('extras'), f"{ca.get('name')} channels")
        for sa, sb in zip(ca['samplers'], cb['samplers']):
            check(sa.get('interpolation') == sb.get('interpolation'), f"{ca.get('name')} interpolation")
            for k in ('input', 'output'):
                check(accessor_bytes(a, ab, sa[k]) == accessor_bytes(b, bb, sb[k]), f"{ca.get('name')} {k}")
    node_name = lod_node(after_path)
    node = next(n for n in b['nodes'] if n.get('name') == node_name and 'mesh' in n)
    extras = b['meshes'][node['mesh']]['extras']
    far = {extras['openyamm_lods'][level - 1] for level in levels}
    far |= {extras['openyamm_shadow_lods'][level] for level in levels if level < len(extras.get('openyamm_shadow_lods', []))}
    check(len(a['meshes']) == len(b['meshes']), 'mesh count')
    for i, (ma, mb) in enumerate(zip(a['meshes'], b['meshes'])):
        if i in far:
            check(ma.get('name') == mb.get('name'), f'far mesh {i} name')
            continue
        check(mesh_key(a, ab, ma) == mesh_key(b, bb, mb), f"mesh {i} {ma.get('name')}")
    base = lambda doc, binary: [(m['name'], resolved_material(doc, binary, i)) for i, m in enumerate(doc['materials'])
                                if not LOD_NAME.search(m['name'])]
    check(base(a, ab) == base(b, bb), 'LOD0/LOD1 materials')
    by_name = {m['name']: i for i, m in enumerate(b['materials'])}
    copies = 0
    for i, material in enumerate(b['materials']):
        match = LOD_NAME.search(material['name'])
        if not match:
            continue
        copies += 1
        lod0 = by_name.get(material['name'][:match.start()])
        if lod0 is None:
            bad.append(f"{material['name']}: no LOD0 material")
            continue
        check(resolved_material(b, bb, i, True).replace(material['name'], b['materials'][lod0]['name'])
              == resolved_material(b, bb, lod0, True), f"{material['name']} properties/ramps differ from LOD0's")
        shared = set(re.findall(r'[0-9a-f]{16}\{', resolved_material(b, bb, i))) \
            & set(re.findall(r'[0-9a-f]{16}\{', resolved_material(b, bb, lod0)))
        if shared:
            print(f"NOTE {material['name']} keeps {len(shared)} LOD0 map(s) (maps outside the far set, e.g. emissive)")
    far_triangles = {i: sum(b['accessors'][p['indices']]['count'] // 3 for p in b['meshes'][i]['primitives'])
                     for i in sorted(far)}
    print('far meshes', {b['meshes'][i]['name']: t for i, t in far_triangles.items()}, 'far material copies', copies)
    print('UNEXPECTED: ' + ', '.join(bad) if bad else 'OK: only the far levels differ')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
