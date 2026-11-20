"""work/pick_lod0.glb -> work/pick_lods.glb with LOD1-3 and shadow LODs, the creature's own settings
(as the source chain's tools/build_actor_lods.py: ratios 0.5 / 0.18 / 0.06 (its defaults, as the source export), 8 influences; mm7_m426 node M426), with protected
points: the top 5 mm of the crown (locking the 360 sole points as well left LOD3 too few triangles: its arms
collapsed, width 0.68 of 0.96 m). shrink_shadow_lods.py and carry_variants.py then finish export/mm7_m426.glb. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.import_scene.gltf(filepath=str(P / 'work/pick_lod0.glb')); sc = bpy.context.scene
o = bpy.data.objects['M426']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
rest = [o.matrix_world @ v.co for v in o.data.vertices]; top = max(p.z for p in rest)
keep = {i for i, p in enumerate(rest) if p.z > top - .005}       # the crown (soles locked too froze LOD3: arms collapsed)
# Death/Dead floor contacts are NOT locked here (the MM8 lock): the warlock's DROP_FLAT corpse lays the gown and cape
# flat on the floor (hundreds of contact points froze LOD3 at 1,214 triangles); lod_check.py checks the floor instead
points = [tuple(rest[i]) for i in sorted(keep)]
print('PROTECTED', len(points), 'points (crown)')
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P / 'work/pick_lod0.glb', P / 'work/pick_lods.glb', 'M426', ratios=(.5, .18, .06), max_influences=8,
         protected_points=points)
