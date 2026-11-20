"""LOD0 GLB -> LOD1-3 and shadow LODs with the Sorcerer's own settings (tools/build_actor_lods.py defaults as
../mm9_evilsorcerer_claude/scripts/rebuild.sh: ratios 0.5 / 0.18 / 0.06, 4 influences), with protected points (MM8 batch
LOD locks, mm7_m274_reduce_claude/scripts/build_lods.py): rest vertices within 5 mm of the floor (soles; LOD3 stood 6 mm
up without them) and the crown's top 5 mm; CORPSE=Death,Dead also LOD0 vertices within 1 cm of the floor in those
clips' frames (off: with them LOD3's corpse went 29 cm under the floor).
Usage: blender -b -P build_lods.py -- <lod0.glb> <out.glb>"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
src, dst = (Path(a).resolve() for a in sys.argv[sys.argv.index('--') + 1:][:2])
bpy.ops.import_scene.gltf(filepath=str(src)); sc = bpy.context.scene
o = bpy.data.objects['Sorcerer']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest); low = min(p.z for p in rest)
keep = {i for i, p in enumerate(rest) if p.z > top - .005 or p.z < low + .005}
for name in [n for n in __import__('os').environ.get('CORPSE', '').split(',') if n]:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
        keep |= {v.index for v in me.vertices if (ev.matrix_world @ v.co).z < .01}; ev.to_mesh_clear()
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (soles, crown top, Death/Dead floor contact)')
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(src, dst, 'Sorcerer', ratios=(.5, .18, .06), max_influences=4, protected_points=points)
