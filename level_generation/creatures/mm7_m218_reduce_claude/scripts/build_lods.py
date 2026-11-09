"""LOD0 GLB -> GLB with LOD1-3 and shadow LODs: tools/build_actor_lods.py (8 influence slots as the source build,
../mm7_m218_claude/scripts/build_runtime.sh) with ratios 0.5 / 0.196 / 0.0625 instead of its default 0.5 / 0.18 / 0.06,
so LOD2/LOD3 stay just below the source's 1,692 / 541 body triangles (the reduced LOD0 keeps hands, face and crown
leaves exactly, so a smaller LOD0 times the old ratios would cut the coarse LODs below the source). On the body alone
(the spear stays the separate attachment), with the crown-leaf top and spread (crown_points.py) and the Dead/Death
floor contacts (floor_points.py) protected. Usage: blender -b -P build_lods.py -- <in lod0.glb> <out.glb>"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
points = []
for name in ('crown_points.json', 'floor_points.json'):
    points += json.loads((P / 'work' / name).read_text())
generate(Path(src), Path(dst), 'Elf', ratios=(.5, .196, .0625), protected_points=[tuple(x) for x in points])
print('PROTECTED', len(points))
