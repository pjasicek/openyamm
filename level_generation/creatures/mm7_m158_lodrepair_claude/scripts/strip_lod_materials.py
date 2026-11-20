#!/usr/bin/env python3
"""Drop the old far-LOD materials (`<material>_LOD<N>`) that no primitive or variant mapping uses any more, and the
textures and images only they used. build_lods.py calls this after it has replaced the far meshes (which drop the
old copies' references), so a rerun on an already-repaired GLB gives apply_bake.py an input without `_LOD<N>`
materials. Referenced materials, LOD0/LOD1 materials, other textures and images (even orphans) stay; indices are
remapped. Image buffer views of dropped images are left for splice_lods.compact() to remove.
Usage (standalone, also compacts): strip_lod_materials.py <in.glb> <out.glb>"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
sys.path.insert(0, str(HERE))
from build_actor_lods import read_glb, write_glb  # noqa: E402

LOD_NAME = re.compile(r'_LOD\d+$')


def texture_refs(value):
    """Every {'index': n} dict inside a material (core maps and extras such as the region mask and burn map)."""
    if isinstance(value, dict):
        if isinstance(value.get('index'), int):
            yield value
        for child in value.values():
            yield from texture_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from texture_refs(child)


def material_refs(doc):
    """(holder, key) for every material index in the meshes: primitive materials and variant mappings."""
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            if 'material' in primitive:
                yield primitive, 'material'
            for mapping in primitive.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                yield mapping, 'material'


def strip_unused_lod_materials(doc):
    """Returns the names of the dropped materials."""
    used = {holder[key] for holder, key in material_refs(doc)}
    drop = {i for i, m in enumerate(doc['materials']) if i not in used and LOD_NAME.search(m.get('name', ''))}
    if not drop:
        return []
    dropped_textures = {r['index'] for i in drop for r in texture_refs(doc['materials'][i])}
    names = [doc['materials'][i]['name'] for i in sorted(drop)]
    material_map = {old: new for new, old in enumerate(i for i in range(len(doc['materials'])) if i not in drop)}
    doc['materials'] = [m for i, m in enumerate(doc['materials']) if i not in drop]
    for holder, key in material_refs(doc):
        holder[key] = material_map[holder[key]]
    # Textures only the dropped materials used; images only those textures used.
    kept_refs = {r['index'] for m in doc['materials'] for r in texture_refs(m)}
    drop_textures = dropped_textures - kept_refs
    texture_map = {old: new for new, old in enumerate(i for i in range(len(doc['textures'])) if i not in drop_textures)}
    dropped_images = {doc['textures'][i]['source'] for i in drop_textures if 'source' in doc['textures'][i]}
    doc['textures'] = [t for i, t in enumerate(doc['textures']) if i not in drop_textures]
    for material in doc['materials']:
        for ref in texture_refs(material):
            ref['index'] = texture_map[ref['index']]
    drop_images = dropped_images - {t['source'] for t in doc['textures'] if 'source' in t}
    image_map = {old: new for new, old in enumerate(i for i in range(len(doc['images'])) if i not in drop_images)}
    doc['images'] = [m for i, m in enumerate(doc['images']) if i not in drop_images]
    for texture in doc['textures']:
        if 'source' in texture:
            texture['source'] = image_map[texture['source']]
    return names


def main():
    from splice_lods import compact
    doc, binary = read_glb(Path(sys.argv[1]))
    names = strip_unused_lod_materials(doc)
    packed = compact(doc, bytearray(binary))
    write_glb(Path(sys.argv[2]), doc, bytes(packed))
    print('STRIPPED', len(names), 'materials:', ', '.join(names))


if __name__ == '__main__':
    main()
