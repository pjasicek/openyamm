#!/usr/bin/env python3
"""Put the LOD textures (unwrap_lods.py, transfer_textures.py) into a built GLB (build_lods.py).

Per level, each colour LOD primitive whose material has textures gets new vertices (its LOD vertex with the new UV per
triangle corner, deduplicated), a new index buffer, and copies of its default and variant materials named
<name>_LOD<N> that point at the level's own images for the maps the material has (base colour, metal/roughness, normal,
region mask). Region ramps and every other material property are copied unchanged, so the colour tiers keep working.
Untextured primitives and shadow
meshes are untouched. Unused buffer data is compacted.
Usage: apply_bake.py <built.glb> <node> <unwrap dir> <out.glb> <level,...>"""
import copy
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
sys.path.insert(0, str(HERE))
from build_actor_lods import append_accessor, read_glb, write_glb  # noqa: E402
from build_lods import rows  # noqa: E402
from splice_lods import compact, triangles  # noqa: E402
from transfer_textures import material_maps, own_map_variants, unwrapped_uvs  # noqa: E402


def add_image(doc, binary, name, path, sampler):
    binary.extend(b'\0' * (-len(binary) % 4))
    data = path.read_bytes()
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    texture = {'source': len(doc['images']) - 1}
    if sampler is not None:
        texture['sampler'] = sampler
    doc['textures'].append(texture)
    return len(doc['textures']) - 1


def lod_material(doc, index, level, textures):
    """Copy of material `index` for one LOD level with that level's textures (cached by name)."""
    source = doc['materials'][index]
    name = f'{source["name"]}_LOD{level}'
    for i, material in enumerate(doc['materials']):
        if material['name'] == name:
            return i
    material = copy.deepcopy(source)
    material['name'] = name
    pbr = material.get('pbrMetallicRoughness', {})
    if 'basecolor' in textures:
        pbr['baseColorTexture'] = {'index': textures['basecolor']}
    if 'mr' in textures:
        pbr['metallicRoughnessTexture'] = {'index': textures['mr']}
    if 'normal' in textures:
        # The transferred normal map already carries LOD0's normal-map strength.
        material['normalTexture'] = {'index': textures['normal']}
    if 'mask' in textures:
        material['extras']['openyamm_region_mask'] = {'index': textures['mask']}
    doc['materials'].append(material)
    return len(doc['materials']) - 1


def main():
    built, node_name, bake_dir, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
    levels = [int(x) for x in sys.argv[5].split(',')]
    doc, binary = read_glb(built)
    binary = bytearray(binary)
    node = next(n for n in doc['nodes'] if n.get('name') == node_name and 'mesh' in n)
    lod0 = doc['meshes'][node['mesh']]
    if any(m['name'].endswith(tuple(f'_LOD{level}' for level in levels)) for m in doc['materials']):
        raise ValueError('the input already has baked LOD materials: rebuild from the original GLB')
    for level in levels:
        unwrapped = np.load(bake_dir / f'lod{level}.npz')
        mesh = doc['meshes'][lod0['extras']['openyamm_lods'][level - 1]]
        new_primitives = []
        for index, primitive in enumerate(mesh['primitives']):
            primitive_index = index  # `index` is reused for accessors below
            material = doc['materials'][primitive['material']]
            kinds = material_maps(material)
            if not kinds:
                new_primitives.append(primitive)
                continue
            first = next(iter(kinds.values()))
            sampler = doc['textures'][first].get('sampler')
            textures = {kind: add_image(doc, binary, f'{material["name"]}_lod{level}_{kind}',
                                        bake_dir / f'lod{level}_p{index}_{kind}.png', sampler) for kind in kinds}
            faces, face_uv = unwrapped_uvs(doc, binary, primitive, index, unwrapped)
            corners = [[(int(v), tuple(np.round(uv, 7))) for v, uv in zip(triangle, uvs)]
                       for triangle, uvs in zip(faces, face_uv)]
            keys = sorted({c for triangle in corners for c in triangle})
            index_of = {key: i for i, key in enumerate(keys)}
            references = np.array([v for v, _ in keys])
            new_uv = np.array([uv for _, uv in keys], dtype=np.float32)
            out_primitive = {'attributes': {}, 'material': lod_material(doc, primitive['material'], level, textures)}
            for semantic, index in primitive['attributes'].items():
                accessor = copy.deepcopy(doc['accessors'][index])
                data = new_uv.view(np.uint8).reshape(len(keys), -1) if semantic == 'TEXCOORD_0' \
                    else rows(doc, binary, index)[references]
                accessor['count'] = len(keys)
                accessor.pop('min', None)
                accessor.pop('max', None)
                if semantic == 'POSITION':
                    values = data.copy().view(np.float32).reshape(-1, 3)
                    accessor['min'], accessor['max'] = values.min(0).tolist(), values.max(0).tolist()
                out_primitive['attributes'][semantic] = append_accessor(doc, binary, accessor, data.tobytes())
            indices = np.array([[index_of[c] for c in triangle] for triangle in corners])
            index_type = 5123 if len(keys) < 65536 else 5125
            out_primitive['indices'] = append_accessor(
                doc, binary, {'componentType': index_type, 'type': 'SCALAR', 'count': indices.size},
                indices.astype(np.uint16 if index_type == 5123 else np.uint32).tobytes())
            if 'extensions' in primitive:
                extension = copy.deepcopy(primitive['extensions'])
                own = own_map_variants(doc, primitive)
                for mapping in extension.get('KHR_materials_variants', {}).get('mappings', []):
                    variant = mapping['material']
                    variant_kinds = material_maps(doc['materials'][variant])
                    if variant in own:
                        # Maps shared with the default at LOD0 keep the default's far map.
                        stem = f'lod{level}_p{primitive_index}_m{variant}'
                        variant_name = doc['materials'][variant]['name']
                        variant_textures = {kind: textures[kind] if kinds.get(kind) == t
                                            else add_image(doc, binary, f'{variant_name}_lod{level}_{kind}',
                                                           bake_dir / f'{stem}_{kind}.png', sampler)
                                            for kind, t in variant_kinds.items()}
                    else:
                        # Same maps as the default: share its far maps, only those the variant has (no mask
                        # without ramps).
                        variant_textures = {kind: t for kind, t in textures.items() if kind in variant_kinds}
                    mapping['material'] = lod_material(doc, variant, level, variant_textures)
                out_primitive['extensions'] = extension
            new_primitives.append(out_primitive)
            print(f'APPLIED lod{level} {material["name"]}: {len(corners)} triangles, {len(keys)} vertices')
        mesh['primitives'] = new_primitives
    counts = [triangles(doc, i) for i in [node['mesh']] + lod0['extras']['openyamm_lods']]
    if not all(a > b for a, b in zip(counts, counts[1:])):
        raise ValueError(f'LOD triangle counts must decrease: {counts}')
    packed = compact(doc, binary)
    write_glb(out, doc, bytes(packed))
    print('BAKED GLB', out, 'triangles', counts, f'{len(packed) / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
