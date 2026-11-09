"""LOD0 GLB -> GLB with LOD1-3 and shadow LODs: tools/build_actor_lods.py with 8 influence slots as the source project
(../mm7_m254_claude: default ratios 0.5 / 0.18 / 0.06 on its 10,051-triangle LOD0, 5,024 / 1,808 / 598), here ratios
0.5 / 0.2 / 0.075 on the 8,043-triangle reduced LOD0 so LOD2 and LOD3 keep about the source's counts, with the crown
rim and horn tips (spike_points.py) and the Dead/Death floor contacts (floor_points.py) protected.
Usage: blender -b -P build_lods.py -- <in lod0.glb> <out.glb>"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
points = []
for name in ('spike_points.json', 'floor_points.json'):
    points += json.loads((P / 'work' / name).read_text())
generate(Path(src), Path(dst), 'Golem', ratios=(.5, .2, .075), protected_points=[tuple(x) for x in points])
print('PROTECTED', len(points))
