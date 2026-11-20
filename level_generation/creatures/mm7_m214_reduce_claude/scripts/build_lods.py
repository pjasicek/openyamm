"""LOD0 GLB -> GLB with LOD1-3 and shadow LODs: tools/build_actor_lods.py with 8 influence slots as the source project
(../mm7_m214_claude/scripts/build_runtime.sh, default ratios 0.5 / 0.18 / 0.06 on body + bow, 4,008 / 1,427 / 455 body
triangles) but on the body alone (the bow and arrow stay the separate attachments) with ratios 0.5 / 0.2 / 0.065, which
keep every level just below the source's counts. Protected: the head crown and the quiver arrow tips
(top_points.json, the picking height), the bowstring's nock ring and end rings (string_points.json; the source LODs
lost the nock, so the distant string stayed straight during the draw) and the Dead/Death floor contacts
(floor_points.json). Usage: blender -b -P build_lods.py -- <in lod0.glb> <out.glb>"""
import json, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
points = []
for name in ('top_points.json', 'string_points.json', 'floor_points.json'):
    points += json.loads((P / 'work' / name).read_text())
generate(Path(src), Path(dst), 'Elf', ratios=(.5, .205, .072), protected_points=[tuple(x) for x in points])
print('PROTECTED', len(points))
