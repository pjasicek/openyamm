#!/usr/bin/env python3
"""Flip the inverted LOD2 fruit tetrahedra of a food tree GLB in place (2026-10-16).

add_fruit.py's LOD2 tetrahedron listed its faces clockwise seen from outside, so all four faces pointed inward
(check_winding.py: 16 inverted closed parts on mm6_deco_tree06a). The opaque single-sided Fruit material then showed the
inside faces. This swaps the 2nd and 3rd index of every triangle of the Fruit primitive on the given LOD level, in the
file's own bytes. Every other byte stays identical. add_fruit.py is fixed for future builds.
Usage: fix_fruit_winding.py <in.glb> <out.glb> [--level 2] [--material Fruit]"""
import argparse
from pathlib import Path

import numpy as np

import fix_bark_uv as glb


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src', type=Path); ap.add_argument('out', type=Path)
    ap.add_argument('--level', type=int, default=2); ap.add_argument('--material', default='Fruit')
    args = ap.parse_args()
    raw = bytearray(args.src.read_bytes())
    doc, _ = glb.link.read_glb(args.src)
    binary = memoryview(raw)[28 + int.from_bytes(raw[12:16], 'little'):]
    node = next(n for n in doc['nodes'] if 'mesh' in n)
    chain = [node['mesh']] + doc['meshes'][node['mesh']].get('extras', {}).get('openyamm_lods', [])
    flipped = 0
    for prim in doc['meshes'][chain[args.level]]['primitives']:
        if doc['materials'][prim['material']]['name'] != args.material:
            continue
        tris = glb.read(doc, binary, prim['indices']).reshape(-1, 3)
        glb.write(doc, binary, prim['indices'], tris[:, [0, 2, 1]].reshape(-1, 1))
        flipped += len(tris)
    binary.release()
    args.out.write_bytes(raw)
    print('FLIPPED', flipped, 'fruit triangles on LOD', args.level, '->', args.out)


if __name__ == '__main__':
    main()
