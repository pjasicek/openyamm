"""LOD0 GLB -> GLB with LOD1-3 and shadow LODs: tools/build_actor_lods.py with 8 influence slots as the source project
(../mm7_m414_claude) but ratios 0.5 / 0.2 / 0.075 instead of its 0.5 / 0.18 / 0.06: the reduced LOD0 keeps hands, face
and the gold lines exactly, and at 0.068 LOD3 (607 triangles) collapsed the helmet dome and pushed the brim over the
eyes; 0.2 keeps LOD2 below the source's 1,857, 0.075 gives LOD3 669 (source 617). On the body alone (the short sword
stays the separate attachment), with the crest outline and helmet top (spike_points.py) and the Dead/Death floor
contacts (floor_points.py) protected. Usage: blender -b -P build_lods.py -- <in lod0.glb> <out.glb>"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
points = []
for name in ('spike_points.json', 'floor_points.json'):
    points += json.loads((P / 'work' / name).read_text())
generate(Path(src), Path(dst), 'Titan', ratios=(.5, .2, .075), protected_points=[tuple(x) for x in points])
print('PROTECTED', len(points))
