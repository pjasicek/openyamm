#!/usr/bin/env python3
"""Far-LOD textures from the repainted LOD0 (texture-quality pass, 2026-10-31).

The installed LOD2/LOD3 meshes and their UVs come from lod_repair_claude (2026-10-22) and stay as installed; only
their textures are filled again from the new LOD0 maps with that project's transfer_textures.transfer (same
per-texel nearest-surface lookup and engine normal frame), at the installed sizes. Re-running repair.py instead would
start from its originals/ and rebuild different far meshes (MeshLab is not deterministic).
Usage: far_lod_textures.py <glb with new LOD0 UVs and maps> <out dir>  -> <out dir>/<image name>.png
"""
import io
import sys
import types
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / 'tools'))
sys.path.insert(0, str(HERE.parents[2] / 'lod_repair_claude/scripts'))
# build_lods.py imports pymeshlab for its collapse; only its source_faces() is used here.
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
from build_actor_lods import read_glb  # noqa: E402
from build_lods import source_faces  # noqa: E402
from splice_lods import floats  # noqa: E402
from transfer_textures import material_maps, transfer  # noqa: E402


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    doc, binary = read_glb(src)
    node = next(n for n in doc['nodes'] if n.get('name') == 'BoneDragon' and 'mesh' in n)
    lod0 = doc['meshes'][node['mesh']]
    primitive = lod0['primitives'][0]
    for level in (2, 3):
        lod_primitive = doc['meshes'][lod0['extras']['openyamm_lods'][level - 1]]['primitives'][0]
        material = doc['materials'][lod_primitive['material']]
        faces = source_faces(doc, binary, lod_primitive)
        corner_uv = floats(doc, binary, lod_primitive['attributes']['TEXCOORD_0'])[faces]
        images = {kind: doc['images'][doc['textures'][index]['source']]
                  for kind, index in material_maps(material).items()}
        sizes = set()
        for kind, img in images.items():
            view = doc['bufferViews'][img['bufferView']]
            start = view.get('byteOffset', 0)
            sizes.add(Image.open(io.BytesIO(binary[start:start + view['byteLength']])).size)
        if len(sizes) != 1:
            raise ValueError(f'LOD{level} maps differ in size: {sizes}')
        width, height = sizes.pop()
        assert width == height
        maps, coverage = transfer(doc, binary, primitive, lod_primitive, faces, corner_uv, width)
        for kind, picture in maps.items():
            name = images[kind]['name']
            picture.save(out / f'{name}.png')
            print(f'LOD{level} {kind}: {name}.png {width}px, {coverage:.0%} covered')


if __name__ == '__main__':
    main()
