#!/usr/bin/env python3
"""Give the far-LOD copies of variant materials their own maps in an installed, repaired GLB.

Until 2026-11-07 apply_bake.py pointed every variant's <material>_LOD<N> copy at the default material's far maps.
A variant with maps of its own (an MM9 tier painted separately rather than tinted by ramps, a second face, the MM7
robot and MM8 turtle tiers) then showed the default tier's paint at LOD2/LOD3, and a variant without a region mask got
the default's mask without ramps, which the loader rejects ("colour regions need a region mask and one to four ramps").

Per far-LOD primitive with KHR_materials_variants mappings: a variant whose LOD0 maps differ from the default's gets
maps transferred from its own LOD0 maps onto the LOD primitive's existing UVs (transfer_textures.transfer, the same
size as the default's far base colour); a variant sharing the default's maps keeps them, minus maps its LOD0 material
lacks. Geometry, UVs, skins, clips and every other material stay byte-identical.

--all also re-transfers the default material's far maps (2026-11-07: with the supersampled, UV-correspondence
transfer; the nearest-point maps were grainy on pleats, mail and scales) and drops the images it replaced.
--param <built.glb> passes the repair's built GLB (build_lods.py output, LOD0 UVs on the far triangles) so the
transfer uses its UV correspondence first (transfer_textures.transfer param_uv).
Usage: fix_variant_maps.py <in.glb> <out.glb> [--all] [--param <built.glb>]"""
import io
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
sys.path.insert(0, str(HERE))
from build_actor_lods import read_glb, write_glb  # noqa: E402
from build_lods import source_faces  # noqa: E402
from splice_lods import compact, floats  # noqa: E402
from transfer_textures import image, material_maps, own_map_variants, transfer  # noqa: E402

SLOTS = {'basecolor': ('pbr', 'baseColorTexture'), 'mr': ('pbr', 'metallicRoughnessTexture'),
         'normal': ('material', 'normalTexture'), 'mask': ('extras', 'openyamm_region_mask')}


def add_png(doc, binary, name, picture, sampler):
    data = io.BytesIO()
    picture.save(data, 'PNG')
    data = data.getvalue()
    binary.extend(b'\0' * (-len(binary) % 4))
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)})
    binary.extend(data)
    doc['images'].append({'bufferView': len(doc['bufferViews']) - 1, 'mimeType': 'image/png', 'name': name})
    texture = {'source': len(doc['images']) - 1}
    if sampler is not None:
        texture['sampler'] = sampler
    doc['textures'].append(texture)
    return len(doc['textures']) - 1


def slot(material, kind):
    where, key = SLOTS[kind]
    if where == 'pbr':
        return material.setdefault('pbrMetallicRoughness', {}), key
    if where == 'extras':
        return material.setdefault('extras', {}), key
    return material, key


def set_maps(material, textures):
    """Point the material's map slots at `textures`; drop slots it has no texture for. Returns dropped kinds."""
    dropped = []
    for kind in SLOTS:
        holder, key = slot(material, kind)
        if kind in textures:
            entry = holder.get(key, {})
            entry['index'] = textures[kind]
            holder[key] = entry
        elif key in holder:
            del holder[key]
            dropped.append(kind)
    return dropped


def prune_textures(doc):
    """Drop textures no material references (any {'index': n} inside a material) and images no texture uses."""
    used = set()

    def walk(value):
        if isinstance(value, dict):
            if isinstance(value.get('index'), int):
                used.add(value['index'])
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(doc['materials'])
    keep = sorted(used)
    texture_map = {old: new for new, old in enumerate(keep)}
    doc['textures'] = [doc['textures'][i] for i in keep]
    images = sorted({t['source'] for t in doc['textures']})
    image_map = {old: new for new, old in enumerate(images)}
    doc['images'] = [doc['images'][i] for i in images]
    for texture in doc['textures']:
        texture['source'] = image_map[texture['source']]

    def remap(value):
        if isinstance(value, dict):
            if isinstance(value.get('index'), int):
                value['index'] = texture_map[value['index']]
            for item in value.values():
                remap(item)
        elif isinstance(value, list):
            for item in value:
                remap(item)
    remap(doc['materials'])


def main():
    source, out = Path(sys.argv[1]), Path(sys.argv[2])
    everything = '--all' in sys.argv[3:]
    built = None
    if '--param' in sys.argv[3:]:
        built_doc, built_binary = read_glb(Path(sys.argv[sys.argv.index('--param') + 1]))
        built = (built_doc, built_binary)
    doc, binary = read_glb(source)
    binary = bytearray(binary)
    names = {m['name']: i for i, m in enumerate(doc['materials'])}
    changes = []
    for node in doc['nodes']:
        if 'mesh' not in node or 'skin' not in node:
            continue
        lod0 = doc['meshes'][node['mesh']]
        for level, mesh_index in enumerate((lod0.get('extras') or {}).get('openyamm_lods', []), start=1):
            suffix = f'_LOD{level}'
            mesh = doc['meshes'][mesh_index]
            if len(mesh['primitives']) != len(lod0['primitives']):
                continue
            for index, (lod_primitive, primitive) in enumerate(zip(mesh['primitives'], lod0['primitives'])):
                default = doc['materials'][lod_primitive['material']]
                if default['name'] != doc['materials'][primitive['material']]['name'] + suffix:
                    continue  # this level shares LOD0's materials (LOD1) or was not repaired
                mappings = lod_primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', [])
                own = own_map_variants(doc, primitive)
                corners = source_faces(doc, binary, lod_primitive)
                corner_uv = floats(doc, binary, lod_primitive['attributes']['TEXCOORD_0'])[corners]
                size = image(doc, binary, material_maps(default)['basecolor']).shape[0]
                lod0_default = material_maps(doc['materials'][primitive['material']])
                param_uv = None
                if built is not None:
                    built_doc, built_binary = built
                    built_lod0 = next(built_doc['meshes'][n['mesh']] for n in built_doc['nodes']
                                      if n.get('name') == node.get('name') and 'mesh' in n)
                    built_primitive = built_doc['meshes'][built_lod0['extras']['openyamm_lods'][level - 1]][
                        'primitives'][index]
                    built_faces = source_faces(built_doc, built_binary, built_primitive)
                    if len(built_faces) == len(corners):
                        param_uv = floats(built_doc, built_binary,
                                          built_primitive['attributes']['TEXCOORD_0'])[built_faces]
                    else:
                        changes.append(f'{mesh["name"]} p{index}: built GLB does not match, no UV correspondence')
                if everything:
                    sampler = doc['textures'][next(iter(lod0_default.values()))].get('sampler')
                    maps, _ = transfer(doc, binary, primitive, lod_primitive, corners, corner_uv, size,
                                       param_uv=param_uv)
                    changes.append(f'{default["name"]}: {transfer.param_share:.0%} by UV correspondence')
                    set_maps(default, {kind: add_png(doc, binary, f'{default["name"]}_{kind}', maps[kind], sampler)
                                       for kind in lod0_default})
                    changes.append(f'{default["name"]}: maps')
                far_default = material_maps(default)
                for mapping in mappings:
                    copy = doc['materials'][mapping['material']]
                    if copy is default or not copy['name'].endswith(suffix) or copy['name'][:-len(suffix)] not in names:
                        continue
                    variant = names[copy['name'][:-len(suffix)]]
                    kinds = material_maps(doc['materials'][variant])
                    # Maps the variant shares with the default at LOD0 keep the default's far map.
                    shared = {kind for kind, t in kinds.items() if lod0_default.get(kind) == t}
                    if variant in own and set(kinds) - shared:
                        sampler = doc['textures'][next(iter(kinds.values()))].get('sampler')
                        maps, _ = transfer(doc, binary, primitive, lod_primitive, corners, corner_uv, size, variant,
                                           param_uv)
                        textures = {kind: far_default[kind] if kind in shared
                                    else add_png(doc, binary, f'{copy["name"]}_{kind}', maps[kind], sampler)
                                    for kind in kinds}
                        changes.append(f'{copy["name"]}: own maps ({", ".join(sorted(set(kinds) - shared))})')
                    else:
                        textures = {kind: far_default[kind] for kind in kinds if kind in far_default}
                    before = material_maps(copy)
                    dropped = set_maps(copy, textures)
                    if dropped:
                        changes.append(f'{copy["name"]}: dropped {", ".join(dropped)}')
                    elif before != material_maps(copy) and not (variant in own and set(kinds) - shared):
                        changes.append(f'{copy["name"]}: follows default')
    if not changes:
        print('UNCHANGED', source.name)
        return
    prune_textures(doc)
    packed = compact(doc, binary)
    write_glb(out, doc, bytes(packed))
    print('FIXED', source.name, '; '.join(changes))


if __name__ == '__main__':
    main()
