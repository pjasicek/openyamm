"""tools/build_actor_lods.py (default ratios 0.5 / 0.18 / 0.06, 4 influences, as the model was built) with the floor contact
and the crown as protected points (MM8 batch lesson; mm9_banshee_reduce_claude/scripts/build_lods.py): the boot-sole vertices
within SOLE m of the rest floor and the head-set vertices within TOP m of the top. Without them LOD3 of the reduced model
stood 1.1 cm above the floor in Standing and sank 2.5 cm in Dead (installed LOD3: 0.35 / 1.5 cm); the corpse contact
vertices (posed within LIE of the floor at the end of Death, Death2 and in Dead) are protected too.
Usage: blender -b -P build_lods.py -- <lod0.glb> <out.glb>"""
import os, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools')); sys.path.insert(0, str(HERE))
from build_actor_lods import generate  # noqa: E402
import glbpack as G, bglbio  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
SOLE = float(os.environ.get('SOLE', '0.006')); TOP = float(os.environ.get('TOP', '0.004'))
d, b = G.read(src)
node = next(n for n in d['nodes'] if n.get('name') == 'Njam' and 'mesh' in n)
pr = {p['material']: p for p in bglbio.prims(d, bytes(b), node['mesh'])}
limbs = pr['Njam']['POSITION'].astype(np.float64); head = pr['NjHead']['POSITION'].astype(np.float64)
keep = [limbs[limbs[:, 1] < limbs[:, 1].min() + SOLE], head[head[:, 1] > head[:, 1].max() - TOP]]
# the corpse's floor contact: vertices within LIE m of the floor at the end of Death and Death2 and in Dead (rest positions)
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
m = Model(Glb(src)); LIE = float(os.environ.get('LIE', '0.01'))
for clip in ('Death', 'Dead', 'PlayDeath'):
    t = m.clip_times(clip)[-1]
    for k, (posed, _) in enumerate(m.skinned_positions(m.world(m.sample(clip, t)))[:3]):
        rest = bglbio.prims(d, bytes(b), node['mesh'])[k]['POSITION'].astype(np.float64)
        keep.append(rest[posed[:, 1] < LIE])
pts = np.unique(np.round(np.vstack(keep), 6), axis=0)
pts = [(float(x), float(-z), float(y)) for x, y, z in pts]
print('PROTECTED points', len(pts))
generate(Path(src).resolve(), Path(dst).resolve(), 'Njam', ratios=(0.5, 0.18, 0.06), max_influences=4, protected_points=pts)
