"""LOD0 GLB -> GLB with LOD1-3 and shadow LODs: tools/build_actor_lods.py with 8 influence slots as the source project
(../mm7_m302_claude/scripts/build_runtime.sh, default ratios 0.5 / 0.18 / 0.06 from a 10,027-triangle LOD0) but ratios
0.5 / 0.2 / 0.066 from the reduced LOD0, which keeps LOD2/LOD3 at (just below) the source's 1,803 / 598 triangles. On the
body alone (the axe stays the separate attachment), with the helmet spike and horn curves (spike_points.py) and the
Dead/Death floor contacts (floor_points.py) protected. Usage: blender -b -P build_lods.py -- <in lod0.glb> <out.glb>"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
points = []
for name in ('spike_points.json', 'floor_points.json'):
    points += json.loads((P / 'work' / name).read_text())
generate(Path(src), Path(dst), 'Dwarf', ratios=(.5, .21, .07), protected_points=[tuple(x) for x in points])
print('PROTECTED', len(points))
