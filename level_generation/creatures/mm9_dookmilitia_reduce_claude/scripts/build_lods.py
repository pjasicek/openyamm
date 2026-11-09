"""LOD0 GLB -> GLB with LOD1-3 and shadow LODs: tools/build_actor_lods.py with the Half-Orc's own settings (4 influences,
default ratios 0.5 / 0.18 / 0.06, ../mm9_dookmilitia_claude/scripts/rebuild.sh) plus protected points: the sole contacts and
the Death/Dead corpse contacts (floor_points.py, work/floor_points.json, Blender Z-up) and the top of the helmet (TOP m).
Snap fix (mm9_imp_reduce_claude/scripts/build_lods.py, the LOD-protection trap of REDUCTION_BRIEF_20261104): Blender's glTF
import moves vertices by ~1e-5 m and build_actor_lods.py matches protected points to 1e-5 m, so each point becomes the world
position of the imported vertex nearest to it (within 1e-4 m); unmatched points are reported.
Usage: blender -b -P build_lods.py -- <in lod0.glb> <out.glb>"""
import json, os, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
import bpy  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
points = json.loads((P / 'work' / 'floor_points.json').read_text())
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
o = bpy.data.objects['DookMilitia']; Wv = [o.matrix_world @ v.co for v in o.data.vertices]
TOP = float(os.environ.get('TOP', '0.004')); ztop = max(w.z for w in Wv)
points += [tuple(w) for w in Wv if w.z > ztop - TOP]
kd = KDTree(len(Wv)); [kd.insert(w, i) for i, w in enumerate(Wv)]; kd.balance()
mapped = []; worst = 0.0
for p in points:
    co, i, dist = kd.find(p)
    if dist < 1e-4:
        mapped.append(tuple(co)); worst = max(worst, dist)
pts = list({tuple(round(c, 7) for c in p): p for p in mapped}.values())
print('PROTECTED mapped', len(mapped), 'of', len(points), 'worst offset', worst, 'unique', len(pts))
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(Path(src).resolve(), Path(dst).resolve(), 'DookMilitia', max_influences=4, protected_points=pts)
print('PROTECTED', len(pts))
