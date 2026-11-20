"""Head-only upload of the CURRENT master for a fresh head retexture (orchestrator review r3, 2026-11-02: repaint tier A's
head instead of patching): the head faces (attribute head, not hand; the loose lip piece already gone, the mouth caps in) with
their frozen layout - the master's HeadUV / HEAD_SCALE, exactly what texpass_head_uv.py uploaded (no re-unwrap: the head set
keeps its layout, so compose_headhand.py resamples the new paint the same way). One UV layer, no materials, rest pose.
Args (Blender): <master blend> <upload glb> [head_scale 0.8]"""
import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, UPLOAD = a[0], a[1]
HS = float(a[2]) if len(a) > 2 else 0.8
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig is not None and rig.animation_data:
    rig.animation_data.action = None
if rig is not None:
    for b in rig.pose.bones:
        b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
n = len(me.polygons)
hd = np.zeros(n, np.int32); hn = np.zeros(n, np.int32)
me.attributes['head'].data.foreach_get('value', hd)
me.attributes['hand'].data.foreach_get('value', hn)
head = (hd == 1) & (hn == 0)
dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup)
dm = dup.data
hu = dm.uv_layers['HeadUV'].data
uv = np.zeros(len(dm.loops) * 2); hu.foreach_get('uv', uv)
uv /= HS
for name in [l.name for l in dm.uv_layers]:
    if name != 'HeadUV':
        dm.uv_layers.remove(dm.uv_layers[name])
dm.uv_layers['HeadUV'].data.foreach_set('uv', uv)
dm.uv_layers['HeadUV'].name = 'UVMap'
bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not head[f.index]], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(dm); bm.free(); dm.update()
dup.vertex_groups.clear()
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True, export_skins=False,
                          export_animations=False, export_materials='NONE', export_attributes=False)
print('HEADUPLOAD2', UPLOAD, int(head.sum()), 'faces; uv range', uv.reshape(-1, 2)[np.repeat(head, 1)[[p.index for p in me.polygons for _ in p.loop_indices]]].min(0).round(3) if False else '')
