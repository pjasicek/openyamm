"""Check that the exported sleeves remain centered on the accepted source arms."""
import json
import sys
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared/gates'))
from run_gates import Glb, Mesh

samples = np.arange(.12, .401, .02)
profiles = {}
assets = {}
for label, path in [('source', P.parent / 'mm6_mfp_codex/export/mm6_mfp.glb'),
                    ('before', P / 'work/arm_fix/before/export/mm8_m464.glb'),
                    ('after', P / 'export/mm8_m464.glb')]:
    glb = Glb(path)
    assets[label] = glb.sha256
    node = next(i for i, n in enumerate(glb.nodes) if n.get('mesh') == 0)
    mesh = Mesh(glb, 0, node, 'Body')
    profiles[label] = {}
    for side in 'LR':
        shoulder, wrist = [glb.rest[glb.names[f'B_{side}_{n}'], :3, 3] for n in ['UpperArm', 'Hand']]
        axis = wrist - shoulder
        axis /= np.linalg.norm(axis)
        y = np.array([0., 1., 0.])
        y -= y.dot(axis) * axis
        y /= np.linalg.norm(y)
        basis = np.array([y, np.cross(axis, y)])
        t = (mesh.rest - shoulder) @ axis
        xy = (mesh.rest - shoulder) @ basis.T
        joints = [i for i, n in enumerate(mesh.bone_names) if n.startswith(f'B_{side}_')
                  and any(k in n for k in ['UpperArm', 'Forearm', 'Hand'])]
        arm = np.sum(mesh.weights * np.isin(mesh.joints, joints), axis=1) > .7
        rows = []
        for sample in samples:
            near = arm & (abs(t - sample) < .045)
            points = xy[near]
            kernel = np.exp(-.5 * ((t[near] - sample) / .018) ** 2)
            assert len(points) >= 5
            matrix = np.c_[2 * points, np.ones(len(points))]
            fit = np.linalg.lstsq(matrix * kernel[:, None] ** .5,
                                 (points * points).sum(1) * kernel ** .5, rcond=None)[0]
            rows.append(fit[:2])
        profiles[label][side] = np.array(rows)
report = {'status': 'PASS', 'assets_sha256': assets, 'samples_from_shoulder_m': samples.tolist(),
          'max_center_error_limit_mm': 5, 'arms': {}}
for side in 'LR':
    arm = {}
    for label in ['before', 'after']:
        error = np.linalg.norm(profiles[label][side] - profiles['source'][side], axis=1) * 1000
        arm[label] = {'mean_mm': float(error.mean()), 'max_mm': float(error.max())}
    assert arm['after']['max_mm'] < 5, (side, arm)
    report['arms'][side] = arm
(P / 'review/arm_fix/export_fit.json').write_text(json.dumps(report, indent=2) + '\n')
print('Sleeve centering PASS:', report['arms'])
