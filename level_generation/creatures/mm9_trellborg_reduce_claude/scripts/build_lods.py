"""tools/build_actor_lods.py (the installed ratios 0.5/0.18/0.06, 4 influences) with protected points, from
../mm9_dwarf_reduce_claude/scripts/build_lods.py: the default LOD3 of the reduced LOD0 lost 2.4 cm of the hair spikes' tops (picking
bounds use the coarsest LOD; installed LOD3 was 0.9 cm under LOD0). Protected: every vertex within TOP_H of the rest top and within
4 mm of the rest floor (Blender rest coordinates), and DEATH_PTS (death_floor_pts.py: floor contact of
Death/Death2/Dead). Usage: blender -b -P build_lods.py -- <lod0.glb> <dst.glb> <mesh node>"""
import os, sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import build_actor_lods as L  # noqa: E402
src, dst, node = sys.argv[sys.argv.index('--') + 1:][:3]
TOP_H = float(os.environ.get('TOP_H', '0.03'))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
body = bpy.data.objects[node]
rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE'); rig.animation_data_clear()
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
W = [body.matrix_world @ v.co for v in body.data.vertices]
top = max(w.z for w in W); floor = min(w.z for w in W)
tops = [w for w in W if w.z > top - TOP_H]; soles = [w for w in W if w.z < floor + 0.004]
import numpy as np
from mathutils import Vector
dead = [Vector(x) for x in np.load(os.environ['DEATH_PTS'])] if os.environ.get('DEATH_PTS') else []
pts = {tuple(round(c, 7) for c in w): w.copy() for w in tops + soles + dead}
print('PROTECT top', len(tops), 'soles', len(soles), 'death floor', len(dead), 'unique', len(pts), 'top', round(top, 4))
bpy.ops.wm.read_factory_settings(use_empty=True)
L.generate(Path(src).resolve(), Path(dst).resolve(), node, ratios=(0.5, 0.18, 0.06), max_influences=4,
           protected_points=list(pts.values()))
