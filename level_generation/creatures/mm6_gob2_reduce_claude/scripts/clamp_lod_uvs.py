#!/usr/bin/env python3
"""Clamp the LOD and shadow meshes' texture coordinates into [0, 1] (Blender's LOD decimation pushed a few head corners to
1.0022; tools/merge_head_material.py cannot pack coordinates outside the unit square). LOD0 is checked, not changed.
Usage: clamp_lod_uvs.py <glb> (in place)"""
import struct, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402
path = Path(sys.argv[1]); doc, binary = read_glb(path); binary = bytearray(binary)
clamped = 0
for mesh in doc['meshes']:
    lods = mesh.get('extras', {}).get('openyamm_lods')
    if lods is None:
        continue
    for p in mesh['primitives']:
        uv = np.frombuffer(accessor_bytes(doc, binary, p['attributes']['TEXCOORD_0']), np.float32)
        assert uv.min() >= 0 and uv.max() <= 1, 'LOD0 coordinates outside [0, 1]'
    for index in lods + mesh['extras'].get('openyamm_shadow_lods', []):
        for p in doc['meshes'][index]['primitives']:
            acc = doc['accessors'][p['attributes']['TEXCOORD_0']]
            uv = np.frombuffer(accessor_bytes(doc, binary, p['attributes']['TEXCOORD_0']), np.float32).reshape(-1, 2)
            out = np.clip(uv, 0, 1); clamped += int((out != uv).any(1).sum())
            p['attributes']['TEXCOORD_0'] = append_accessor(doc, binary, dict(acc, min=out.min(0).tolist(), max=out.max(0).tolist()),
                                                            out.astype(np.float32).tobytes())
write_glb(path, doc, bytes(binary))
print('CLAMPED', clamped, 'LOD corners')
