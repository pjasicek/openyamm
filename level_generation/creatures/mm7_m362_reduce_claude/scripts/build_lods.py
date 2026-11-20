"""LOD0 GLB -> GLB with LOD1-3 and shadow LODs: tools/build_actor_lods.py with 8 influence slots as the source project
(../mm7_m410_claude/scripts/build_runtime.sh), on the body alone (the dagger stays the separate attachment, unchanged),
ratios 0.5 / 0.22 / 0.074 instead of the source's 0.5 / 0.18 / 0.06 so LOD2/LOD3 of the 9,077-triangle LOD0 stay just
below the source's 2,029 / 676 triangles (0.06 would give LOD3 545), with the cap tip (cap_points.py) and the
Dead/Death floor contacts (floor_points.py) protected. Usage: blender -b -P build_lods.py -- <in lod0.glb> <out.glb>"""
import json, os, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
points = []
for name in ('spike_points.json', 'floor_points.json'):
    points += json.loads((P / 'work' / name).read_text())
ratios = tuple(float(x) for x in os.environ.get('REA_LOD_RATIOS', '0.5,0.22,0.074').split(','))
generate(Path(src), Path(dst), 'M362', ratios=ratios, protected_points=[tuple(x) for x in points])
print('PROTECTED', len(points), 'RATIOS', ratios)
