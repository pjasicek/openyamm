"""v3 UVs and the three Meshy retexture uploads (after scripts/mm6_cdr1_reduce_claude/scripts/uv_uploads.py).
In: work/v3/spines.blend (graft + spine row). Small open loops on the head piece (<= 6 edges) are filled first.
Fresh smart-project UVs for the body set (slot 0: cdr1 body, lofted neck, spines; 80 deg) and the head set (slot 1:
the grafted MM7 head; 80 deg); the wings keep the cdr1 wing layout. Runtime layouts: body islands in [0, .92]^2,
head and wings in [0, .86]^2 (so each upload's return is the runtime texture without resampling).
Every upload carries the whole dragon so Meshy paints neighbouring sets at one scale size: the target set at its
runtime place, the other two small in the strip beside it.
Out: work/v3/uv_master.blend, work/v3/{body,head,wings}_upload.glb, work/v3/uv_report.json."""
import json, math, os, bmesh, bpy
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[2]; W3 = P / 'work/v3'
bpy.ops.wm.open_mainfile(filepath=str(W3 / 'spines.blend'))
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = o.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
# fill small holes of the head piece (v2 head had two 5-edge openings behind the eyes and degenerate slits)
bm = bmesh.new(); bm.from_mesh(me); part = bm.verts.layers.int.get('v3part')
small = {e for e in bm.edges if e.is_boundary and all(v[part] == 1 for v in e.verts)}
filled = []
while small:
    e0 = small.pop(); loop = [e0.verts[0], e0.verts[1]]; used = {e0}
    while True:
        nxt = [e for e in loop[-1].link_edges if e in small and e not in used]
        if not nxt: break
        e = nxt[0]; used.add(e); small.discard(e); v = e.other_vert(loop[-1])
        if v is loop[0]: break
        loop.append(v)
    if 3 <= len(loop) <= 6:
        try:
            f = bm.faces.new(loop)
        except ValueError:      # a degenerate slit whose face exists already
            continue
        f.material_index = 1; f.smooth = True; filled.append(f)
bm.normal_update()
for f in filled:   # outward: agree with a neighbouring face across the shared edge
    nb = [g for e in f.edges for g in e.link_faces if g is not f]
    if nb and f.normal.dot(sum((g.normal for g in nb), f.normal * 0)) < 0: f.normal_flip()
res = {'faces': bmesh.ops.triangulate(bm, faces=filled)['faces']}
print('FILLED', len(res['faces']), 'open edges left', sum(1 for e in bm.edges if e.is_boundary))
bm.to_mesh(me); bm.free(); me.update()
uv = me.uv_layers['UVMap']
# keep the source layouts for proxy renders and bakes: cdr1 UVs (cdr1 faces) and the v2 head UVs (UV_v2head)
src = me.uv_layers.new(name='UV_cdr1'); n = len(uv.data); buf = [0.0] * (2 * n)
uv = me.uv_layers['UVMap']; uv.data.foreach_get('uv', buf); me.uv_layers['UV_cdr1'].data.foreach_set('uv', buf)
uv = me.uv_layers['UVMap']; me.uv_layers.active = uv
wing_slot = 2
wing_uv = {li: tuple(uv.data[li].uv) for f in me.polygons if f.material_index == wing_slot for li in f.loop_indices}
layouts = {}
for slot, angle in ((0, 80), (1, 80)):
    tmp = o.copy(); tmp.data = me.copy(); tmp.parent = None; tmp.modifiers.clear(); bpy.context.collection.objects.link(tmp)
    bm = bmesh.new(); bm.from_mesh(tmp.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != slot], context='FACES'); bm.to_mesh(tmp.data); bm.free()
    tmp.data.uv_layers.active = tmp.data.uv_layers['UVMap']
    bpy.ops.object.select_all(action='DESELECT'); tmp.select_set(True); bpy.context.view_layer.objects.active = tmp
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=.004, area_weight=0, correct_aspect=True, scale_to_bounds=True)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=.004, margin_method='FRACTION', shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    tuv = tmp.data.uv_layers['UVMap']; src = [f for f in me.polygons if f.material_index == slot]
    assert len(src) == len(tmp.data.polygons)
    layouts[slot] = {}
    for f, g in zip(src, tmp.data.polygons):
        for li, lj in zip(f.loop_indices, g.loop_indices): layouts[slot][li] = tuple(tuv.data[lj].uv)
    bpy.data.objects.remove(tmp, do_unlink=True)
# wings: cdr1 layout normalised to its own bounds
wu = np.array(list(wing_uv.values())); wlo, whi = wu.min(0), wu.max(0); ws = float((whi - wlo).max())
layouts[2] = {li: ((u - wlo[0]) / ws, (v - wlo[1]) / ws) for li, (u, v) in wing_uv.items()}
SCALE = {0: .92, 1: .86, 2: .86}
for slot, sc in SCALE.items():
    for li, (u, v) in layouts[slot].items(): uv.data[li].uv = (u * sc, v * sc)
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
bpy.ops.wm.save_as_mainfile(filepath=str(W3 / 'uv_master.blend'))
placement = {
    'body': {0: (.92, 0, 0), 1: (.08, .92, 0), 2: (.08, .92, .08)},
    'head': {1: (.86, 0, 0), 0: (.14, .86, 0), 2: (.14, .86, .14)},
    'wings': {2: (.86, 0, 0), 0: (.14, .86, 0), 1: (.14, .86, .14)},
}
report = {'wing_layout_bounds': [wlo.tolist(), whi.tolist()]}
for label, place in placement.items():
    if (P / f'meshy/{label}_retexture_v3/model_urls_glb.glb').exists():
        # the upload was sent; its geometry and UVs live in the Meshy return (scripts/v3/meshy_uvs.py restores
        # them, packing is not bit-reproducible), so it is not rewritten
        continue
    dup = o.copy(); dup.data = me.copy(); dup.parent = None; dup.modifiers.clear(); dup.vertex_groups.clear()
    bpy.context.collection.objects.link(dup)
    for l in [l for l in dup.data.uv_layers if l.name != 'UVMap']: dup.data.uv_layers.remove(l)
    duv = dup.data.uv_layers['UVMap']
    for f in dup.data.polygons:
        s, ox, oy = place[f.material_index]
        for li in f.loop_indices:
            u, v = layouts[f.material_index][li]; duv.data[li].uv = (ox + u * s, oy + v * s)
    dup.data.materials.clear(); m = bpy.data.materials.new('Neutral'); m.use_nodes = True; dup.data.materials.append(m)
    for f in dup.data.polygons: f.material_index = 0
    bpy.ops.object.select_all(action='DESELECT'); dup.select_set(True); bpy.context.view_layer.objects.active = dup
    bpy.ops.export_scene.gltf(filepath=str(W3 / f'{label}_upload.glb'), use_selection=True, export_format='GLB',
                              export_animations=False, export_skins=False, export_attributes=False, export_morph=False)
    area = {0: 0., 1: 0., 2: 0.}; dup.data.calc_loop_triangles(); tris = []
    for t in dup.data.loop_triangles:
        mi = me.polygons[t.polygon_index].material_index; p = [tuple(duv.data[li].uv) for li in t.loops]
        tris.append([mi] + [c for q in p for c in q])
        area[mi] += abs((p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) - (p[2][0] - p[0][0]) * (p[1][1] - p[0][1])) / 2
    np.save(W3 / f'uv_tris_{label}.npy', np.array(tris, np.float32))
    report[label] = {'triangles': len(dup.data.loop_triangles), 'uv_area': {k: round(v, 3) for k, v in area.items()}}
    bpy.data.objects.remove(dup, do_unlink=True)
(W3 / 'uv_report.json').write_text(json.dumps(report, indent=1)); print('UV', json.dumps(report))
