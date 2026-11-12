#!/usr/bin/env python3
"""m620 copy of lod_repair_claude/scripts/unwrap_lods.py (2026-11-12, texpass-final): every textured far primitive
gets the level's full size (512 / 256) instead of the size scaled by its surface share. The m620 head set (face,
hair volume and about 100 hair strands) got 256 / 128 px at its share and packed to 8 % / 5 % atlas use (hundreds of
strand charts at 4 px padding): far head density 39 / 16 against the body's 317 / 143. The head primitive is packed
at padding 1 with brute force.

New UVs for rebuilt LODs (build_lods.py output); transfer_textures.py then fills their textures from LOD0.

The LOD0 atlases are split into islands of a few triangles, so a strongly reduced LOD cannot use them: its triangles
span many islands. Each LOD primitive is unwrapped and packed on its own by xatlas, for the level's texture size, on its
vertices welded by position (the LOD keeps LOD0's vertex splits at every old UV/normal seam, which would make each
triangle its own chart). xatlas keeps the input triangle order, so the UVs are stored per triangle corner in the
primitive's own index order. Blender's Smart UV Project returned NaN UVs on some multi-material bodies (MM6 Hydra).
Texture size per primitive: the level's size scaled by the square root of the primitive's share of the surface, to a
power of two (at least 64), so a five-material body costs about what a one-material body does.
Writes <out dir>/lod<N>.npz with p<primitive>_uv (triangles x 3 x 2, glTF orientation) and p<primitive>_size.
Usage: unwrap_lods.py <built.glb> <node> <out dir> <level:size,...>"""
import sys
from pathlib import Path

import numpy as np
import xatlas

HERE = Path(__file__).resolve().parents[2] / 'lod_repair_claude' / 'scripts'
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
sys.path.insert(0, str(HERE))
from build_actor_lods import read_glb  # noqa: E402
from build_lods import source_faces  # noqa: E402
from splice_lods import floats  # noqa: E402
from transfer_textures import material_maps  # noqa: E402

PADDING = 4  # texels between charts, for filtering and the smaller mips


def area(positions, faces):
    corners = positions[faces]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    return float(np.linalg.norm(normals, axis=1).sum()) / 2


def unwrap(positions, faces, size, padding=PADDING, brute=False):
    """Per triangle corner UVs (0..1) of one primitive."""
    _, point = np.unique(positions.astype(np.float32), axis=0, return_inverse=True)
    point = point.reshape(-1)
    points = np.zeros((point.max() + 1, 3), np.float32)
    points[point] = positions
    atlas = xatlas.Atlas()
    atlas.add_mesh(points, point[faces].astype(np.uint32))
    pack = xatlas.PackOptions()
    pack.resolution = size
    pack.padding = padding
    pack.bruteForce = brute
    pack.bilinear = True
    pack.rotate_charts = True
    atlas.generate(pack_options=pack)
    _, indices, uvs = atlas[0]
    if len(indices) != len(faces):
        raise ValueError(f'xatlas returned {len(indices)} of {len(faces)} triangles')
    corner_uv = uvs[indices.reshape(-1, 3)]
    if not np.isfinite(corner_uv).all():
        raise ValueError('xatlas returned non-finite UVs')
    return corner_uv


def main():
    built, node_name, out_dir = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    plan = {int(k): int(v) for k, v in (item.split(':') for item in sys.argv[4].split(','))}
    out_dir.mkdir(parents=True, exist_ok=True)
    doc, binary = read_glb(built)
    node = next(n for n in doc['nodes'] if n.get('name') == node_name and 'mesh' in n)
    lod0 = doc['meshes'][node['mesh']]
    for level, size in sorted(plan.items()):
        mesh = doc['meshes'][lod0['extras']['openyamm_lods'][level - 1]]
        textured = [(index, primitive) for index, primitive in enumerate(mesh['primitives'])
                    if material_maps(doc['materials'][primitive['material']])]
        areas = {index: area(floats(doc, binary, primitive['attributes']['POSITION']),
                             source_faces(doc, binary, primitive)) for index, primitive in textured}
        arrays = {}
        for index, primitive in textured:
            share = areas[index] / max(sum(areas.values()), 1e-12)
            own = max(64, int(2 ** np.ceil(np.log2(max(size * np.sqrt(share), 1.0)))))
            arrays[f'p{index}_size'] = size
            # the head set (primitive 1): ~100 thin hair-strand charts, whose 4-texel padding took most of the map
            # (17 % of a 512 map in triangles at padding 4; 40 % at padding 1 with brute-force packing). Gutters are
            # re-filled with the nearest island texel afterwards (gutter_fill).
            head = index == 1
            arrays[f'p{index}_uv'] = unwrap(floats(doc, binary, primitive['attributes']['POSITION']),
                                            source_faces(doc, binary, primitive), arrays[f'p{index}_size'],
                                            padding=1 if head else PADDING, brute=head)
        np.savez(out_dir / f'lod{level}.npz', **arrays)
        sizes = [int(arrays[f'p{index}_size']) for index, _ in textured]
        print(f'UNWRAPPED lod{level} primitives {[index for index, _ in textured]} at {sizes} px', flush=True)


if __name__ == '__main__':
    main()
