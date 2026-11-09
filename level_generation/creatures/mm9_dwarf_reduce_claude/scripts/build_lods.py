"""tools/build_actor_lods.py (same ratios 0.5/0.18/0.06, 4 influences) with protected points, as the dwarf's own chain
but keeping what the coarse LODs dropped on the reduced LOD0: the helmet spike (picking bounds and the native-height
regressions use the coarsest LOD; the default LOD3 came out 1.228 m against LOD0 1.322 m) and the soles' floor contact
(LOD3 rest soles 1.7 cm up). Protected: every vertex within SPIKE_R of the spike axis and above top - SPIKE_H, every horn
tip vertex (top 1.5 cm of each horn), every vertex within 4 mm of the rest floor (Blender rest coordinates), and the skirt's side hand-over (vertices
weighted over SIDE_W to both the front and the back skirt leg bones).
Usage: blender -b -P build_lods.py -- <lod0.glb> <dst.glb> <mesh node>"""
import os, sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import build_actor_lods as L  # noqa: E402
src, dst, node = sys.argv[sys.argv.index('--') + 1:][:3]
SPIKE_H, SPIKE_R = float(os.environ.get('SPIKE_H', '0.08')), 0.03
SIDE_W = float(os.environ.get('SIDE_W', '0.1'))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
body = bpy.data.objects[node]
rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE'); rig.animation_data_clear()
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
W = [body.matrix_world @ v.co for v in body.data.vertices]
top = max(w.z for w in W); floor = min(w.z for w in W)
spike = [w for w in W if w.z > top - SPIKE_H and w.x ** 2 + (w.y + 0.016) ** 2 < SPIKE_R ** 2]
horn_top = {s: max(w.z for w in W if s * w.x > 0.15) for s in (1, -1)}
horns = [w for w in W if abs(w.x) > 0.15 and w.z > horn_top[1 if w.x > 0 else -1] - 0.015]
soles = [w for w in W if w.z < floor + 0.004]
# the skirt's sides, where the front leg bones (forward swing only) hand over to the back ones: a coarse LOD face across
# the hand-over stretched 20-60x in Running and Death (LOD2/LOD3 of the first build); vertices carrying both keep the grading
gn = {g.index: g.name for g in body.vertex_groups}
def share(v, key): return sum(g.weight for g in v.groups if gn[g.group].startswith(key))
sides = [W[v.index] for v in body.data.vertices if share(v, 'SkirtLegF') > SIDE_W and share(v, 'SkirtLegB') > SIDE_W]
pts = {tuple(round(c, 7) for c in w): w.copy() for w in spike + horns + soles + sides}
print('PROTECT spike', len(spike), 'horn tips', len(horns), 'soles', len(soles), 'skirt sides', len(sides), 'unique', len(pts), 'top', round(top, 4))
bpy.ops.wm.read_factory_settings(use_empty=True)
L.generate(Path(src).resolve(), Path(dst).resolve(), node, ratios=(0.5, 0.18, 0.06), max_influences=4,
           protected_points=list(pts.values()))
