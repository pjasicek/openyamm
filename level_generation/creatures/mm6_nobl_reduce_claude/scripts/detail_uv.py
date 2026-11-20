"""Front detail texture set (third 1K section of the merged atlas, body | head | detail = 3136 wide): the faces in
work/detail_faces.json get their own UVs (smart project, density averaged, concave pack, overlaps re-projected); every
other face keeps its pixels (u rescaled from the 2080-wide atlas). Writes
- work/ladder_detail.blend (runtime UVs),
- texturing/detail_upload.glb: the whole mesh, detail faces filling 94 % of the UV square and every other face squeezed
  into the top-right 6 % corner, so Meshy paints the detail faces at high resolution while seeing the whole character,
- work/detail_uv.npz: per detail triangle corner the 0..1 detail UV and rest world position, its installed region
  class (0 none, 1 cloak, 2 tunic) and part (0).
Usage: blender -b -P detail_uv.py"""
import json, math, os, bmesh, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_W, NEW_W, X0 = 2080, 3136, 2112      # detail section starts after body 1024 + gutter 32 + head 1024 + gutter 32
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_body.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
cand = bpy.data.objects['Cand_62']; me = cand.data; mw = cand.matrix_world
groups = json.load(open(os.path.join(HERE, 'work', 'detail_faces.json')))
detail = {i for g in groups.values() for i in g}
region = [0] * len(me.polygons); me.attributes['inst_region'].data.foreach_get('value', region)   # detail_faces.py
cls = {fi: region[fi] for fi in detail}

me.uv_layers.new(name='DetailUV'); me.uv_layers.active = me.uv_layers['DetailUV']
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
    b = bmesh.from_edit_mesh(me); b.faces.ensure_lookup_table(); layer = b.loops.layers.uv['DetailUV']
    owner = np.full((N, N), -1, np.int64); bad = set()
    for fi in detail:
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
    select(detail); bpy.ops.uv.average_islands_scale()
    select(detail); bpy.ops.uv.pack_islands(margin=.004, rotate=True, shape_method='CONCAVE')


select(detail); bpy.ops.uv.smart_project(angle_limit=math.radians(80), island_margin=.002, scale_to_bounds=False)
layout()
for attempt in range(6):
    bad = overlapping(); print('OVERLAP faces', len(bad), flush=True)
    if not bad:
        break
    select(bad); bpy.ops.uv.smart_project(angle_limit=math.radians(30), island_margin=.002, scale_to_bounds=False)
    layout()
assert not bad, 'unresolved detail UV overlap'
bpy.ops.object.mode_set(mode='OBJECT')
du = me.uv_layers['DetailUV']; main = me.uv_layers[0]; assert main.name != 'DetailUV'

# upload UVs (layer 'Upload'): detail 94 %, everything else in the top-right corner
me.uv_layers.new(name='Upload'); up_uv = me.uv_layers['Upload']; du = me.uv_layers['DetailUV']; main = me.uv_layers[0]
for p in me.polygons:
    for li in p.loop_indices:
        if p.index in detail:
            u, v = du.data[li].uv; up_uv.data[li].uv = (u * .94, v * .94)
        else:
            u, v = main.data[li].uv; up_uv.data[li].uv = (.945 + u * .055, .945 + v * .055)
# runtime UVs
cu, cp, cc = [], [], []
me.calc_loop_triangles()
for t in me.loop_triangles:
    if t.polygon_index in detail:
        for li, vi in zip(t.loops, t.vertices):
            cu.append(du.data[li].uv[:]); cp.append((mw @ me.vertices[vi].co)[:])
        cc.append(cls[t.polygon_index])
for p in me.polygons:
    for li in p.loop_indices:
        if p.index in detail:
            u, v = du.data[li].uv; main.data[li].uv = ((X0 + u * 1024) / NEW_W, v)
        else:
            u, v = main.data[li].uv; main.data[li].uv = (u * OLD_W / NEW_W, v)
np.savez(os.path.join(HERE, 'work', 'detail_uv.npz'), uv=np.array(cu).reshape(-1, 3, 2), pos=np.array(cp).reshape(-1, 3, 3),
         cls=np.array(cc), part=np.zeros(len(cc), int), detail=np.zeros(len(cc), bool))

up = cand.copy(); up.data = me.copy(); up.name = 'SwordsmanDetailUpload'; bpy.context.scene.collection.objects.link(up)
up.parent = None; up.matrix_world = mw.copy(); up.modifiers.clear(); up.vertex_groups.clear()
for name in [l.name for l in up.data.uv_layers if l.name != 'Upload']:
    up.data.uv_layers.remove(up.data.uv_layers[name])
up.data.materials.clear(); m = bpy.data.materials.new('Neutral'); m.use_nodes = True; up.data.materials.append(m)
for p in up.data.polygons:
    p.material_index = 0
for o in bpy.context.view_layer.objects:
    o.select_set(o == up)
bpy.context.view_layer.objects.active = up
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'detail_upload.glb'), use_selection=True,
                          export_format='GLB', export_animations=False, export_skins=False, export_attributes=False)
bpy.data.objects.remove(up, do_unlink=True)
me.uv_layers.remove(me.uv_layers['Upload']); me.uv_layers.remove(me.uv_layers['DetailUV']); me.uv_layers.active = me.uv_layers[0]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_detail.blend'))
print('DETAIL faces', len(detail), 'triangles', len(cc))
