#!/usr/bin/env python3
"""A copy of a GLB whose skinned node draws LOD k (its openyamm_lods[k-1] mesh), so the LOD0-only gates (see_through_gate.py,
lining_poke.py) look at that LOD. Review copies only, never for install. Usage: lod_swap.py <glb> <k> <out glb>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbpack  # noqa: E402
doc, binary = glbpack.read(sys.argv[1]); k = int(sys.argv[2])
node = next(n for n in doc['nodes'] if 'mesh' in n and 'skin' in n)
lods = doc['meshes'][node['mesh']]['extras']['openyamm_lods']
node['mesh'] = lods[k - 1]
glbpack.write(sys.argv[3], doc, binary)
print('LOD_SWAP', k, 'mesh', node['mesh'], doc['meshes'][node['mesh']]['name'])
