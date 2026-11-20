"""UVs for the final Wyrm geometry and the two Meshy retexture uploads (the original project's route).

1. Body layout for every face (Smart UV Project 66 degrees, head islands at 3x texel density), packed; export the
   unrigged mesh to mm6_drr1_claude/texturing/wyrm_neutral_v2.glb (body retexture input).
2. Head layout: faces of the WyrmHead material re-unwrapped into their own 0..1 (75 degrees); body faces keep the
   body layout. Export the head faces alone to texturing/wyrm_head_neutral_v2.glb (head retexture input).
Saves work/uv_final.blend (both layouts, material 1 = head)."""
import math
import os
import sys
import bmesh
import bpy

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WYRM = os.path.join(os.path.dirname(HERE), 'mm6_drr1_claude')
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'claude_shared'))
from uv_head_density import scale_head_islands  # noqa: E402

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'final_geometry.blend'))
mesh = bpy.data.objects['Wyrm']
rig = bpy.data.objects['Wyrm_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
for uv in list(mesh.data.uv_layers):
    mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers.new(name='UVMap')


def select_only(obj):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj


def export_faces(name, keep_material):
    dup = mesh.copy(); dup.data = mesh.data.copy(); dup.modifiers.clear(); dup.parent = None
    bpy.context.scene.collection.objects.link(dup)
    if keep_material is not None:
        bm = bmesh.new(); bm.from_mesh(dup.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != keep_material], context='FACES')
        bm.to_mesh(dup.data); bm.free()
    dup.data.materials.clear()
    select_only(dup)
    path = os.path.join(WYRM, 'texturing', name)
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_skins=False, export_animations=False, export_materials='NONE')
    print('EXPORTED', path, len(dup.data.polygons), 'faces')
    bpy.data.objects.remove(dup, do_unlink=True)


def unwrap(slot, angle, margin):
    """Smart UV Project + concave packing of one material's faces into their own 0..1; returns loop UVs."""
    select_only(mesh)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for f in mesh.data.polygons:
        f.select = f.material_index == slot
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, area_weight=0.0,
                             scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=margin, rotate=True, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    return [u.uv.copy() for u in mesh.data.uv_layers.active.data]


# Each texture set packs only its own faces (head islands packed into the body layout left that space empty).
head_uv = unwrap(1, 85, 0.004)
body_uv = unwrap(0, 80, 0.003)
uvd = mesh.data.uv_layers.active.data
BODY_SCALE, CORNER = 0.94, 0.06
# Body upload: body islands at 94 %; the head islands ride along in a 6 % corner so Meshy sees the whole Wyrm.
for f in mesh.data.polygons:
    for li in f.loop_indices:
        if f.material_index == 0:
            uvd[li].uv = body_uv[li] * BODY_SCALE
        else:
            uvd[li].uv = head_uv[li] * CORNER + head_uv[li].__class__((BODY_SCALE, BODY_SCALE))
export_faces('wyrm_neutral_v2.glb', None)
select_only(mesh)
# Runtime layout: body faces keep the 94 % body layout (as uploaded), head faces use the head layout.
for f in mesh.data.polygons:
    if f.material_index == 1:
        for li in f.loop_indices:
            uvd[li].uv = head_uv[li]
export_faces('wyrm_head_neutral_v2.glb', 1)
select_only(mesh)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv_final.blend'))
print('UV body faces', sum(1 for f in mesh.data.polygons if f.material_index == 0),
      'head faces', sum(1 for f in mesh.data.polygons if f.material_index == 1))
