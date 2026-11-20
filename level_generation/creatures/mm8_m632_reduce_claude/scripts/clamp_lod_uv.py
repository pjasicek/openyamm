"""Clamp the small LOD decimation UV overshoot at the padded texture edge, as the creature's own
../mm8_m632_claude/scripts/clamp_lod_uv.py does (LOD primitives only, |overshoot| < 0.002). Usage: clamp_lod_uv.py <glb>"""
import sys
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
import merge_head_material as M  # noqa: E402
path = Path(sys.argv[1]); d, b = M.read_glb(path); fixed = []
for mesh in d['meshes']:
    for p in mesh['primitives']:
        old = p['attributes']['TEXCOORD_0']; uv = M.accessor_array(d, b, old)
        if uv.min() >= 0 and uv.max() <= 1:
            continue
        assert '_LOD' in mesh['name'] and uv.min() > -.002 and uv.max() < 1.002, (mesh['name'], uv.min(), uv.max())
        p['attributes']['TEXCOORD_0'] = M.append_accessor(d, b, np.clip(uv, 0, 1), d['accessors'][old], 34962)
        fixed.append(mesh['name'])
M.write_glb(path, d, b); print('UV EDGE', fixed)
