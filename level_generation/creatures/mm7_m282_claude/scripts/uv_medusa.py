"""UVs and Meshy uploads for the Medusa (rest pose): work/rig_v3.blend -> work/rig_v4.blend,
texturing/m282_body_upload.glb and texturing/m282_head_upload.glb.
- Face attribute `head` (CLAUDE_CREATURE_TEXTURES.md, head-only retexture): skin faces above the collar (mean z > 1.47:
  face, scalp, upper neck) and the two eye pieces. They get their own UV layout filling 0..1 in the same UVMap layer
  (the export gives them the head material; body faces keep the body layout).
- Body faces (skin, hair snakes, scale-mail, quiver, arrows, hands, rings, collar): Smart UV Project 66 deg, packed.
- Uploads: neutral unrigged GLBs (body faces only / head faces only) for the two retextures, enable_original_uv."""
import bpy, bmesh, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = lambda *p: os.path.join(HERE, *p)
bpy.ops.wm.open_mainfile(filepath=W('work', 'rig_v3.blend'))
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
EYES = {28, 30}
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices])
head = np.zeros(len(me.polygons), np.int32)
for p in me.polygons:
    vs = list(p.vertices)
    if (pv[vs] == 0).all() and co[vs, 2].mean() > 1.47 or pv[vs[0]] in EYES:
        head[p.index] = 1
if 'head' in me.attributes:
    me.attributes.remove(me.attributes['head'])
me.attributes.new('head', 'INT', 'FACE').data.foreach_set('value', head)
print('UV head faces', int(head.sum()), 'of', len(me.polygons))
for uv in list(me.uv_layers):
    me.uv_layers.remove(uv)
me.uv_layers.new(name='UVMap')
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)


def unwrap(sel):
    """unwrap and pack one face set with the other set hidden (pack_islands would otherwise pack both)"""
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal(); bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = bool(sel[f.index])
    bmesh.update_edit_mesh(me)
    bpy.context.scene.tool_settings.use_uv_select_sync = True     # UV operators act on the selected faces only
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.002, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin_method='FRACTION', margin=0.003, rotate=True, shape_method='CONCAVE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = me.uv_layers['UVMap'].data; me.calc_loop_triangles(); area = 0.0
    for t in me.loop_triangles:
        if sel[t.polygon_index]:
            P = np.array([tuple(uv[l].uv) for l in t.loops])
            area += 0.5 * abs((P[1, 0] - P[0, 0]) * (P[2, 1] - P[0, 1]) - (P[2, 0] - P[0, 0]) * (P[1, 1] - P[0, 1]))
    print('UV set coverage', round(area, 3))


unwrap(head == 0)
unwrap(head == 1)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=W('work', 'rig_v4.blend'))
os.makedirs(W('texturing'), exist_ok=True)
for name, keep in (('m282_body_upload.glb', 0), ('m282_head_upload.glb', 1)):
    dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None; dup.vertex_groups.clear()
    bpy.context.scene.collection.objects.link(dup)
    bm = bmesh.new(); bm.from_mesh(dup.data); lay = bm.faces.layers.int.get('head')
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[lay] != keep], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(dup.data); bm.free()
    for at in [a.name for a in dup.data.attributes if a.name in ('piece', 'orig_co', 'head')]:
        dup.data.attributes.remove(dup.data.attributes[at])
    for o in bpy.data.objects:
        o.select_set(o == dup)
    bpy.context.view_layer.objects.active = dup
    bpy.ops.export_scene.gltf(filepath=W('texturing', name), use_selection=True, export_format='GLB', export_yup=True,
                              export_skins=False, export_animations=False, export_materials='NONE', export_attributes=False)
    print('UV upload', name, len(dup.data.vertices), 'verts', len(dup.data.polygons), 'faces')
    bpy.data.objects.remove(dup, do_unlink=True)
