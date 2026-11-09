"""work/r57_lod0.glb -> work/r57_lods.glb with LOD1-3 and shadow LODs at 0.5 / 0.25 / 0.10 and 4 influences.
The installed m524 used the tool defaults 0.5 / 0.18 / 0.06 (10,618 -> 1,907 / 613); on the 6,156-triangle LOD0
those gave a 346-triangle LOD3 with an angular tail and stick arms (review/lods/sheet_006.png), so LOD2/3 keep about
the installed far counts (1,539 / 616). Protected: the floor contacts of every clip (floor_contacts.py; the tail lies on the ground) and the
vertices within 2 cm of each bounding extreme (picking bounds use the coarsest LOD). Then the m524 project's
shrink_shadow_lods.py and carry_variants.py. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import json
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
src = P / 'work/r57_lod0.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src))
o = bpy.data.objects['Body']
co = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
pick = np.zeros(len(co), bool)
for k in range(3):
    pick |= co[:, k] > co[:, k].max() - .02
    pick |= co[:, k] < co[:, k].min() + .02
points = [tuple(p) for p in co[pick]] + [tuple(p) for p in json.load(open(P / 'work/floor_contacts.json'))]
print('PROTECTED', int(pick.sum()), 'extreme vertices +', len(points) - int(pick.sum()), 'floor contacts')
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(src, P / 'work/r57_lods.glb', 'Body', ratios=(.5, .25, .10), max_influences=4, protected_points=points)
