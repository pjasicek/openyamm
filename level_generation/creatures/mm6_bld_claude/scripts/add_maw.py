"""Add the attack maw: a shallow funnel disc in the mouth opening on its own 'Maw' bone (child of Head), UV-mapped to a
free corner of the texture. All existing UVs shrink to 90% toward the top-left corner (compose_bld.py shrinks the
Meshy textures the same way), leaving the bottom-right square u 0.9-1, v 0-0.1 for the native maw art.
Run once on work/anim_v1.blend (after rig_bld.py/uv_export.py); saves it in place."""
import bpy, os, math
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mesh = bpy.data.objects['Bld']; rig = bpy.data.objects['Bld_Rig']
assert 'Maw' not in rig.data.bones, 'maw already added'
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
UV_SCALE, MAW_UV = 0.9, (0.95, 0.05, 0.048)          # shrink factor; maw disc centre u, v and radius in UV

# Mouth opening from the rest mesh: front-most vertices weighted to the Mouth bone.
co = np.array([tuple(v.co) for v in mesh.data.vertices])
mouth = mesh.vertex_groups['Mouth'].index
in_mouth = np.array([any(g.group == mouth and g.weight > 0.5 for g in v.groups) for v in mesh.data.vertices])
tip = co[in_mouth, 1].min()
front = in_mouth & (co[:, 1] < tip + 0.012)
cx, cz = float(np.median(co[front, 0])), float(np.median(co[front, 2]))
R = 0.052

# Maw bone at the opening, pointing forward.
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
maw_bone = rig.data.edit_bones.new('Maw')
maw_bone.head = Vector((cx, tip + 0.004, cz)); maw_bone.tail = Vector((cx, tip - 0.03, cz))
maw_bone.align_roll(Vector((0, 0, 1)))
maw_bone.parent = rig.data.edit_bones['Head']
bpy.ops.object.mode_set(mode='OBJECT')

# Shrink existing UVs toward the top-left corner.
for loop_uv in mesh.data.uv_layers.active.data:
    u, v = loop_uv.uv
    loop_uv.uv = (u * UV_SCALE, 1.0 - (1.0 - v) * UV_SCALE)

# Funnel disc: rim at the opening, centre pushed into the mouth so the teeth converge inward.
rings, segments = 5, 32
verts, faces, uvs = [(cx, tip + 0.016, cz)], [], []
for r in range(1, rings + 1):
    k = r / rings
    for s in range(segments):
        a = 2 * math.pi * s / segments
        verts.append((cx + R * k * math.cos(a), tip + 0.016 - 0.02 * k ** 0.7, cz + R * k * math.sin(a)))
for s in range(segments):
    faces.append((0, 1 + (s + 1) % segments, 1 + s))
for r in range(1, rings):
    a0, b0 = 1 + (r - 1) * segments, 1 + r * segments
    for s in range(segments):
        s1 = (s + 1) % segments
        faces.append((a0 + s, a0 + s1, b0 + s1, b0 + s))
disc_me = bpy.data.meshes.new('maw'); disc_me.from_pydata(verts, [], faces); disc_me.update()
uv_layer = disc_me.uv_layers.new(name=mesh.data.uv_layers.active.name)
for poly in disc_me.polygons:
    for li in poly.loop_indices:
        x, _, z = disc_me.vertices[disc_me.loops[li].vertex_index].co
        uv_layer.data[li].uv = (MAW_UV[0] + (x - cx) / R * MAW_UV[2], MAW_UV[1] + (z - cz) / R * MAW_UV[2])
disc = bpy.data.objects.new('maw', disc_me); bpy.context.scene.collection.objects.link(disc)
group = disc.vertex_groups.new(name='Maw'); group.add(list(range(len(verts))), 1.0, 'REPLACE')
for p in disc_me.polygons:
    p.use_smooth = True
# Face the disc forward (-Y): flip if the first face points backward.
if disc_me.polygons[0].normal.y > 0:
    for p in disc_me.polygons:
        p.flip()
for o in bpy.data.objects:
    o.select_set(o in (mesh, disc))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
print('MAW added: centre', round(cx, 3), round(tip, 3), round(cz, 3), 'radius', R, 'verts', len(verts))
bpy.ops.wm.save_mainfile()
