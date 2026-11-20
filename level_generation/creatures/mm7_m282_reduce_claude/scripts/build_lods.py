"""Reduced LOD0 GLB -> GLB with LOD1-3 and shadow LODs (tools/build_actor_lods.py, 8 influence slots at LOD1-3 as the
batch I export), with protected points: the bounding extremes of LOD0 (top 5 mm: the highest hair snakes; the outer
5 mm at both sides and both ends: snake curls, hands, the rattle tip) and the Death/Dead floor contacts
(work/floor_points.json from floor_points.py). Ratios REA_LOD_RATIOS (default 0.5,0.27,0.094: LOD2/LOD3 near the
batch I counts 2,782 / 918). Usage: blender -b -P build_lods.py -- <in lod0.glb> <out.glb>"""
import json, os, sys
from pathlib import Path
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.import_scene.gltf(filepath=src)
o = bpy.data.objects['M282']
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest)
xmin = min(p.x for p in rest); xmax = max(p.x for p in rest); ymin = min(p.y for p in rest); ymax = max(p.y for p in rest)
pts = [tuple(p) for p in rest if p.z > top - .005 or p.x < xmin + .005 or p.x > xmax - .005
       or p.y < ymin + .005 or p.y > ymax - .005]
n_ext = len(pts)
pts += [tuple(x) for x in json.loads((P / 'work' / 'floor_points.json').read_text())]
bpy.ops.wm.read_factory_settings(use_empty=True)
R = tuple(float(x) for x in os.environ.get('REA_LOD_RATIOS', '0.5,0.27,0.094').split(','))
generate(Path(src), Path(dst), 'M282', ratios=R, max_influences=8, protected_points=pts)
print('PROTECTED', len(pts), 'extremes', n_ext, 'ratios', R)
