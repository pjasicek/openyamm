"""Stage F: one UV atlas for the joined Peasant mesh. Body keeps MakeHuman UVs (face as one island); skirt gets a
cylindrical unwrap with a back seam; other parts use Smart UV Project. Face/hands are enlarged before packing."""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
mesh = bpy.data.objects['Peasant']
PARTS = json.loads(bpy.context.scene['pfem_parts'])
rig = bpy.data.objects['Peasant_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects: o.select_set(o == mesh)
me = mesh.data
if not me.uv_layers:
    me.uv_layers.new(name='UVMap')
while len(me.uv_layers) > 1:
    me.uv_layers.remove(me.uv_layers[-1])
part = np.zeros(len(me.polygons), dtype=np.int32)
me.attributes['part'].data.foreach_get('value', part)
skirt_i = PARTS.index('Skirt'); body_i = PARTS.index('Body')

bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(me)
uv = bm.loops.layers.uv.active
bm.faces.ensure_lookup_table()
# Smart project everything except body and skirt.
for f in bm.faces:
    f.select = bool(part[f.index] not in (skirt_i, body_i))
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, scale_to_bounds=False)
bm = bmesh.from_edit_mesh(me); uv = bm.loops.layers.uv.active; bm.faces.ensure_lookup_table()
# Skirt: cylinder unwrap around its own axis, seam at the back (azimuth 180 deg).
skirt_faces = [f for f in bm.faces if part[f.index] == skirt_i]
cx = np.mean([v.co.x for f in skirt_faces for v in f.verts]); cy = np.mean([v.co.y for f in skirt_faces for v in f.verts])
for f in skirt_faces:
    us = []
    for loop in f.loops:
        a = math.atan2(loop.vert.co.x - cx, -(loop.vert.co.y - cy))  # 0 front, +pi/-pi back
        us.append((a + math.pi) / (2 * math.pi))
    if max(us) - min(us) > 0.5:
        us = [u + 1.0 if u < 0.5 else u for u in us]
    for loop, u in zip(f.loops, us):
        loop[uv].uv = (u * 1.4, (loop.vert.co.z - 0.15) / 0.86 * 0.81)
bmesh.update_edit_mesh(me)
# Uniform texel density per part (3D area / UV area), then enlarge face/hands and shrink the skirt.
bm = bmesh.from_edit_mesh(me); uv = bm.loops.layers.uv.active; bm.faces.ensure_lookup_table()
def uv_area(f):
    pts = [l[uv].uv for l in f.loops]
    return abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y for i in range(len(pts)))) / 2
def scale_group(faces, factor):
    loops = [l for f in faces for l in f.loops]
    if not loops:
        return
    centre = sum((l[uv].uv for l in loops), Vector((0, 0))) / len(loops)
    for l in loops:
        l[uv].uv = centre + (l[uv].uv - centre) * factor
def head_face(f):
    return part[f.index] == body_i and f.calc_center_median().z > 1.36
def hand_face(f):
    c = f.calc_center_median()
    return part[f.index] == body_i and abs(c.x) > 0.28 and c.z < 1.0
EXTRA = {'head': 2.6, 'hand': 1.35, 'skirt': 0.6}
groups = {}
for f in bm.faces:
    key = 'head' if head_face(f) else 'hand' if hand_face(f) else ('skirt' if part[f.index] == skirt_i else 'part%d' % part[f.index])
    groups.setdefault(key, []).append(f)
for key, faces in groups.items():
    a3 = sum(f.calc_area() for f in faces); a2 = sum(uv_area(f) for f in faces)
    if a2 <= 0:
        continue
    scale_group(faces, math.sqrt(a3 / a2) * EXTRA.get(key, 1.0))
bmesh.update_edit_mesh(me)
bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
for f in bm.faces:
    f.select = True
bmesh.update_edit_mesh(me)
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')
print('UV packed', len(me.polygons))
bpy.ops.wm.save_mainfile()
