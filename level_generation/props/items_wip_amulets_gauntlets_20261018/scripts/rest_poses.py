"""Choose a shallow dorsal-up rest for each curved gauntlet without changing its painting frame."""
import json
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

P = Path(__file__).resolve().parents[1]
designs = json.loads((P / 'designs.json').read_text())
records = {}
for name, design in designs.items():
    if design['family'] != 'gauntlets':
        continue
    path = P / 'work/codex_tex' / (name + '.blend')
    if not path.exists():
        continue
    bpy.ops.wm.open_mainfile(filepath=str(path))
    obj = bpy.data.objects[name]
    transform = obj.matrix_world.copy()
    if not np.allclose(np.array(transform), np.eye(4), atol=1e-6):
        obj.data.transform(transform)
        obj.matrix_world = Matrix.Identity(4)
        bpy.ops.wm.save_as_mainfile(filepath=str(path))
    positions = np.array([v.co[:] for v in obj.data.vertices])
    candidates = []
    for angle in range(-135, -44, 5):
        rotation = np.array(Matrix.Rotation(math.radians(angle), 3, 'X'))
        span = np.ptp(positions @ rotation.T, axis=0)
        candidates.append((float(span[2]), abs(angle + 90), angle, span.tolist()))
    height, _, angle, span = min(candidates)
    assert height < max(span[:2]), (name, span)
    design['export_rest_x_degrees'] = angle
    records[name] = {'rest_x_degrees': angle, 'rest_extent': span,
                     'criterion': 'Minimum vertical extent, dorsal face up, five degree sampling'}
    print('REST', name, angle, span, flush=True)
designs['equipment_7item248']['export_rest_x_degrees'] = designs['equipment_7item113']['export_rest_x_degrees']
(P / 'designs.json').write_text(json.dumps(designs, indent=2) + '\n')
(P / 'receipts/rest_poses.json').write_text(json.dumps(records, indent=2) + '\n')
