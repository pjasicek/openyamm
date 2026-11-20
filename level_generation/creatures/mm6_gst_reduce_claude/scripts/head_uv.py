"""Fresh head-set UVs for the picked reduction (work/ladder_skull60.blend, Cand_55): head faces (atlas u > 0.5) are
unwrapped again, skull and hood separately, texel density averaged and the skull islands doubled (linear) before
packing, so eyes and teeth get more texels. Writes
- work/ladder_head.blend: Cand_55 with the head faces' atlas UVs in the head half (body UVs unchanged),
- texturing/head_upload.glb: head faces only, rest pose, head UVs in 0..1 (Meshy retexture, enable_original_uv),
- work/head_uv.npz: per head triangle corner the 0..1 head UV and rest world position, and the skull flag.
Usage: blender -b -P head_uv.py"""
import math, os, bmesh, bpy
import numpy as np
from mathutils import kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, G, H = 2080, 32, 1024  # merged atlas width, gutter, half width (tools/merge_head_material.py)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_skull60.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
cand = bpy.data.objects['Cand_55']; me = cand.data; mw = cand.matrix_world

# skull faces: nearest source face centroid is a skull/eye face (work/bone_faces.npy, region mask)
src = np.load(os.path.join(HERE, 'work', 'mesh_in.npz')); bone = np.load(os.path.join(HERE, 'work', 'bone_faces.npy'))
cent = src['verts'][src['faces']].mean(1)
kd = kdtree.KDTree(len(cent))
for i, c in enumerate(cent):
    kd.insert(c, i)
kd.balance()
uvl = me.uv_layers.active
head, skull = set(), set()
for p in me.polygons:
    if np.mean([uvl.data[li].uv[0] for li in p.loop_indices]) > .5:
        head.add(p.index)
        if bone[kd.find(mw @ p.center)[1]]:
            skull.add(p.index)
print('HEAD faces', len(head), 'skull', len(skull), 'of', len(me.polygons))

me.uv_layers.new(name='HeadUV'); me.uv_layers.active = me.uv_layers['HeadUV']
bpy.context.view_layer.objects.active = cand
for o in bpy.context.view_layer.objects:
    o.select_set(o == cand)
cand.hide_set(False); cand.hide_viewport = False
bpy.context.scene.tool_settings.use_uv_select_sync = True
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_mode(type='FACE')


def select(faces):
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select_set(f.index in faces)
    bmesh.update_edit_mesh(me)


def overlapping(N=1024):
    """head faces whose UV triangles share texel centres with another (folded cloth projected onto itself)"""
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); layer = bm.loops.layers.uv['HeadUV']
    owner = np.full((N, N), -1, np.int64); bad = set()
    for fi in head:
        f = bm.faces[fi]; pts = [l[layer].uv for l in f.loops]
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
    select(head); bpy.ops.uv.average_islands_scale()
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); layer = bm.loops.layers.uv['HeadUV']
    for fi in skull:
        for loop in bm.faces[fi].loops:
            loop[layer].uv *= 2.0
    bmesh.update_edit_mesh(me)
    select(head); bpy.ops.uv.pack_islands(margin=.004, rotate=True, shape_method=os.environ.get('REA_PACK', 'CONVEX'))


for part in (skull, head - skull):
    select(part); bpy.ops.uv.smart_project(angle_limit=math.radians(80), island_margin=.002, scale_to_bounds=False)
layout()
for attempt in range(6):
    bad = overlapping(); print('OVERLAP faces', len(bad), flush=True)
    if not bad:
        break
    for part in (bad & skull, bad - skull):  # separate islands for the folded faces
        if part:
            select(part); bpy.ops.uv.smart_project(angle_limit=math.radians(30), island_margin=.002, scale_to_bounds=False)
    layout()
assert not bad, 'unresolved head UV overlap'
bpy.ops.object.mode_set(mode='OBJECT')
hu = me.uv_layers['HeadUV']  # layer references go stale across mode switches

# atlas UVs for the runtime candidate, dump for compose
main = me.uv_layers[0]; assert main.name != 'HeadUV'
corners_uv, corners_pos, corner_skull = [], [], []
me.calc_loop_triangles()
for t in me.loop_triangles:
    if t.polygon_index not in head:
        continue
    for li, vi in zip(t.loops, t.vertices):
        corners_uv.append(hu.data[li].uv[:]); corners_pos.append((mw @ me.vertices[vi].co)[:])
    corner_skull.append(t.polygon_index in skull)
for p in me.polygons:
    if p.index in head:
        for li in p.loop_indices:
            u, v = hu.data[li].uv
            main.data[li].uv = ((H + G + u * H) / W, v)
cuv = np.array(corners_uv).reshape(-1, 3, 2)
print('HEAD UV range', cuv.min((0, 1)), cuv.max((0, 1)))
np.savez(os.path.join(HERE, 'work', 'head_uv.npz'), uv=cuv, pos=np.array(corners_pos).reshape(-1, 3, 3),
         skull=np.array(corner_skull))

# head-only upload
up = cand.copy(); up.data = me.copy(); up.name = 'GhostHeadUpload'; bpy.context.scene.collection.objects.link(up)
up.parent = None; up.matrix_world = mw.copy(); up.modifiers.clear(); up.vertex_groups.clear()
bm = bmesh.new(); bm.from_mesh(up.data); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in head], context='FACES'); bm.to_mesh(up.data); bm.free()
up.data.uv_layers.remove(up.data.uv_layers[0]); up.data.materials.clear()
m = bpy.data.materials.new('Neutral'); m.use_nodes = True; up.data.materials.append(m)
for o in bpy.context.view_layer.objects:
    o.select_set(o == up)
bpy.context.view_layer.objects.active = up
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'head_upload.glb'), use_selection=True,
                          export_format='GLB', export_animations=False, export_skins=False, export_attributes=False)
bpy.data.objects.remove(up, do_unlink=True)
me.uv_layers.remove(me.uv_layers['HeadUV']); me.uv_layers.active = me.uv_layers[0]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_head.blend'))
print('UPLOAD faces', len(head))
