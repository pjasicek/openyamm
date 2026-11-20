"""Port check: re-simulate a model's accepted Walking chains with cloak.py and compare the chain joints (bone heads
1-3 of every chain) with the installed bake, per sample (cm: median / p95 / max).

    cloak_check.py <glb> <cloak spec json>  [clip]
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cloak  # noqa: E402
from compose_gait import Body  # noqa: E402

glb, spec = sys.argv[1], json.loads(sys.argv[2])
clip = sys.argv[3] if len(sys.argv) > 3 else 'Walking'
P = Body(glb)
P.extra_authored = set()
T = P.clip_length(clip)
N = int(round(T * 120))
_, worlds = P.clip_world(clip, np.arange(N) / N * T)
sim = cloak.Cloak(P, spec)
pts = sim.simulate(worlds, T)
d = []
for c, bones in enumerate(sim.bones):
    for k in (1, 2, 3):
        d.append(np.linalg.norm(worlds[:, bones[k], :3, 3] - pts[:, c, 2 * k], axis=1))
d = np.concatenate(d) * 100
print(f'{clip}: chain joints vs installed bake, cm: median {np.median(d):.1f} p95 {np.percentile(d, 95):.1f} '
      f'max {d.max():.1f}; radii {[round(r, 3) for r in sim.radii]}')
