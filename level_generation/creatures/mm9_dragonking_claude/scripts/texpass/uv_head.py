"""Texture quality pass, head set (2026-10-30): the head faces' Smart UV layout (head_split_dk.py: 610 islands, 13 % of
the surface on fragments, in a 0.8 square that left the right fifth of the set empty) is replaced by
claude_shared/uv_atlas.py charts packed into the whole band under the mouth strip (v 0..HEIGHT_SHARE). Mouth faces keep
their HeadUV in the top strip, so its painted texels stay where they are; body faces keep HeadUV (0, 0), UVMap, weights
and geometry are unchanged. The upload is the head without the mouth (as head_split_dk.py), at these exact UVs: no
rescale between the Meshy return and the set.

Args (Blender): <in blend: uv_body output> <out blend> <upload glb> <report json> [key=value uv_atlas options]
Never re-run once its upload went to Meshy (xatlas packs differently per run)."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..'] * 3), 'claude_shared'))
import uv_atlas

HEIGHT_SHARE = 0.8
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
hd, mo = np.zeros(n, np.int32), np.zeros(n, np.int32)
me.attributes['head'].data.foreach_get('value', hd)
me.attributes['mouth'].data.foreach_get('value', mo)
sel = (hd > 0) & (mo == 0)
dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup)
dm = dup.data
fi = dm.attributes.new('tp_face', 'INT', 'FACE'); fi.data.foreach_set('value', list(range(n)))
ov = dm.attributes.new('tp_vert', 'INT', 'POINT'); ov.data.foreach_set('value', list(range(len(dm.vertices))))
bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not sel[f.index]], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(dm); bm.free(); dm.update()
dup.vertex_groups.clear()
report = uv_atlas.unwrap(dup, height_share=HEIGHT_SHARE, **options)
src, vert = np.zeros(len(dm.polygons), np.int32), np.zeros(len(dm.vertices), np.int32)
dm.attributes['tp_face'].data.foreach_get('value', src)
dm.attributes['tp_vert'].data.foreach_get('value', vert)
du = dm.uv_layers['UVMap'].data
flat = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers['HeadUV'].data.foreach_get('uv', flat)
uv = flat.reshape(-1, 3, 2)
loops = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', loops)
for p in dm.polygons:
    table = {int(vert[dm.loops[li].vertex_index]): tuple(du[li].uv) for li in p.loop_indices}
    f = int(src[p.index])
    for k in range(3):
        uv[f, k] = table[int(loops[f * 3 + k])]
me.uv_layers['HeadUV'].data.foreach_set('uv', uv.ravel())
e1, e2 = uv[sel, 1] - uv[sel, 0], uv[sel, 2] - uv[sel, 0]
area = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) / 2
report.update(head_faces=int(sel.sum()), zero_area=int((area < 1e-10).sum()), height_share=HEIGHT_SHARE,
              v_max=float(uv[sel, :, 1].max()), u_max=float(uv[sel, :, 0].max()))
print('TEXPASS_HEAD_UV', json.dumps(report))
json.dump(report, open(REPORT, 'w'), indent=1)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)

# upload: the head without the mouth, HeadUV as the only UV layer (dup has it from uv_atlas as UVMap)
dm.attributes.remove(dm.attributes['tp_face']); dm.attributes.remove(dm.attributes['tp_vert'])
dm.materials.clear()
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('TEXPASS_HEAD_UV done; upload', UPLOAD, int(sel.sum()))
