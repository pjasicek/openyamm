"""Smart UV Project on the blob faces (part 0) of work/rig_v1.blend (rest pose), pack, save work/rig_uv.blend, and
export the blob alone (no pod, no armature) as texturing/ooz_neutral_upload.glb for the Meshy retexture. The pod's
UVs are assigned after the retexture (compose_ooz.py samples the blob's top surface)."""
import bpy, bmesh, os, sys, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
mesh, rig = bpy.data.objects['Ooze'], bpy.data.objects['Ooze_Rig']
for b in rig.pose.bones:
    b.matrix_basis.identity()
me = mesh.data
for uv in list(me.uv_layers):
    me.uv_layers.remove(uv)
me.uv_layers.new(name='UVMap')
part = np.zeros(len(me.polygons), int)
me.attributes['part'].data.foreach_get('value', part)
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type='FACE')
bpy.ops.mesh.select_all(action='DESELECT')
bm = bmesh.from_edit_mesh(me)
bm.faces.ensure_lookup_table()
for f in bm.faces:
    f.select_set(bool(part[f.index] == 0))
bm.select_flush_mode()
bmesh.update_edit_mesh(me)
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_uv.blend'))
dup = mesh.copy()
dup.data = mesh.data.copy()
dup.modifiers.clear()
dup.vertex_groups.clear()
dup.parent = None
bpy.context.scene.collection.objects.link(dup)
bm = bmesh.new()
bm.from_mesh(dup.data)
bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if part[f.index] != 0], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(dup.data)
bm.free()
for a in [a.name for a in dup.data.attributes if a.name == 'part']:
    dup.data.attributes.remove(dup.data.attributes[a])
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
out = os.path.join(common.PROJECT, 'texturing', 'ooz_neutral_upload.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                          export_animations=False, export_materials='NONE', export_attributes=False)
print('UV+EXPORT', out, len(dup.data.polygons), 'faces')
