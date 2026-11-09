"""Fresh body-set UVs for the chest-repaired pick (work/ladder_chest.blend, Cand_62): body faces (merged-atlas
u < 0.5) are unwrapped again, density averaged, the clasp at 2x linear density; the cord, necklace links, pendant plate and
gem (face attribute chest_part, chest_repair.py) each map onto one flat colour square (work/flat_squares.json); convex pack, overlapping faces re-projected until none overlap. Writes
- work/ladder_body.blend: Cand_62 with the body faces' atlas UVs in the body half (head faces unchanged),
- texturing/body_upload.glb: body faces only, rest pose, UVs 0..1 (Meshy retexture, enable_original_uv),
- work/body_uv.npz: per body triangle corner the 0..1 UV and rest world position; per triangle the detail flag and
  the installed region class of its source face (0 none, 1 cloak, 2 tunic; new parts 0) and chest_part.
Usage: blender -b -P body_uv.py"""
import math, os, bmesh, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, G, H = 2080, 32, 1024
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_chest.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
cand = bpy.data.objects['Cand_62']; me = cand.data; mw = cand.matrix_world
mask = bpy.data.images.load(os.path.join(HERE, 'work', 'region_mask.png'))
mW, mH = mask.size; px = np.array(mask.pixels[:], np.float32).reshape(mH, mW, 4)
uvl = me.uv_layers.active
body, cls = set(), {}
for p in me.polygons:
    u = np.mean([uvl.data[li].uv[0] for li in p.loop_indices]); v = np.mean([uvl.data[li].uv[1] for li in p.loop_indices])
    if u < .5:
        body.add(p.index)
        s = px[min(int(v * mH), mH - 1), min(int(u * mW), mW - 1)]
        cls[p.index] = 1 if s[0] > .5 else (2 if s[1] > .5 else 0)

# small chest parts: connected pieces under 60 vertices in the chest band (cord lumps, links, pendant, clasp)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen, detail = set(), set()
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); stack.append(y)
    z = np.mean([(mw @ x.co).z for x in comp])
    if len(comp) < 60 and 1.15 < z < 1.45:
        detail |= {f.index for x in comp for f in x.link_faces}
bm.free()
detail &= body
part = [0] * len(me.polygons); me.attributes['chest_part'].data.foreach_get('value', part)
flat = {p.index for p in me.polygons if part[p.index]}      # cord, links, pendant: one flat colour square each
detail -= flat
for fi in detail | flat:
    cls[fi] = 0
print('BODY faces', len(body), 'detail (clasp)', len(detail), 'flat colour parts', len(flat))
smart = body - flat

me.uv_layers.new(name='BodyUV'); me.uv_layers.active = me.uv_layers['BodyUV']
bpy.context.view_layer.objects.active = cand
for o in bpy.context.view_layer.objects:
    o.select_set(o == cand)
bpy.context.scene.tool_settings.use_uv_select_sync = True
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE')


def select(faces):
    b = bmesh.from_edit_mesh(me); b.faces.ensure_lookup_table()
    for f in b.faces:
        f.select_set(f.index in faces)
    bmesh.update_edit_mesh(me)


def overlapping(N=1024):
    b = bmesh.from_edit_mesh(me); b.faces.ensure_lookup_table(); layer = b.loops.layers.uv['BodyUV']
    owner = np.full((N, N), -1, np.int64); bad = set()
    for fi in smart:
        pts = [l[layer].uv for l in b.faces[fi].loops]
        for k in range(1, len(pts) - 1):
            q = np.array([pts[0][:], pts[k][:], pts[k + 1][:]]) * N
            lo = np.maximum(0, np.floor(q.min(0)).astype(int)); hi = np.minimum(N - 1, np.ceil(q.max(0)).astype(int))
            m = np.column_stack([q[1] - q[0], q[2] - q[0]])
            if hi[0] < lo[0] or hi[1] < lo[1] or abs(np.linalg.det(m)) < 1e-9:
                continue
            xx, yy = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
            w = (np.stack([xx, yy], -1) - q[0]) @ np.linalg.inv(m).T
            inside = (w[..., 0] > 1e-4) & (w[..., 1] > 1e-4) & (w.sum(-1) < .9999)
            block = owner[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]; hits = block[inside & (block >= 0) & (block != fi)]
            if len(hits):
                bad.add(fi); bad.update(int(x) for x in hits)
            block[inside] = fi
    return bad


def layout():
    select(smart); bpy.ops.uv.average_islands_scale()
    b = bmesh.from_edit_mesh(me); b.faces.ensure_lookup_table(); layer = b.loops.layers.uv['BodyUV']
    for fi in detail:
        for loop in b.faces[fi].loops:
            loop[layer].uv *= 2.0
    bmesh.update_edit_mesh(me)
    select(smart); bpy.ops.uv.pack_islands(margin=.003, rotate=True, shape_method=os.environ.get('REA_PACK', 'CONCAVE'))


for grp in (detail, smart - detail):
    select(grp); bpy.ops.uv.smart_project(angle_limit=math.radians(float(os.environ.get('REA_ANGLE', '80'))), island_margin=.002, scale_to_bounds=False)
layout()
for attempt in range(6):
    bad = overlapping(); print('OVERLAP faces', len(bad), flush=True)
    if not bad:
        break
    for grp in (bad & detail, bad - detail):
        if grp:
            select(grp); bpy.ops.uv.smart_project(angle_limit=math.radians(30), island_margin=.002, scale_to_bounds=False)
    layout()
assert not bad, 'unresolved body UV overlap'
# flat colour squares in a bottom strip: the packed layout is scaled by .97 and lifted by .03
b = bmesh.from_edit_mesh(me); b.faces.ensure_lookup_table(); layer = b.loops.layers.uv['BodyUV']
for fi in smart:
    for loop in b.faces[fi].loops:
        u, v = loop[layer].uv; loop[layer].uv = (u * .97, .03 + v * .97)
SQUARES = {1: (.02, .004), 2: (.06, .004), 3: (.10, .004), 4: (.14, .004)}   # lower-left corners, 0.022 wide
for fi in flat:
    x0, y0 = SQUARES[part[fi]]; tri = [(.25, .25), (.75, .25), (.5, .75), (.25, .75)]
    for k, loop in enumerate(b.faces[fi].loops):
        u, v = tri[k % 4]; loop[layer].uv = (x0 + u * .022, y0 + v * .022)
bmesh.update_edit_mesh(me)
json_path = os.path.join(HERE, 'work', 'flat_squares.json')
import json; json.dump({str(k): [x0, y0, .022] for k, (x0, y0) in SQUARES.items()}, open(json_path, 'w'))
bpy.ops.object.mode_set(mode='OBJECT')
bu = me.uv_layers['BodyUV']; main = me.uv_layers[0]; assert main.name != 'BodyUV'
cu, cp, cdet, ccls, cpart = [], [], [], [], []
me.calc_loop_triangles()
for t in me.loop_triangles:
    if t.polygon_index not in body:
        continue
    for li, vi in zip(t.loops, t.vertices):
        cu.append(bu.data[li].uv[:]); cp.append((mw @ me.vertices[vi].co)[:])
    cdet.append(t.polygon_index in detail); ccls.append(cls[t.polygon_index]); cpart.append(part[t.polygon_index])
for p in me.polygons:
    if p.index in body:
        for li in p.loop_indices:
            u, v = bu.data[li].uv
            main.data[li].uv = (u * H / W, v)
np.savez(os.path.join(HERE, 'work', 'body_uv.npz'), uv=np.array(cu).reshape(-1, 3, 2), pos=np.array(cp).reshape(-1, 3, 3),
         detail=np.array(cdet), cls=np.array(ccls), part=np.array(cpart))

up = cand.copy(); up.data = me.copy(); up.name = 'SwordsmanBodyUpload'; bpy.context.scene.collection.objects.link(up)
up.parent = None; up.matrix_world = mw.copy(); up.modifiers.clear(); up.vertex_groups.clear()
b = bmesh.new(); b.from_mesh(up.data); b.faces.ensure_lookup_table()
bmesh.ops.delete(b, geom=[f for f in b.faces if f.index not in body], context='FACES'); b.to_mesh(up.data); b.free()
up.data.uv_layers.remove(up.data.uv_layers[0]); up.data.materials.clear()
m = bpy.data.materials.new('Neutral'); m.use_nodes = True; up.data.materials.append(m)
for o in bpy.context.view_layer.objects:
    o.select_set(o == up)
bpy.context.view_layer.objects.active = up
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'body_upload.glb'), use_selection=True,
                          export_format='GLB', export_animations=False, export_skins=False, export_attributes=False)
bpy.data.objects.remove(up, do_unlink=True)
me.uv_layers.remove(me.uv_layers['BodyUV']); me.uv_layers.active = me.uv_layers[0]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_body.blend'))
print('UPLOAD body faces', len(body))
