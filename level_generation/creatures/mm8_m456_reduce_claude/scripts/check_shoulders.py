"""A sleeve root must stay beneath the cuirass through every delivered clip and LOD (production check of the 2026-10-16
shoulder repair, copied from ../mm8_m456_claude/scripts/): installed source against the reduced export.
Usage: check_shoulders.py -> work/shoulder_check.json"""
from pathlib import Path
import json, sys, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared/gates'))
from run_gates import Glb, load_meshes, sample_grid

def check(path):
    g = Glb(path)
    chest = g.names['B_Spine2']
    rest_inv = np.linalg.inv(g.rest[chest])
    results = []
    for m in load_meshes(g):
        if '/colour' not in m.label:
            continue
        _, weld = np.unique(np.round(m.rest, 5), axis=0, return_inverse=True)
        weld = weld.ravel(); a, b = weld[m.edges.T]
        graph = coo_matrix((np.ones(len(a)), (a, b)), shape=(int(weld.max() + 1),) * 2)
        components = connected_components(graph, directed=False)[1][weld]
        for side in 'LR':
            arm = m.weight([f'B_{side}_UpperArm*'])
            component = max(set(components), key=lambda c: arm[components == c].sum())
            sleeve = components == component
            root = sleeve & (abs(m.rest[:, 0]) < .075) & (m.rest[:, 2] > 1.18)
            assert root.sum() >= 3, (m.label, side, 'missing continuous sleeve root')
            a, b = m.edges.T
            take = sleeve[a] & sleeve[b]
            edges = m.edges[take]; lengths = m.lengths[take]
            result = {'mesh': m.label, 'side': side, 'root_vertices': int(root.sum()), 'clips': {}}
            for name, clip, start, end in g.clips():
                drift, p99, maximum = 0., 0., 0.
                for pose in g.pose(clip, sample_grid(start, end, 120)):
                    co = m.posed(pose); D = pose[chest] @ rest_inv
                    expected = m.rest[root] @ D[:3, :3].T + D[:3, 3]
                    drift = max(drift, float(np.linalg.norm(co[root] - expected, axis=1).max()) * 1000)
                    ratios = np.linalg.norm(co[edges[:, 0]] - co[edges[:, 1]], axis=1) / lengths
                    p99 = max(p99, float(np.percentile(ratios, 99)))
                    maximum = max(maximum, float(ratios.max()))
                result['clips'][name] = {'root_drift_mm': drift, 'stretch_p99': p99, 'stretch_max': maximum}
            results.append(result)
    return {'sha256': g.sha256, 'results': results}

before = check(P / 'work/mm8_m456_source_pre_reduce.glb')
after = check(P / 'export/mm8_m456.glb')
report = {'before': before, 'after': after, 'root_drift_limits_mm': [4, 6, 10, 20]}
(P / 'work/shoulder_check.json').write_text(json.dumps(report, indent=2) + '\n')
for r in after['results']:
    limit = report['root_drift_limits_mm'][int(r['mesh'][-1])]
    assert max(c['root_drift_mm'] for c in r['clips'].values()) < limit, r
    assert max(c['stretch_max'] for c in r['clips'].values()) < 4.5, r
print('SHOULDER_ATTACHMENT_PASS', [(r['mesh'], r['side'], round(max(c['root_drift_mm'] for c in r['clips'].values()), 3), round(max(c['stretch_p99'] for c in r['clips'].values()), 3)) for r in after['results']])
