"""work/runtime_lod0.glb -> export/mm8_m596.glb with colour LOD1-3 and shadow LODs (build_actor_lods.generate),
4 influences, ratios about 50 % per level. Protected: sole vertices (bind z below 6 mm), the crown top, both claw-tip
extremes and the outermost claw points, so every LOD keeps its floor contact and bounds.
Usage: blender -b -P build_lods.py -- [r1 r2 r3]"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
R = tuple(float(x) for x in a[:3]) if len(a) >= 3 else (.5, .25, .125)
SRC = P / 'work/runtime_lod0.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))
body = bpy.data.objects['CrystalWalker']
co = [body.matrix_world @ v.co for v in body.data.vertices]
protected = [list(c) for c in co if c.z < .006]
# round 6: LOD1 joined the inner claws to the thigh (a face stretched ~20x when the arms rise in Cast); the claw and
# thigh vertices of that gap are kept so no decimated face bridges hand and leg
protected += [list(c) for c in co if .30 < abs(c.x) < .48 and -.22 < c.y < .12 and .55 < c.z < .90]
for key in (lambda c: c.z, lambda c: c.x, lambda c: -c.x, lambda c: -c.y, lambda c: c.y, lambda c: -c.z if c.z > .3 else -9):
    protected.append(list(max(co, key=key)))
print('PROTECTED', len(protected), 'ratios', R)
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(SRC, P / 'export/mm8_m596.glb', 'CrystalWalker', ratios=R, max_influences=4, protected_points=protected)
