"""Texture uploads from the gated animation master (work/anim_v3.blend, rest pose, no armature, no rock):
- texturing/qfi_body_upload.glb: the whole queen (head included, so the silhouette matches the HD views) for a Meshy
  retexture with enable_original_uv: false; Meshy's layout is copied back face by face (transfer_uv.py);
- texturing/qfi_head_upload.glb: the grafted head mesh alone (face attribute part = 1) with its own UV layer
  'HeadUV' (Smart UV Project, 66 deg, 0.01 margin) for the head retexture (enable_original_uv: true) from the head
  turnaround - the 1K head set (CLAUDE_CREATURE_TEXTURES.md, Head detail).
Both keep the actor-space placement (facing -Y; glTF export turns it to +Z). Saves work/anim_v3h.blend (HeadUV)."""
import bpy, bmesh
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v3.blend'))
rig = bpy.data.objects['Rig']; queen = bpy.data.objects['Queen']; me = queen.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
part = np.array([p.value for p in me.attributes['part'].data])
# head UV layer: Smart UV Project of the head faces only, filling 0..1
if 'HeadUV' not in me.uv_layers:
    me.uv_layers.new(name='HeadUV')
me.uv_layers.active = me.uv_layers['HeadUV']
for o in bpy.data.objects:
    o.select_set(o == queen)
bpy.context.view_layer.objects.active = queen
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons:
    p.select = bool(part[p.index] == 1)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.uv.smart_project(angle_limit=1.1519, island_margin=0.01, scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
me.uv_layers.active = me.uv_layers[0]
(P / 'texturing').mkdir(exist_ok=True)


def export_copy(path, keep_faces, uv_layer):
    """Static copy of the queen with only keep_faces, only uv_layer (as the active and only UV map)."""
    dup = queen.copy(); dup.data = queen.data.copy(); dup.modifiers.clear(); dup.parent = None
    dup.matrix_world = queen.matrix_world
    bpy.context.scene.collection.objects.link(dup)
    m = dup.data
    for layer in [l.name for l in m.uv_layers if l.name != uv_layer]:
        m.uv_layers.remove(m.uv_layers[layer])
    bm = bmesh.new(); bm.from_mesh(m); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not keep_faces[f.index]], context='FACES')
    bm.to_mesh(m); bm.free()
    dup.vertex_groups.clear()
    m.materials.clear()
    for o in bpy.data.objects:
        o.select_set(o == dup)
    bpy.context.view_layer.objects.active = dup
    bpy.ops.export_scene.gltf(filepath=str(path), use_selection=True, export_format='GLB', export_yup=True,
                              export_animations=False, export_skins=False, export_materials='NONE',
                              export_attributes=False)
    print('UPLOAD', path.name, 'faces', len(m.polygons), 'triangles', sum(len(p.vertices) - 2 for p in m.polygons))
    bpy.data.objects.remove(dup, do_unlink=True)


export_copy(P / 'texturing' / 'qfi_body_upload.glb', np.ones(len(part), bool), me.uv_layers[0].name)
export_copy(P / 'texturing' / 'qfi_head_upload.glb', part == 1, 'HeadUV')
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'anim_v3h.blend'))
