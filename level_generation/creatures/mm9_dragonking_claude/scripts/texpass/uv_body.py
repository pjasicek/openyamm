"""Texture quality pass, body set (claude_shared/TEXTURE_QUALITY_PASS.md, 2026-10-30): the body faces' xatlas layout
(uv_v2: 43 % of the atlas when it also held the head, 36 % since the head moved to its own set) is replaced by
claude_shared/uv_atlas.py charts of the body faces alone. Every other face (head, teeth, eyes, mouth cavity) stays in
the upload, so Meshy sees the whole dragon, with its UVMap collapsed to one point (zero area: no atlas spent on it;
those faces read HeadUV at export, as mm9_wingedmutant_claude/scripts/uv_texpass.py). Mesh, weights, HeadUV and
attributes are unchanged, apart from the seven quads of the mouth rebuild, triangulated (export triangulates anyway).

Args (Blender): <in blend: head_v1> <out blend> <upload glb> <report json> <old uv npz> [key=value uv_atlas options]
Never re-run once its upload went to Meshy (xatlas packs differently per run)."""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), *(['..'] * 3), 'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, REPORT, OLD = argv[:5]
options = {k: (float(v) if '.' in v else int(v) if v.isdigit() else v) for k, v in (a.split('=', 1) for a in argv[5:])}
DUMP = (0.25 / 2048, 0.25 / 2048)
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
bm = bmesh.new(); bm.from_mesh(me)
quads = [f for f in bm.faces if len(f.verts) != 3]
bmesh.ops.triangulate(bm, faces=quads)
bm.to_mesh(me); bm.free(); me.update()
n = len(me.polygons)
assert all(len(p.vertices) == 3 for p in me.polygons)
hd = np.zeros(n, np.int32); me.attributes['head'].data.foreach_get('value', hd)
sel = hd == 0

# approved layouts, per triangle corner, for the colour pin and the class transfer (uv_pairs.py)
def corners(layer):
    flat = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers[layer].data.foreach_get('uv', flat)
    return flat.reshape(-1, 3, 2)


assert np.array_equal(np.array([p.loop_start for p in me.polygons]), np.arange(n) * 3)
np.savez(OLD, uvmap=corners('UVMap'), headuv=corners('HeadUV'), head=hd)

dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup)
dm = dup.data
fi = dm.attributes.new('tp_face', 'INT', 'FACE'); fi.data.foreach_set('value', list(range(n)))
ov = dm.attributes.new('tp_vert', 'INT', 'POINT'); ov.data.foreach_set('value', list(range(len(dm.vertices))))
b2 = bmesh.new(); b2.from_mesh(dm); b2.faces.ensure_lookup_table()
bmesh.ops.delete(b2, geom=[f for f in b2.faces if not sel[f.index]], context='FACES')
bmesh.ops.delete(b2, geom=[v for v in b2.verts if not v.link_faces], context='VERTS')
b2.to_mesh(dm); b2.free(); dm.update()
dup.vertex_groups.clear()
report = uv_atlas.unwrap(dup, **options)
src, vert = np.zeros(len(dm.polygons), np.int32), np.zeros(len(dm.vertices), np.int32)
dm.attributes['tp_face'].data.foreach_get('value', src)
dm.attributes['tp_vert'].data.foreach_get('value', vert)
du = dm.uv_layers['UVMap'].data
uv = np.zeros((n, 3, 2), np.float32); uv[:] = DUMP
loops = np.zeros(len(me.loops), np.int32); me.loops.foreach_get('vertex_index', loops)
for p in dm.polygons:
    table = {int(vert[dm.loops[li].vertex_index]): tuple(du[li].uv) for li in p.loop_indices}
    f = int(src[p.index])
    for k in range(3):
        uv[f, k] = table[int(loops[f * 3 + k])]
me.uv_layers['UVMap'].data.foreach_set('uv', uv.ravel())
e1, e2 = uv[sel, 1] - uv[sel, 0], uv[sel, 2] - uv[sel, 0]
area = np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) / 2
report.update(body_faces=int(sel.sum()), other_faces=int((~sel).sum()), quads_triangulated=len(quads),
              zero_area=int((area < 1e-10).sum()))
print('TEXPASS_UV', json.dumps(report))
json.dump(report, open(REPORT, 'w'), indent=1)
bpy.data.objects.remove(dup)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)

# upload: the whole dragon, neutral, UVMap only
up = body.copy(); up.data = me.copy(); up.modifiers.clear(); up.parent = None
up.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(up)
up.data.uv_layers.remove(up.data.uv_layers['HeadUV'])
up.data.materials.clear()
for o in bpy.data.objects:
    o.select_set(o == up)
bpy.context.view_layer.objects.active = up
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('TEXPASS_UV done; upload', UPLOAD, n)
