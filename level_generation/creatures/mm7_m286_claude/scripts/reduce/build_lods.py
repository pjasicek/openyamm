"""LOD0 GLB -> GLB with LOD1-3 and shadow LODs: tools/build_actor_lods.py (8 influence slots at LOD1-3 as the v2c
build, scripts/build_runtime.sh) with ratios 0.5 / 0.22 / 0.072 from the reduced LOD0, which keeps LOD2/LOD3 at about
the v2c counts (1,882 / 615; the default 0.18 / 0.06 of a smaller LOD0 would make the far LODs coarser than before).
On the body alone (the axe stays the separate attachment), with the horn tips and curves (spike_points.py) and the
Dead/Death floor contacts (floor_points.py) protected. Usage: blender -b -P build_lods.py -- <in lod0.glb> <out.glb>"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
points = []
for name in ('spike_points.json', 'floor_points.json'):
    points += json.loads((P / 'work' / name).read_text())
generate(Path(src), Path(dst), 'Minotaur', ratios=(.5, .22, .072), protected_points=[tuple(x) for x in points])
print('PROTECTED', len(points))
