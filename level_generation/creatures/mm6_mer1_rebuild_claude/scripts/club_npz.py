#!/usr/bin/env python3
"""LOD0 vertices of the approved club GLB (its own frame) -> work/club.npz. Args: <club glb> <out npz>"""
import sys
import numpy as np
from pygltflib import GLTF2
h = GLTF2().load(sys.argv[1]); bb = h.binary_blob()
p = h.meshes[0].primitives[0]; a = h.accessors[p.attributes.POSITION]; bv = h.bufferViews[a.bufferView]
P = np.frombuffer(bb, np.float32, a.count * 3, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(-1, 3).astype(float)
np.savez(sys.argv[2], P=P); print('CLUB', len(P), P.min(0).round(3), P.max(0).round(3))
