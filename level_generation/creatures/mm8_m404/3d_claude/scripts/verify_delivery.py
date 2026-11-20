from pathlib import Path
import sys, json
import numpy as np

p = Path('level_generation/creatures/mm8_m404/3d_claude')
sys.path.insert(0, 'level_generation/creatures/claude_shared/gates')
import run_gates as g

body = g.Glb(p / 'export/mm8_m404.glb')
old = g.Glb(p / 'review/approved_motion_20261018/export/mixamo_attack_combined.glb')
mesh = next(m for m in g.load_meshes(body) if m.label.endswith('/colour0'))
prop = g.load_meshes(g.Glb(p / 'export/mm8_m404_sword.glb'))[0]
animations = {a['name']: a for a in body.doc['animations']}
expected = {'Standing': 2, 'Walking': .8, 'Attack': 38/30, 'Attack2': 38/30,
            'Hit': .5, 'Fidget': 70/30, 'Death': 1.4, 'Dead': 4/30}
assert set(animations) == set(expected)
report = {'runtime_sha256': body.sha256, 'clips': {}, 'approved_attack_max_matrix_error': {}}
for name, animation in animations.items():
    duration = max(body.accessor(s['input']).max() for s in animation['samplers'])
    assert abs(duration - expected[name]) < 1e-5, (name, duration)
    times = np.linspace(0, duration, round(duration * 240) + 1)
    poses = body.pose(animation, times)
    minimum_body = min(float(mesh.posed(pose)[:, 2].min()) for pose in poses)
    minimum_sword = min(float(g.transform(pose[body.names['Socket_Sword']] @ np.linalg.inv(g.C),
                                          prop.rest)[:, 2].min()) for pose in poses)
    report['clips'][name] = {'duration_s': float(duration), 'body_min_z_m': minimum_body,
                             'sword_min_z_m': minimum_sword, 'samples': len(times)}
    assert minimum_body >= -.002, (name, 'body floor', minimum_body)
    assert minimum_sword >= -.002, (name, 'sword floor', minimum_sword)
    if name in ('Attack', 'Attack2'):
        original = next(a for a in old.doc['animations'] if a['name'] == name)
        old_poses = old.pose(original, times)
        common = [n for n in old.names if n in body.names and
                  n.startswith(('B_', 'Tail', 'Socket'))]
        error = max(float(np.abs(poses[:, body.names[n]] - old_poses[:, old.names[n]]).max()) for n in common)
        report['approved_attack_max_matrix_error'][name] = error
        assert error < 1e-5, (name, 'approved motion changed', error)
gates = json.loads((p / 'review/delivery_gates/gates.json').read_text())
failures = [r for r in gates['gates'] if r['status'] == 'FAIL']
assert len(failures) == 18 and all(r['clip'] in ('Attack', 'Attack2') for r in failures), failures
report['accepted_motion_deviations'] = len(failures)
(p / 'work/delivery_verification.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
