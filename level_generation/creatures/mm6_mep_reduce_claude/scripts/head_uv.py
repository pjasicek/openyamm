"""Fresh UVs for the face of the picked reduction (work/ladder_g3.blend, Cand_62) before a Meshy head retexture.
Head-set faces (atlas u > 0.5) whose installed colour is the pale-blue turban keep their island shapes; the other
head faces (face skin, eyes, brows, beard, neck cloth) are unwrapped again as whole charts (skin and eyes at 1.6x
density), and everything is packed again without overlaps. Writes
- work/ladder_head.blend: Cand_62 with the new atlas UVs (body and turban UVs unchanged),
- texturing/head_upload.glb: all head faces, rest pose, head UVs in 0..1 (Meshy retexture, enable_original_uv),
- work/head_uv.npz: per head triangle the corner UVs (0..1 head half, new) and the face-part flag.
Usage: blender -b -P head_uv.py"""
import math, os, bmesh, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, G, H = 2080, 32, 1024  # merged atlas width, gutter, head half width (tools/merge_head_material.py)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_g3.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
cand = bpy.data.objects['Cand_62']; me = cand.data; mw = cand.matrix_world

img = bpy.data.images.load(os.path.join(HERE, 'work', 'basecolor.png'))
iw, ih = img.size; px = np.array(img.pixels[:], np.float32).reshape(ih, iw, 4)  # bottom-up rows
uvl = me.uv_layers.active
rng = np.random.default_rng(1); B = rng.dirichlet((1, 1, 1), 12)
head, face, skin = set(), set(), set()
me.calc_loop_triangles()
for p in me.polygons:
    uv = np.array([uvl.data[li].uv[:] for li in p.loop_indices])
    if uv[:, 0].mean() <= .5:
        continue
    head.add(p.index)
    s = B @ uv[:3]
    c = px[np.clip((s[:, 1] * ih).astype(int), 0, ih - 1), np.clip((s[:, 0] * iw).astype(int), 0, iw - 1)] * 255
    if ((c[:, 2] - c[:, 0]) > 8).mean() <= .5:  # not the pale-blue turban
        face.add(p.index)
        if (((c[:, 0] - c[:, 2]) > 40) & (c[:, 0] > 70)).mean() > .3 or p.area < 2e-5:  # brown skin, eye pieces
            skin.add(p.index)
turban = head - face
print('HEAD faces', len(head), 'face part', len(face), 'skin/eyes', len(skin), 'turban kept', len(turban), 'of', len(me.polygons))

me.uv_layers.new(name='HeadUV'); hu = me.uv_layers['HeadUV']
for p in me.polygons:
    for li in p.loop_indices:
        u, v = uvl.data[li].uv
        hu.data[li].uv = ((u * W - (H + G)) / H, v)
me.uv_layers.active = hu
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


def pin_turban():
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); layer = bm.loops.layers.uv['HeadUV']
    for fi in head:
        for loop in bm.faces[fi].loops:
            loop[layer].pin_uv = fi in turban
    bmesh.update_edit_mesh(me)


def overlapping(N=1024):
    """face-part faces whose UV triangles share texel centres with any other head face"""
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); layer = bm.loops.layers.uv['HeadUV']
    owner = np.full((N, N), -1, np.int64); bad = set()
    for fi in list(turban) + list(face):  # turban first: its own folds are not ours to fix
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
            if fi in face and len(hits):
                bad.add(fi); bad.update(int(x) for x in hits if x in face)
            block[inside] = fi
    return bad


def layout():
    select(head); bpy.ops.uv.average_islands_scale()
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); layer = bm.loops.layers.uv['HeadUV']
    for fi in skin:  # islands are split at the skin edge below, so skin islands scale as a whole
        for loop in bm.faces[fi].loops:
            loop[layer].uv *= SKIN_SCALE
    bmesh.update_edit_mesh(me)
    select(head)
    bpy.ops.uv.pack_islands(rotate=True, scale=True, margin=.003, shape_method='CONCAVE')


SKIN_SCALE = float(os.environ.get('REA_SKIN_SCALE', '1.6'))
FACE_ANGLE = float(os.environ.get('REA_FACE_ANGLE', '80'))
for part in (skin, face - skin):
    select(part)
    if os.environ.get('REA_UNWRAP', '1') == '1':  # whole charts: the selection border is the seam
        bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, margin=.002)
    else:
        bpy.ops.uv.smart_project(angle_limit=math.radians(FACE_ANGLE), island_margin=.002, scale_to_bounds=False)
layout()
for attempt in range(6):
    bad = overlapping(); print('OVERLAP faces', len(bad), flush=True)
    if not bad:
        break
    for part in (bad & skin, bad - skin):
        if part:
            select(part); bpy.ops.uv.smart_project(angle_limit=math.radians(30), island_margin=.002, scale_to_bounds=False)
    layout()
assert not bad, 'unresolved face UV overlap'
bpy.ops.object.mode_set(mode='OBJECT')
hu = me.uv_layers['HeadUV']; main = me.uv_layers[0]; assert main.name != 'HeadUV'

# turban islands keep their shapes (moved, rotated and scaled as a whole by the packer); compose_head.py copies
# their texels per triangle from the installed layout

# density report (texels per cm in the 1024 head half)
def density(faces, layer, scale):
    a2 = a3 = 0.0
    for fi in faces:
        p = me.polygons[fi]; a3 += p.area
        q = [np.array(layer.data[li].uv[:]) * scale for li in p.loop_indices]
        a2 += sum(abs(np.cross(q[k] - q[0], q[k + 1] - q[0])) / 2 for k in range(1, len(q) - 1))
    return math.sqrt(a2 / (a3 * 1e4))
for nm, fs in (('skin', skin), ('rest', face - skin)):
    print('DENSITY', nm, 'old', round(density(fs, main, np.array([W, H])), 2), 'new', round(density(fs, hu, H), 2))

corners_uv, corners_old, corner_face, corners_pos = [], [], [], []
for t in me.loop_triangles:
    if t.polygon_index in head:
        corners_uv.append([hu.data[li].uv[:] for li in t.loops]); corner_face.append(t.polygon_index in face)
        corners_pos.append([(mw @ me.vertices[vi].co)[:] for vi in t.vertices])
        corners_old.append([((main.data[li].uv[0] * W - (H + G)) / H, main.data[li].uv[1]) for li in t.loops])
for fi in head:  # every head face takes its new atlas UV (turban texels are copied into the new layout)
    for li in me.polygons[fi].loop_indices:
        u, v = hu.data[li].uv
        main.data[li].uv = ((H + G + u * H) / W, v)
np.savez(os.path.join(HERE, 'work', 'head_uv.npz'), uv=np.array(corners_uv), old=np.array(corners_old), face=np.array(corner_face),
         pos=np.array(corners_pos),
         skin=np.array([t.polygon_index in skin for t in me.loop_triangles if t.polygon_index in head]))
np.save(os.path.join(HERE, 'work', 'head_faces.npy'), np.array(sorted(face)))

# head-only upload
os.makedirs(os.path.join(HERE, 'texturing'), exist_ok=True)
up = cand.copy(); up.data = me.copy(); up.name = 'MepHeadUpload'; bpy.context.scene.collection.objects.link(up)
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
