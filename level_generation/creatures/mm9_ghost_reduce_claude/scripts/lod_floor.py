#!/usr/bin/env python3
"""Every colour LOD of a creature GLB (copied from mm9_banshee_reduce_claude), without Blender: rest bounds (height, span), the lowest point over every clip
(30 Hz; glTF +Y up, floor y = 0) and the faces stretched over 20 x their rest area at any sampled frame.
Usage: lod_floor.py <glb> <label> -> work/lod_floor_<label>.json"""
import copy, json, sys, tempfile
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import glbpack as G  # noqa: E402
glb, label = sys.argv[1:3]
D, B = G.read(glb)
node = next(n for n in D['nodes'] if 'mesh' in n)
levels = [node['mesh']] + D['meshes'][node['mesh']].get('extras', {}).get('openyamm_lods', [])
report = {}
for level, mi in enumerate(levels):
    d = copy.deepcopy(D); next(n for n in d['nodes'] if 'mesh' in n)['mesh'] = mi
    d['meshes'][mi]['name'] = D['meshes'][node['mesh']]['name']
    with tempfile.NamedTemporaryFile(suffix='.glb', dir=HERE / 'work', delete=True) as tmp:
        G.write(tmp.name, d, B); m = Model(Glb(tmp.name))
    rest = m.skinned_positions(m.world({}))
    P0 = np.concatenate([p for p, _ in rest])
    area = lambda pts, T: np.linalg.norm(np.cross(pts[T[:, 1]] - pts[T[:, 0]], pts[T[:, 2]] - pts[T[:, 0]]), axis=1)
    a0 = [area(p, T) for p, T in rest]
    item = {'tris': int(sum(len(T) for _, T in rest)), 'rest_min': P0.min(0).round(4).tolist(), 'rest_max': P0.max(0).round(4).tolist(), 'clips': {}}
    for clip in m.clips:
        t1 = m.clip_times(clip)[-1]; low = 9.0; stretched = 0
        for t in np.append(np.arange(0, t1, 1 / 30), t1):
            posed = m.skinned_positions(m.world(m.sample(clip, t)))
            low = min(low, min(float(p[:, 1].min()) for p, _ in posed))
            stretched = max(stretched, sum(int(((a1 := area(p, T)) > 1e-10).__and__(a1 > 20 * (a + 1e-12)).sum()) for (p, T), a in zip(posed, a0)))
        item['clips'][clip] = {'min_y': round(low, 4), 'stretched_faces': stretched}
    report[level] = item
    print('LOD', label, level, item['tris'], 'height', round(item['rest_max'][1] - item['rest_min'][1], 4), 'span', round(item['rest_max'][0] - item['rest_min'][0], 4),
          'min_y', {k: v['min_y'] for k, v in item['clips'].items()}, 'stretched', {k: v['stretched_faces'] for k, v in item['clips'].items() if v['stretched_faces']}, flush=True)
(HERE / 'work' / f'lod_floor_{label}.json').write_text(json.dumps(report, indent=1) + '\n')
