"""Rock alcove from the multi-image return, in the queen's model units, ready to join the actor.

Native placement, measured on the restored standing frame (mm6_qfi/redo_2x/aligned_2x/qfia0.png, 2x pixels, frame scale
2.0): rock 648 tall x 767 wide game units, base on the actor's ground pivot, centred; queen 393 units from horn tips to
the bottom of the abdomen, raised 104 units onto the niche lip. The queen model is 2.4 units tall, so the actor scale is
393 / 2.4 = 163.75 game units per model unit and the rock is 3.957 tall x 4.684 wide here. Depth keeps the width's
factor (the back stands against the wall, unseen). Seam vertices welded, then decimated to ROCK_TRIANGLES (rigid, lumpy silhouette; the normal
map carries the small relief). Writes work/rock.blend (object 'Rock'), work/rock_report.json and review renders."""
import bpy, sys, json
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
GAME_PER_UNIT = 393.0 / 2.4
ROCK_HEIGHT = 648.0 / GAME_PER_UNIT
ROCK_WIDTH = 767.0 / GAME_PER_UNIT
ROCK_TRIANGLES = 4000
# The sprite draws the rock flat at the actor's position; this rock stands behind her, so it is flattened to
# DEPTH_FACTOR of its width (its back is against the end wall, unseen) and enlarged by APPARENT so it matches the
# sprite's apparent size from the room (in-game comparison at 800 units: 25 % small before).
DEPTH_FACTOR = 0.45
APPARENT = 1.1
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P / 'meshy/rock_multiview_v1/model_urls_glb.glb'))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.name = 'Rock'
ob.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in ob.data.vertices])
lo, hi = co.min(0), co.max(0)
sz = ROCK_HEIGHT / (hi[2] - lo[2])
sxy = ROCK_WIDTH / ((hi[0] - lo[0]) * sz)
depth = DEPTH_FACTOR * ROCK_WIDTH / ((hi[1] - lo[1]) * sz)
# the front (-Y) face stays where it was: flatten toward the front
ob.data.transform(Matrix.Diagonal((APPARENT, APPARENT, APPARENT, 1.0))
                  @ Matrix.Translation(Vector((0.0, -ROCK_WIDTH / 2 * 1.0 + DEPTH_FACTOR * ROCK_WIDTH / 2, 0.0)))
                  @ Matrix.Diagonal((sz * sxy, sz * depth, sz, 1.0))
                  @ Matrix.Translation(-Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))))
ob.data.update()
# Meshy splits vertices along UV seams: weld them first, or the collapse opens cracks along every seam.
import bmesh
bm = bmesh.new(); bm.from_mesh(ob.data)
welded = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
welded -= len(bm.verts)
bm.to_mesh(ob.data); bm.free(); ob.data.update()
before = sum(len(p.vertices) - 2 for p in ob.data.polygons)
mod = ob.modifiers.new('decimate', 'DECIMATE')
mod.ratio = ROCK_TRIANGLES / before
mod.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier=mod.name)
for p in ob.data.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in ob.data.vertices])
tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
report = {'depth_factor': DEPTH_FACTOR, 'apparent': APPARENT, 'welded_vertices': welded, 'triangles_before': before, 'triangles': tris, 'size': (co.max(0) - co.min(0)).round(3).tolist(),
          'game_units_per_model_unit': GAME_PER_UNIT, 'xy_factor_vs_height': sxy}
print('ROCK', json.dumps(report))
(P / 'work' / 'rock_report.json').write_text(json.dumps(report, indent=1))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'rock.blend'))
