"""Texturing uploads from a master whose UVs are already laid (no re-layout; texpass_uv.py / texpass_head_uv.py are never
re-run): body upload = every face with UVMap, head/hand faces split from the body faces along the set border (as
texpass_uv.py exported it); head upload = head faces (not hands) with HeadUV / HEAD_SCALE (as texpass_head_uv.py).
Args (Blender): <master blend> <body upload glb> <head upload glb>"""
import bpy, bmesh, sys
import numpy as np
HEAD_SCALE = 0.8
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; n = len(me.polygons)
hd = np.zeros(n, np.int32); hn = np.zeros(n, np.int32)
me.attributes['head'].data.foreach_get('value', hd); me.attributes['hand'].data.foreach_get('value', hn)


def make_dup():
    dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None
    dup.matrix_world = body.matrix_world
    bpy.context.scene.collection.objects.link(dup)
    for g in list(dup.vertex_groups): dup.vertex_groups.remove(g)
    return dup


def export(dup, path):
    dup.data.uv_layers.active = dup.data.uv_layers['UVMap']
    for nm in [u.name for u in dup.data.uv_layers if u.name != 'UVMap']:
        dup.data.uv_layers.remove(dup.data.uv_layers[nm])
    for o in bpy.data.objects: o.select_set(o == dup)
    bpy.context.view_layer.objects.active = dup
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                              export_animations=False, export_materials='NONE', export_attributes=False)
    bpy.data.objects.remove(dup)


sel = (hd | hn).astype(bool)
dup = make_dup(); bm = bmesh.new(); bm.from_mesh(dup.data); bm.faces.ensure_lookup_table()
border = [e for e in bm.edges if len(e.link_faces) == 2 and sel[e.link_faces[0].index] != sel[e.link_faces[1].index]]
bmesh.ops.split_edges(bm, edges=border); bm.to_mesh(dup.data); bm.free()
export(dup, a[1])
head = (hd == 1) & (hn == 0)
dup = make_dup(); dm = dup.data
hu = dm.uv_layers['HeadUV'].data; mu = dm.uv_layers['UVMap'].data
for p in dm.polygons:
    for li in p.loop_indices:
        u = hu[li].uv; mu[li].uv = (u[0] / HEAD_SCALE, u[1] / HEAD_SCALE)
bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not head[f.index]], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(dm); bm.free()
export(dup, a[2])
print('UPLOADS', n, int(head.sum()))
