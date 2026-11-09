"""tools/build_actor_lods.py (its default ratios and influences, as the creature's build_runtime.sh) with protected
points: every LOD0 vertex that comes within FLOOR_M of the floor (world z) at any frame of Death, Death2 or Dead (MM8
batch lesson, Phoenix). The first s82 build let LOD3 sink 8.1 cm under the floor in Death2 (installed LOD3: 0.2 cm).
Usage: blender -b -P build_lods.py -- <lod0.glb> <dst.glb> <mesh node>"""
import os, sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import build_actor_lods as L  # noqa: E402
src, dst, node = sys.argv[sys.argv.index('--') + 1:][:3]
FLOOR_M = float(os.environ.get('FLOOR_M', '0.01'))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
sc = bpy.context.scene
body = bpy.data.objects[node]
rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE')
rest = [body.matrix_world @ v.co for v in body.data.vertices]
low = set()
for name in ('Death', 'Death2', 'Dead'):
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        low |= {i for i, v in enumerate(me.vertices) if (body.matrix_world @ v.co).z < FLOOR_M}
        ev.to_mesh_clear()
pts = {tuple(round(c, 7) for c in rest[i]): rest[i].copy() for i in low}
print('PROTECT floor-contact vertices', len(low), 'unique', len(pts))
bpy.ops.wm.read_factory_settings(use_empty=True)
# WING_LOD3=<ratio>: the wing slot's LOD3 ratio (default ratios 0.5/0.18/0.06)
mr = {'Wmut_Wing_A': (0.5, 0.18, float(os.environ['WING_LOD3']))} if os.environ.get('WING_LOD3') else None
L.generate(Path(src).resolve(), Path(dst).resolve(), node, protected_points=list(pts.values()), material_ratios=mr)
