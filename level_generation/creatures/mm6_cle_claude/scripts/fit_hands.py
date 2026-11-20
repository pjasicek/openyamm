"""Seat the MPFB hands (work/hands/mpfb_hands.blend, hands_mpfb.py) on the cleric (work/rig_v4.blend, in place).

User review 2026-10-14: both Meshy hands looked bad (the right a closed ring, the left a crude fist). The new hands
are separate skinned objects HandL / HandR; export_runtime.py removes the old hand faces (hand-bone weight > 0.5)
and joins them, so the master's face order (cloak_sides.json, uv3d.npz) stays valid.

- Left: the fist's grip cylinder (axis toward the thumb side) goes onto the staff axis (toward the staff tip); the
  roll about the axis puts the MPFB wrist on our wrist side; slid along the axis so the wrists line up.
- Right: MPFB hand direction -> ours (wrist -> old hand centroid), palm toward the thigh (+X); wrist on our wrist.
- Uniform MPFB scale (same body height). Decimated to DECIM of the MPFB density; the forearm stub stays in the cuff.
- UVs: `HandUV` packed into a square of the head texture set's freed top-right corner (hand_texture_set.py scales
  the head set to HEAD_SCALE), `MHUV` keeps MakeHuman's layout for the skin bake (bake_hands.py).
- Old hand faces: face attribute `old_hand` on the master (hand-weighted faces painted skin, not the gold cuff).
- Weights: every vertex past the wrist 100 % on the hand bone; stub vertices copy the nearest cleric vertex's weights
  (the cuff and sleeve skin under them). Face attribute `hand` = 1.
Writes work/hands/fit.json (squares, frames) and work/hands/old_hand_uvs.json (old skin face UV centroids)."""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Vector, Matrix, kdtree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

HANDS = os.path.join(common.WORK, 'hands')
HEAD_SCALE = 0.8
SQUARES = {'HandL': (0.8, 0.8), 'HandR': (0.8, 0.6)}       # lower-left corners of 0.2 squares in head-set UV space
DECIM = 0.3
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v4.blend'))
rig, mesh = bpy.data.objects['Cleric_Rig'], bpy.data.objects['Cleric']
for n in ('HandL', 'HandR'):
    if n in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
F = json.load(open(os.path.join(HANDS, 'mpfb_frames.json')))
S = F['scale']
with bpy.data.libraries.load(os.path.join(HANDS, 'mpfb_hands.blend')) as (src, dst):
    dst.objects = ['HandL', 'HandR']
for o in dst.objects:
    bpy.context.scene.collection.objects.link(o)
J = lambda n: rig.matrix_world @ rig.pose.bones[n].head
V = lambda a: Vector(a)

# old hand vertices (excluded from the weight source)
names = {g.index: g.name for g in mesh.vertex_groups}
hand_w = {s: np.zeros(len(mesh.data.vertices)) for s in ('LeftHand', 'RightHand')}
for v in mesh.data.vertices:
    for g in v.groups:
        if names[g.group] in hand_w:
            hand_w[names[g.group]][v.index] = g.weight
# the old hand faces export_runtime.py removes: hand-weighted faces painted skin (not the gold cuff), face attribute
# `old_hand` (weights alone also took the cuff's lower ring and left a jagged edge)
img = bpy.data.images.load(os.path.join(common.PROJECT, 'textures', 'cle_a_basecolor_1k.png'))
IW, IH = img.size; px = np.array(img.pixels[:], np.float32).reshape(IH, IW, img.channels)
head_f = np.zeros(len(mesh.data.polygons), np.int32); mesh.data.attributes['head'].data.foreach_get('value', head_f)
uvd = mesh.data.uv_layers.active.data
old = np.zeros(len(mesh.data.polygons), np.int32)
for p in mesh.data.polygons:
    w = max(hand_w['LeftHand'][list(p.vertices)].mean(), hand_w['RightHand'][list(p.vertices)].mean())
    if w <= .5 or head_f[p.index]:
        continue
    u = np.mean([uvd[l].uv[0] for l in p.loop_indices]); v = np.mean([uvd[l].uv[1] for l in p.loop_indices])
    r, g, b = px[min(IH - 1, int(v * IH)), min(IW - 1, int(u * IW))][:3]
    mx, mn = max(r, g, b), min(r, g, b); sat = (mx - mn) / max(mx, 1e-6)
    hue = ((g - b) / max(mx - mn, 1e-6) / 6.0) % 1.0 if mx == r else 0.3
    gold = sat >= 0.6 and 0.075 <= hue <= 0.16
    old[p.index] = 0 if gold else 1
if 'old_hand' in mesh.data.attributes:
    mesh.data.attributes.remove(mesh.data.attributes['old_hand'])
mesh.data.attributes.new('old_hand', 'INT', 'FACE').data.foreach_set('value', old)
json.dump([[float(np.mean([uvd[l].uv[k] for l in p.loop_indices])) for k in (0, 1)]
           for p in mesh.data.polygons if old[p.index]], open(os.path.join(HANDS, 'old_hand_uvs.json'), 'w'))
bpy.data.images.remove(img)
dg = bpy.context.evaluated_depsgraph_get()
me_ev = mesh.evaluated_get(dg).to_mesh()
P = [mesh.matrix_world @ v.co for v in me_ev.vertices]
old_v = {v for p in mesh.data.polygons if old[p.index] for v in p.vertices}
src_ok = [i for i in range(len(P)) if i not in old_v]
kd = kdtree.KDTree(len(src_ok))
for k, i in enumerate(src_ok):
    kd.insert(P[i], k)
kd.balance()


def frame(xa, ya):
    """orthonormal 3x3 with columns x, y (made orthogonal to x), z"""
    x = xa.normalized(); y = (ya - x * ya.dot(x)).normalized()
    return Matrix((x, y, x.cross(y))).transposed()


out = {'head_scale': HEAD_SCALE, 'squares': {}}
for name, side in (('HandL', 'Left'), ('HandR', 'Right')):
    o = bpy.data.objects[name]; fr = F[name]
    W = J(side + 'Hand')
    if name == 'HandL':
        stf = rig.matrix_world @ rig.pose.bones['Staff'].matrix
        a_c = (stf.to_3x3() @ Vector((0, 1, 0))).normalized(); o_c = stf.to_translation()
        a_m, c_m, w_m = V(fr['axis']), V(fr['centre']), V(fr['wrist'])
        perp_m = (w_m - c_m) - a_m * (w_m - c_m).dot(a_m)
        perp_c = (W - o_c) - a_c * (W - o_c).dot(a_c)
        R = frame(a_c, perp_c) @ frame(a_m, perp_m).inverted()
        along = (w_m - c_m).dot(a_m) * S
        c_c = o_c + a_c * ((W - o_c).dot(a_c) - along)
        T = Matrix.Translation(c_c) @ (R.to_4x4() @ Matrix.Scale(S, 4)) @ Matrix.Translation(-c_m)
        out['wrist_offset_mm_L'] = round(((T @ w_m) - W).length * 1000, 1)
    else:
        h_m, n_m, w_m = V(fr['h']), V(fr['n']), V(fr['wrist'])
        cen = Vector(json.load(open(os.path.join(HANDS, 'measure.json')))['Right']['centroid'])
        h_c = (cen - W).normalized(); n_c = Vector((1, 0, 0))
        R = frame(h_c, n_c) @ frame(h_m, n_m).inverted()
        T = Matrix.Translation(W) @ (R.to_4x4() @ Matrix.Scale(S, 4)) @ Matrix.Translation(-w_m)
    o.data.transform(T); o.matrix_world = Matrix.Identity(4)
    # decimate (collapse keeps both UV layers; the islands are re-cut afterwards)
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.context.view_layer.objects.active = o
    d = o.modifiers.new('Dec', 'DECIMATE'); d.ratio = DECIM; d.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=d.name)
    o.data.uv_layers[0].name = 'MHUV'
    uv = o.data.uv_layers.new(name='HandUV'); o.data.uv_layers.active = uv
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    u0, v0 = SQUARES[name]; side_len = 1.0 - HEAD_SCALE
    uv = o.data.uv_layers['HandUV']          # re-fetched: the edit-mode round trip invalidates the earlier reference
    for l in uv.data:
        l.uv = (u0 + l.uv[0] * side_len, v0 + l.uv[1] * side_len)
    out['squares'][name] = [u0, v0, side_len]
    # weights
    o.vertex_groups.clear()
    groups = {g.name: o.vertex_groups.new(name=g.name) for g in mesh.vertex_groups}
    hd = (T.to_3x3() @ V(fr['h'])).normalized()
    stub = 0
    for v in o.data.vertices:
        if (v.co - W).dot(hd) >= 0.0:
            groups[side + 'Hand'].add([v.index], 1.0, 'REPLACE'); continue
        stub += 1
        _, k, _ = kd.find(v.co); src_v = mesh.data.vertices[src_ok[k]]
        for g in src_v.groups:
            groups[names[g.group]].add([v.index], g.weight, 'REPLACE')
    a = o.modifiers.new('Armature', 'ARMATURE'); a.object = rig
    o.parent = rig
    o.matrix_parent_inverse = rig.matrix_world.inverted()
    attr = o.data.attributes.new('hand', 'INT', 'FACE')
    attr.data.foreach_set('value', [1] * len(o.data.polygons))
    for p in o.data.polygons:
        p.use_smooth = True
    out[name] = dict(tris=sum(len(p.vertices) - 2 for p in o.data.polygons), stub_vertices=stub)
json.dump(out, open(os.path.join(HANDS, 'fit.json'), 'w'), indent=1)
print('FIT_HANDS', json.dumps(out))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v4.blend'))
