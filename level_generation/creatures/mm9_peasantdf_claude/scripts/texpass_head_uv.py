"""Texture quality pass UVs for the head part of the head + hands set (2026-10-30): the head faces' Smart UV layout
(head_split.py) is replaced by claude_shared/uv_atlas.py charts packed into 0..1, exported alone as the head upload,
and written into the master's HeadUV scaled by HEAD_SCALE toward the origin (the lower-left square of the head set,
as head_split.py did, so compose_head_texpass.py resamples the retexture exactly). Hand faces keep their HeadUV
squares; UVMap, weights and geometry are unchanged.

Args (Blender): <master blend> <out blend> <upload glb> <report json> [key=value uv_atlas options]
Never re-run once its upload went to Meshy (xatlas packs differently per run).
"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..'] * 2), 'claude_shared'))
import uv_atlas

HEAD_SCALE = 0.8
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, REPORT = argv[:4]
options = {k: (float(v) if '.' in v else int(v) if v.isdigit() else v) for k, v in (a.split('=', 1) for a in argv[4:])}
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
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
fi = dm.attributes.new('tp_face', 'INT', 'FACE')
fi.data.foreach_set('value', list(range(n)))
bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not head[f.index]], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(dm); bm.free(); dm.update()
dup.vertex_groups.clear()
report = uv_atlas.unwrap(dup, **options)
src = np.zeros(len(dm.polygons), np.int32)
dm.attributes['tp_face'].data.foreach_get('value', src)
du = dm.uv_layers['UVMap'].data
hu = me.uv_layers['HeadUV'].data
for p in dm.polygons:
    q = me.polygons[int(src[p.index])]
    uv = {dm.loops[li].vertex_index: tuple(du[li].uv) for li in p.loop_indices}
    pos = {tuple(np.round(dm.vertices[v].co, 6)): u for v, u in uv.items()}
    for li in q.loop_indices:
        u = pos[tuple(np.round(me.vertices[me.loops[li].vertex_index].co, 6))]
        hu[li].uv = (u[0] * HEAD_SCALE, u[1] * HEAD_SCALE)
tri = np.array([[tuple(du[li].uv) for li in p.loop_indices] for p in dm.polygons])
e1, e2 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]
area = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) / 2
report.update(head_faces=int(head.sum()), zero_area=int((area < 1e-10).sum()), head_scale=HEAD_SCALE)
print('TEXPASS_HEAD_UV', json.dumps(report))
json.dump(report, open(REPORT, 'w'), indent=1)
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
dm.attributes.remove(dm.attributes['tp_face'])
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
bpy.data.objects.remove(dup)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('TEXPASS_HEAD_UV done; upload', UPLOAD, int(head.sum()))
