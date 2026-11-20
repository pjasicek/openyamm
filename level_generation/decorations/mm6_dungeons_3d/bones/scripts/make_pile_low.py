"""Low-poly game mesh of the full-detail Meshy skull pile (work/pile_high.blend, import_high.py): loose crumbs dropped,
collapse decimation to 400k, voxel remesh, light smoothing, collapse decimation to LOW_TRIS, the underside (faces below 0.5 units facing down)
removed, smooth shading, Smart UV Project + pack for the 2k bake. Saves work/pile_low.blend with objects 'high'
(unchanged, for the bake) and 'low'. Usage: blender --background ../work/pile_high.blend --python make_pile_low.py --
[low triangles] [voxel units] [smooth iterations] [UV angle]"""
import math
import os
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
LOW_TRIS = int(args[0]) if args else 11000
VOXEL = float(args[1]) if len(args) > 1 else 1.5
SMOOTH = int(args[2]) if len(args) > 2 else 2
ANGLE = float(args[3]) if len(args) > 3 else 66.0
high = bpy.data.objects['high']
low = blib.duplicate(high, 'low')
for o in bpy.data.objects:
    o.select_set(o is low)
bpy.context.view_layer.objects.active = low
pieces, dropped = blib.drop_small_pieces(low, keep_fraction=0.0005)
blib.pl.decimate_to(low, 400000)
# A voxel remesh (VOXEL units) evens the triangles and closes the finest gaps (they live on in the normal and AO
# bakes), so the final decimation gives a smooth surface whose UV charts are large.
mod = low.modifiers.new('R', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = blib.u(VOXEL)
bpy.ops.object.modifier_apply(modifier=mod.name)
smooth = low.modifiers.new('S', 'SMOOTH'); smooth.factor = 0.5; smooth.iterations = SMOOTH
bpy.ops.object.modifier_apply(modifier=smooth.name)
print('REMESHED', blib.pl.triangles(low))
blib.pl.decimate_to(low, LOW_TRIS)
bm = bmesh.new(); bm.from_mesh(low.data)
floor = blib.u(0.5)
under = [f for f in bm.faces if f.normal.z < -0.7 and max(v.co.z for v in f.verts) < floor]
bmesh.ops.delete(bm, geom=under, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(low.data); bm.free()
for p in low.data.polygons:
    p.use_smooth = True
blib.smart_uv(low, angle=math.radians(ANGLE), margin=0.002)
low.data.materials.clear()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blib.WORK, 'pile_low.blend'))
print('LOW', 'pieces', pieces, 'dropped', dropped, 'underside', len(under), 'tris', blib.pl.triangles(low),
      'uv islands done')
