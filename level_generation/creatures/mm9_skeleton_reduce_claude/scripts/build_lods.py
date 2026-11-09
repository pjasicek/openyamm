"""tools/build_actor_lods.py as the skeleton's own build_runtime.sh ran it (default ratios 0.5 / 0.18 / 0.06,
4 influences), with protected points: every vertex within 4 mm of the rest floor (soles of the foot pieces: the floor
contact) and the top 1 cm of the cranium (picking bounds and the native-height checks use the coarsest LOD).
Usage: blender -b -P build_lods.py -- <lod0.glb> <dst.glb> <mesh node>"""
import sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import build_actor_lods as L  # noqa: E402
src, dst, node = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
body = bpy.data.objects[node]
rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE'); rig.animation_data_clear()
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
W = [body.matrix_world @ v.co for v in body.data.vertices]
top = max(w.z for w in W); floor = min(w.z for w in W)
crown = [w for w in W if w.z > top - 0.01]
soles = [w for w in W if w.z < floor + 0.004]
pts = {tuple(round(c, 7) for c in w): w.copy() for w in crown + soles}
print('PROTECT crown', len(crown), 'soles', len(soles), 'unique', len(pts), 'top', round(top, 4), 'floor', round(floor, 4))
bpy.ops.wm.read_factory_settings(use_empty=True)
L.generate(Path(src).resolve(), Path(dst).resolve(), node, ratios=(0.5, 0.18, 0.06), max_influences=4,
           protected_points=list(pts.values()))
