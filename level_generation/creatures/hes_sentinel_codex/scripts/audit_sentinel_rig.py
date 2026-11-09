"""Verify the actual exported neutral Sentinel rig, before paying for its shared texture set."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

P = Path(__file__).resolve().parents[1]
R = P.parents[2]
sys.path.insert(0, str(R / 'level_generation/creatures/claude_shared/floor'))
from glb_pose import Glb, Model

path = P / 'review/sentinel_rig_preview.glb'
g = Glb(path); m = Model(g); d = g.json
expected = {'Standing': 6.0, 'Attack': 0.5, 'Hit': 0.4, 'Death': 1.2, 'Dead': 1.0}
assert set(m.clips) == set(expected)
names = {n['name']: i for i, n in enumerate(d['nodes']) if 'name' in n}
assert all(n in names for n in ['B_Root', 'B_Head', 'B_Barrel', 'B_Recoil',
                              'Socket_Muzzle', 'Socket_Muzzle_Upper', 'Socket_Muzzle_Lower'])
assert len(d['skins']) == 1
assert sum(len(p['triangles']) for p in m.primitives) == 9747
for p in m.primitives:
    assert p['skinned'] and np.isfinite(p['positions']).all()
    assert np.allclose(p['weights'].sum(1), 1)
    assert ((p['weights'] > 0).sum(1) <= 2).all()
rest = m.skinned_positions(m.world(m.sample('Standing', 0)))
root_slot = m.joints.index(names['B_Root'])
fixed = [((p['joints'] == root_slot) & (p['weights'] > 0.9999)).any(1) for p in m.primitives]
report = {'file': str(path.relative_to(P)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
          'triangles': 9747, 'clips': {}, 'status': 'neutral_rig_verified_texture_pending'}
for clip, wanted in expected.items():
    duration = max(m.clip_times(clip)); assert abs(duration - wanted) < 1e-5
    times = np.linspace(0, duration, round(duration * 60) + 1)
    low, base_drift, movement = [], [], []
    first_world = m.world(m.sample(clip, 0))
    for t in times:
        matrices = m.world(m.sample(clip, float(t)))
        movement.append(float(np.max(np.abs(matrices - first_world))))
        posed = m.skinned_positions(matrices)
        low.append(min(float(points[:, 1].min()) for points, _ in posed))
        for (points, _), (original, _), mask in zip(posed, rest, fixed):
            assert np.isfinite(points).all()
            base_drift.append(float(np.max(np.abs(points[mask] - original[mask]))))
        assert np.allclose(np.linalg.det(matrices[:, :3, :3]), 1, atol=1e-5)
    assert min(low) >= -1e-5 and max(low) <= 1e-5, (clip, min(low), max(low))
    assert max(base_drift) < 1e-5
    assert (max(movement) > 0.025) if clip != 'Dead' else (max(movement) < 1e-6), (clip, max(movement))
    report['clips'][clip] = {'duration': duration, 'samples_at_60hz': len(times),
                             'floor_min': min(low), 'floor_max': max(low), 'base_drift': max(base_drift), 'motion_range': max(movement)}
for first, last, end_time in [('Standing', 'Standing', 6), ('Attack', 'Attack', 0.5),
                               ('Hit', 'Hit', 0.4), ('Dead', 'Dead', 1), ('Dead', 'Death', 1.2)]:
    a = m.skinned_positions(m.world(m.sample(first, 0)))
    b = m.skinned_positions(m.world(m.sample(last, end_time)))
    assert all(np.allclose(x[0], y[0], atol=1e-6) for x, y in zip(a, b)), (first, last)
report['loops_and_death_dead_match'] = True
for file in [path, P / 'work/sentinel_texture_upload.glb']:
    subprocess.run([sys.executable, str(R / 'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py'),
                    str(file)], check=True)
subprocess.run([sys.executable, str(R / 'level_generation/creatures/hes_turrets_claude/scripts/check_key_times.py'),
                str(path)], check=True)
(P / 'review/sentinel_geometry/export_gates.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
