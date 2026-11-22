"""Open the mouth for real (the voxel clean fused the lip slit, so opening the Jaw only stretched furry skin into a long
chin): on the UV master work/anim_base.blend (paint layout unchanged: faces and UVs stay, the cut only splits vertices)
  1. cut the lips: in the mouth zone (ahead of the mouth corners, y < -0.975, within 3 cm of the mouth line
     z = 0.967 + 0.221 (y + 0.987)) every edge between a face above and a face below the line is split;
  2. weights in that zone: the upper side wholly Head, the lower side wholly Jaw (a clean lip edge);
  3. a mouth bag inside the head behind the lips: a flattened sphere (9 x 12 x 4 cm), upper half on Head, lower half
     on Jaw with the sides blended, so the open jaws show a dark red gum cavity; its UVs sit in a free corner of the
     atlas (u 0.004-0.074, v 0.910-0.980), painted by compose_saber.py (gum red, tongue, a row of teeth at the front).
Face attribute part 5 = mouth bag. Backup of the input: work/anim_base_premouth.blend (re-run from it).
Also writes texturing/saber_uvref.glb (static, the master's UV islands for gutter_fill.py)."""
import bpy, bmesh, os, math
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base_premouth.blend'))
mesh = bpy.data.objects['Saber']; rig = bpy.data.objects['Saber_Rig']
me = mesh.data


def zm(y):
    return 0.967 + 0.221 * (y + 0.987)


bm = bmesh.new(); bm.from_mesh(me)
pl = bm.faces.layers.int['part']
bm.faces.ensure_lookup_table()
side = {}
for f in bm.faces:
    if f[pl] != 0:
        continue
    c = f.calc_center_median()
    if c.y < -0.975 and abs(c.z - zm(c.y)) < 0.03 and abs(c.x) < 0.11:
        side[f.index] = c.z > zm(c.y)
cut = [e for e in bm.edges if len(e.link_faces) == 2 and all(f.index in side for f in e.link_faces)
       and side[e.link_faces[0].index] != side[e.link_faces[1].index]]
print('MOUTH zone faces', len(side), 'cut edges', len(cut))
bmesh.ops.split_edges(bm, edges=cut)
bm.faces.ensure_lookup_table()
upper_v, lower_v = set(), set()
for f in bm.faces:
    if f.index in side:
        (upper_v if side[f.index] else lower_v).update(v.index for v in f.verts)
both = upper_v & lower_v
print('MOUTH upper verts', len(upper_v), 'lower', len(lower_v), 'shared after split', len(both))
bm.to_mesh(me); bm.free()

groups = {g.name: g for g in mesh.vertex_groups}


def set_weights(i, wd):
    v = me.vertices[i]
    for g in list(v.groups):
        mesh.vertex_groups[g.group].remove([i])
    tot = sum(wd.values()) or 1.0
    for n, w in wd.items():
        if w / tot > 1e-4:
            groups[n].add([i], float(w / tot), 'REPLACE')


def get_w(i):
    return {mesh.vertex_groups[g.group].name: g.weight for g in me.vertices[i].groups if g.weight > 1e-5}


for i in upper_v - both:
    w = get_w(i); hw = w.pop('Jaw', 0.0); w['Head'] = w.get('Head', 0.0) + hw; set_weights(i, w)
for i in lower_v - both:
    w = get_w(i); hw = w.pop('Head', 0.0); w['Jaw'] = w.get('Jaw', 0.0) + hw; set_weights(i, w)

# ---- mouth bag
U0, U1, V0, V1 = 0.004, 0.074, 0.910, 0.980
C = Vector((0.0, -1.012, 0.948)); R = Vector((0.046, 0.062, 0.020))
bb = bmesh.new()
bmesh.ops.create_uvsphere(bb, u_segments=12, v_segments=8, radius=1.0)
for v in bb.verts:
    v.co = Vector((v.co.x * R.x, v.co.y * R.y, v.co.z * R.z)) + C
uvl = bb.loops.layers.uv.new('UVMap')
for f in bb.faces:
    for l in f.loops:
        p = l.vert.co - C
        # front view projection (x, z), the back half folded behind: u across, v up; front half in the left half
        uu = 0.5 + 0.5 * p.x / R.x
        vv = 0.5 + 0.5 * p.z / R.z
        if p.y > 0:                       # back half: mirrored into the right half of the square
            uu = 0.5 + 0.5 * uu
        else:
            uu = 0.5 * uu
        l[uvl].uv = (U0 + (U1 - U0) * uu, V0 + (V1 - V0) * vv)
bmesh.ops.triangulate(bb, faces=bb.faces)
bag_me = bpy.data.meshes.new('Bag'); bb.to_mesh(bag_me); bb.free()
bag_me.uv_layers[0].name = me.uv_layers.active.name
bag = bpy.data.objects.new('Bag', bag_me); bpy.context.scene.collection.objects.link(bag)
pa = bag_me.attributes.new('part', 'INT', 'FACE')
for i in range(len(bag_me.polygons)):
    pa.data[i].value = 5
for n in ('Head', 'Jaw'):
    bag.vertex_groups.new(name=n)
for v in bag_me.vertices:
    k = min(1.0, max(0.0, 0.5 - (v.co.z - C.z) / (2 * R.z) * 1.6))   # 0 at the top, 1 at the bottom
    if k < 1: bag.vertex_groups['Head'].add([v.index], 1 - k, 'REPLACE')
    if k > 0: bag.vertex_groups['Jaw'].add([v.index], k, 'REPLACE')
bag.data.materials.clear()
for m in me.materials:
    bag.data.materials.append(m)
bag.parent = mesh.parent; bag.matrix_parent_inverse = mesh.matrix_parent_inverse.copy()
for mod in mesh.modifiers:
    if mod.type == 'ARMATURE':
        am = bag.modifiers.new('Armature', 'ARMATURE'); am.object = mod.object
for o in bpy.data.objects: o.select_set(o in (mesh, bag))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
print('MOUTH bag tris', len(bag_me.polygons) if 'Bag' in bpy.data.meshes else 'joined', 'total tris', len(mesh.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
# static UV reference for gutter_fill (rest pose, no skin)
rig.data.pose_position = 'REST'
up = mesh.copy(); up.data = mesh.data.copy(); up.name = 'SaberUV'
bpy.context.scene.collection.objects.link(up)
up.modifiers.clear(); up.parent = None; up.matrix_world = mesh.matrix_world.copy(); up.data.materials.clear()
for o in bpy.data.objects: o.select_set(o == up)
bpy.context.view_layer.objects.active = up
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'saber_uvref.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('SAVED anim_base.blend + texturing/saber_uvref.glb')
