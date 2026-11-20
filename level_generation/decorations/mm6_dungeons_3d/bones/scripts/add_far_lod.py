"""Far game mesh for the baked skull pile, sharing LOD0's atlas: 'far' = voxel remesh (FAR_VOXEL units) of the low mesh,
decimated to FAR_TRIS, its own Smart UV charts packed into the atlas corner [CORNER, 1]^2, and LOD0's charts scaled
uniformly into [0, CORNER]^2 (the rest of the right and top strips stays empty). Both are then baked together
(bake_pile.py bakes the joined 'low' + 'far'), so LOD2/LOD3 get colour, AO and tangent normals made for their own
surface: LOD0's normal map on a decimated LOD0 gave shards of light. Run once after make_pile_low.py.
Usage: blender --background ../work/pile_low.blend --python add_far_lod.py"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

FAR_VOXEL = 5.0
FAR_TRIS = 2000
CORNER = 0.875
low = bpy.data.objects['low']
if 'far' in bpy.data.objects:
    raise SystemExit('far already exists: rerun make_pile_low.py first')
for loop in low.data.uv_layers[0].data:
    loop.uv = (loop.uv[0] * CORNER, loop.uv[1] * CORNER)
far = blib.duplicate(low, 'far')
for o in bpy.data.objects:
    o.select_set(o is far)
bpy.context.view_layer.objects.active = far
mod = far.modifiers.new('R', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = blib.u(FAR_VOXEL)
bpy.ops.object.modifier_apply(modifier=mod.name)
blib.pl.decimate_to(far, FAR_TRIS)
for v in far.data.vertices:
    v.co.z = max(v.co.z, 0.0)
for p in far.data.polygons:
    p.use_smooth = True
blib.smart_uv(far, angle=math.radians(66), margin=0.01)
side = 1 - CORNER
for loop in far.data.uv_layers[0].data:
    loop.uv = (CORNER + loop.uv[0] * side, CORNER + loop.uv[1] * side)
bpy.ops.wm.save_mainfile()
print('FAR', 'tris', blib.pl.triangles(far))
