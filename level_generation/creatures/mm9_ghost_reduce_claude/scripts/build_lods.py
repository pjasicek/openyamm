"""tools/build_actor_lods.py with per-material ratios (lod_ratios.py), 4 influences as the Ghost's build, and protected
points: the robe hem's lowest loop (lowest point of the standing actor) and the head's crown (height used by picking bounds
and the native-height regressions, which read the coarsest LOD). Copied from mm9_banshee_reduce_claude.
Usage: blender -b -P build_lods.py -- <runtime_lod0.glb> <out.glb> <ratios.json>"""
import json, sys
from collections import Counter
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools')); sys.path.insert(0, str(HERE))
from build_actor_lods import generate  # noqa: E402
import glbpack as G, glbio  # noqa: E402
src, dst, rj = sys.argv[sys.argv.index('--') + 1:][:3]
mr = {k: tuple(v) for k, v in json.load(open(rj)).items()}
d, b = G.read(src)
ps = {x['material']: x for x in glbio.prims(d, bytes(b), 0)}
p = ps['Ghost']
P = p['POSITION'].astype(np.float64); _, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.reshape(-1)
E = Counter(tuple(sorted((tp[a], tp[c]))) for t in p['T'] for a, c in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))
rep = np.zeros(tp.max() + 1, np.int64); rep[tp] = np.arange(len(P))
bnd = np.unique([v for e, c in E.items() if c == 1 for v in e])
hem = P[rep[bnd]]; hem = hem[hem[:, 1] < P[:, 1].min() + 0.06]
H = ps['GhostHead']['POSITION'].astype(np.float64); crown = H[H[:, 1] > H[:, 1].max() - 0.004]
pts = [(float(x), float(-z), float(y)) for x, y, z in np.concatenate([hem, crown])]
print('PROTECTED hem points', len(hem), 'lowest', round(float(hem[:, 1].min()), 4), 'crown points', len(crown))
generate(Path(src).resolve(), Path(dst).resolve(), 'Ghost', ratios=(0.5, 0.18, 0.06), max_influences=4, material_ratios=mr,
         protected_points=pts)
