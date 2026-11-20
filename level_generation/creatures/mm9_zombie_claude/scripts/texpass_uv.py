"""Texture quality pass UVs for the body set (claude_shared/TEXTURE_QUALITY_PASS.md, 2026-10-30).

The body faces' Smart UV layout (25-26 % of the 2K atlas) is replaced by claude_shared/uv_atlas.py charts (xatlas,
small charts merged, one density, brute-force packing with a 2 px margin). Head and hand faces keep HeadUV (the head
+ hands set; build_export_v2.py copies it over UVMap at export) but stay in the upload so Meshy sees the whole figure:
they are split from the body along the face-set border and packed `small_factor` times less dense, so they cost
little atlas and never share a chart with body faces. Mesh, weights, HeadUV and attributes are unchanged; only the
master's UVMap changes (every face).

Args (Blender): <master blend> <out blend> <upload glb> <report json> [small_factor=0.35] [key=value uv_atlas options]
Never re-run once its upload went to Meshy (xatlas packs differently per run).
"""
import bpy, bmesh, sys, os, json
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD, REPORT = argv[:4]
opts = dict(a.split('=', 1) for a in argv[4:])
small = float(opts.pop('small_factor', 0.35))
options = {k: (float(v) if '.' in v else int(v) if v.isdigit() else v) for k, v in opts.items()}
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
sel = (hd | hn).astype(bool)

# working copy: head/hand faces cut loose from the body faces, original vertex index kept per point
dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup)
dm = dup.data
ov = dm.attributes.new('tp_orig_v', 'INT', 'POINT')
ov.data.foreach_set('value', list(range(len(dm.vertices))))
bm = bmesh.new(); bm.from_mesh(dm)
bm.faces.ensure_lookup_table()
border = [e for e in bm.edges if len(e.link_faces) == 2 and sel[e.link_faces[0].index] != sel[e.link_faces[1].index]]
bmesh.ops.split_edges(bm, edges=border)
bm.to_mesh(dm); bm.free(); dm.update()
assert len(dm.polygons) == n
for g in list(dup.vertex_groups):
    dup.vertex_groups.remove(g)
vg = dup.vertex_groups.new(name='TP_small')
vg.add(sorted({v for p in dm.polygons if sel[p.index] for v in p.vertices}), 1.0, 'REPLACE')
report = uv_atlas.unwrap(dup, head_groups=('TP_small',), head_factor=small, **options)
report.update(small_factor=small, border_edges_split=len(border), body_faces=int((~sel).sum()),
              small_faces=int(sel.sum()))

# write back by corner vertex (split_edges keeps face order and corner order)
orig = np.zeros(len(dm.vertices), np.int32)
dm.attributes['tp_orig_v'].data.foreach_get('value', orig)
du = dm.uv_layers['UVMap'].data
mu = me.uv_layers['UVMap'].data
bad = 0
for p, q in zip(dm.polygons, me.polygons):
    src = {int(orig[dm.loops[li].vertex_index]): tuple(du[li].uv) for li in p.loop_indices}
    for li in q.loop_indices:
        v = me.loops[li].vertex_index
        if v not in src:
            bad += 1
            continue
        mu[li].uv = src[v]
assert bad == 0, f'{bad} corners without a match'
area = []
for p in dm.polygons:
    uv = np.array([tuple(du[li].uv) for li in p.loop_indices])
    area.append(abs((uv[1, 0] - uv[0, 0]) * (uv[2, 1] - uv[0, 1]) - (uv[2, 0] - uv[0, 0]) * (uv[1, 1] - uv[0, 1])) / 2)
area = np.array(area)
report.update(use_body=round(float(area[~sel].sum()), 4), use_small=round(float(area[sel].sum()), 4),
              zero_area_body=int((area[~sel] < 1e-10).sum()))
print('TEXPASS_UV', json.dumps(report))
json.dump(report, open(REPORT, 'w'), indent=1)

os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
dm.attributes.remove(dm.attributes['tp_orig_v'])
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
bpy.data.objects.remove(dup)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('TEXPASS_UV done; upload', UPLOAD, n)
