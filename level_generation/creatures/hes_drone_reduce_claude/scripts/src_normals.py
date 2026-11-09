#!/usr/bin/env python3
"""Hard edges of the hand-built source (drone): the unwelded source GLB's LOD0 vertex positions and normals of the
mesh node (Blender space, z up) -> work/src_normals.npz. The source splits vertices at every hard edge (build_body.py:
profile corners over 50 degrees, material changes, plate lips), and import_source.py's weld merges those splits, so
reduce_ladder.py (REA_SHARP=1) marks an edge of a candidate sharp where the source had two normals at both ends and
each side's face picks a different one; with REA_SHARP=2 every candidate corner on a source vertex
position takes the normal of the source corner there whose face matches its face best (custom normals). Usage: src_normals.py <glb> <mesh node>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402

doc, binary = read_glb(Path(sys.argv[1]))
node = next(n for n in doc['nodes'] if n.get('name') == sys.argv[2])
P, N, T = [], [], []
for prim in doc['meshes'][node['mesh']]['primitives']:
    a = prim['attributes']
    P.append(np.frombuffer(accessor_bytes(doc, binary, a['POSITION']), np.float32).reshape(-1, 3))
    N.append(np.frombuffer(accessor_bytes(doc, binary, a['NORMAL']), np.float32).reshape(-1, 3))
    dt = {5123: np.uint16, 5125: np.uint32, 5121: np.uint8}[doc['accessors'][prim['indices']]['componentType']]
    T.append(np.frombuffer(accessor_bytes(doc, binary, prim['indices']), dt).astype(np.int64).reshape(-1, 3)
             + sum(len(x) for x in P[:-1]))
P, N = np.concatenate(P), np.concatenate(N)
yup = lambda v: np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1)    # glTF y up -> Blender z up
np.savez(Path(__file__).resolve().parents[1] / 'work' / 'src_normals.npz', co=yup(P), n=yup(N), tris=np.concatenate(T))
print('SRCNORMALS', len(P))
