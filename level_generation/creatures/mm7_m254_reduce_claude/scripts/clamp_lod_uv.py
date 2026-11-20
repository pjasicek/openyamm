"""Clamp a sub-texel decimation UV overshoot (build_actor_lods.py LODs only, |overshoot| < 2 texels at 1K) to the padded
texture edge, so tools/merge_head_material.py can pack the atlas (after mm8_m632_claude). Args: <glb> (in place)"""
import sys
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'tools'))
import merge_head_material as M
path = Path(sys.argv[1]); d, b = M.read_glb(path); fixed = []
for mesh in d['meshes']:
    for p in mesh['primitives']:
        old = p['attributes']['TEXCOORD_0']; uv = M.accessor_array(d, b, old)
        if uv.min() >= 0 and uv.max() <= 1:
            continue
        assert '_LOD' in mesh['name'] and uv.min() > -0.002 and uv.max() < 1.002, (mesh['name'], uv.min(), uv.max())
        p['attributes']['TEXCOORD_0'] = M.append_accessor(d, b, np.clip(uv, 0, 1), d['accessors'][old], 34962)
        fixed.append((mesh['name'], round(float(uv.min()), 5), round(float(uv.max()), 5)))
M.write_glb(path, d, b); print('UV EDGE clamped', fixed)
