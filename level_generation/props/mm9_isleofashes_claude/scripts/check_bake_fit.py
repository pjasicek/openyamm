"""Checks the placement formula against the old isle's baked BModels: OpenYAMM = Rz(-yaw_LT) * scale *
swap(model_LT + binding_origin) * 2.56 + swap(Pos) * 2.56 (+ the transcoder's floor offset, reported as `extra`)."""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fitlib import HERE, bmodel_vertices, bmodels, rot  # noqa: E402
from glbio import world_positions  # noqa: E402
import props_table  # noqa: E402

raw = {o['index']: o for o in json.loads((HERE / 'work/raw_objects_compact.json').read_text())}
rows = []
for idx, prop in props_table.placements():
    o = raw[idx]
    p = o['props']
    name = f"MM9_static_prop_{idx}_{p['Name']}"
    if name not in bmodels():
        continue
    g = world_positions(HERE / f'work/raw/{prop}/{prop}.glb') + np.array(props_table.binding_origin(prop)) * 2.56
    local = np.stack([g[:, 0], g[:, 2], g[:, 1]], 1)
    s = p.get('Scale', 1.0)
    pos = np.array([p['Pos'][0], p['Pos'][2], p['Pos'][1]]) * 2.56
    inst = (local * s) @ rot(-p['Rotation'][1]).T + pos
    B = bmodel_vertices(name)
    extra = (B.min(0) + B.max(0)) / 2 - (inst.min(0) + inst.max(0)) / 2
    d, _ = cKDTree(B).query(inst + extra)
    rows.append((idx, prop, p['Rotation'], round(float(np.median(d)), 2), round(float(d.max()), 1),
                 extra.round(1).tolist()))
    print(*rows[-1])
