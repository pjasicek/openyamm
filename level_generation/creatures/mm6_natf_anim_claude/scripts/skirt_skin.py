"""Replace natf's 60-bone skirt cage (per-clip simulated chains that flare the skirt into a bell in Standing and stay at
rest in any clip without a simulation) with skinning to the pelvis and both thighs, and give the slim rest shape a
small clearance over the thighs.

Weights: every vertex the cage drove keeps its other weights for the non-cage share; the cage share goes to
pelvis/thighs: thigh share THIGH_MAX x smoothstep from z TOP (hip, all pelvis) to z BOTTOM (hem), split left/right by
a smoothstep over x (her left is +x) of half width SPLIT. Small separate pieces (feathers, fringe) use their centre
so they move rigidly.
Clearance: skirt vertices closer than CLEAR to the rest legs (signed along the leg normal) move out to CLEAR; the
displacement is smoothed over the skirt surface (SMOOTH Laplacian passes) and pieces move with their nearest point.
Usage: blender -b -P skirt_skin.py -- <runtime glb> <out blend>   (env THIGH_MAX, CLEAR, SPLIT override)"""
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

glb, out = sys.argv[sys.argv.index('--') + 1:][:2]
THIGH_MAX = float(os.environ.get('THIGH_MAX', '0.85'))
TOP, BOTTOM = float(os.environ.get('TOP', '0.93')), float(os.environ.get('BOTTOM', '0.55'))
SPLIT = float(os.environ.get('SPLIT', '0.09')); CLEAR = float(os.environ.get('CLEAR', '0.015'))
SMOOTH = 6
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 60  # import the 60 Hz clips on whole frames (the swing bake keys every frame)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Natf']; me = body.data

# swing-only thigh helpers: the skirt must follow the thighs' swing but not their twist (Standing twists the left
# thigh 16 deg about its axis; a skirt weighted to the thigh sheared into creases against the pelvis-weighted top)
from mathutils import Quaternion  # noqa: E402
SWING = {'B_L_Thigh': 'B_L_ThighSwing', 'B_R_Thigh': 'B_R_ThighSwing'}
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
for t, h in SWING.items():
    tb = rig.data.edit_bones[t]; hb = rig.data.edit_bones.new(h)
    hb.head, hb.tail, hb.roll = tb.head.copy(), tb.tail.copy(), tb.roll
    hb.parent = rig.data.edit_bones['B_Pelvis']; hb.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
sc = bpy.context.scene
for act in bpy.data.actions:
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for t, h in SWING.items():
            M = rig.pose.bones[t].matrix_basis; q = M.to_quaternion()
            tw = Quaternion((q.w, 0.0, q.y, 0.0)); tw.normalize()  # twist about the bone's own Y axis
            hp = rig.pose.bones[h]; hp.rotation_mode = 'QUATERNION'
            hp.rotation_quaternion = q @ tw.inverted(); hp.location = M.translation
            hp.keyframe_insert('rotation_quaternion', frame=f); hp.keyframe_insert('location', frame=f)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body:
        bpy.data.objects.remove(o, do_unlink=True)
groups = {g.index: g.name for g in body.vertex_groups}
co = np.array([v.co[:] for v in me.vertices]); nv = len(co)
cage = np.array([sum(g.weight for g in v.groups if groups[g.group].startswith('Skirt_')) for v in me.vertices])
skirt = cage > 0


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# connected pieces of the welded mesh (glTF splits vertices at seams; group coincident vertices first)
key = {tuple(np.round(c, 6)): i for i, c in enumerate(co)}
weld = np.array([key[tuple(np.round(c, 6))] for c in co])
parent = np.arange(nv)


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i


for p in me.polygons:
    vs = [weld[i] for i in p.vertices]
    for a in vs[1:]:
        ra, rb = find(vs[0]), find(a)
        if ra != rb:
            parent[ra] = rb
piece = np.array([find(weld[i]) for i in range(nv)])
sizes = {p: int((piece == p).sum()) for p in np.unique(piece)}
small = np.array([sizes[piece[i]] <= 120 for i in range(nv)])
centre = {p: co[piece == p].mean(0) for p in np.unique(piece[skirt & small])}
at = np.array([centre[piece[i]] if skirt[i] and small[i] else co[i] for i in range(nv)])

# smooth the skirt cloth (Codex's narrowed rest shape has facet creases that the old cage flare hid): Taubin passes on
# the welded surface of cage-driven cloth between hem and waistband; hem, waistband and the rest stay pinned; feathers
# and fringe pieces ride along with their nearest cloth point
SMOOTH_SKIRT = int(os.environ.get('SMOOTH_SKIRT', '12'))
cloth = skirt & ~small & (cage >= 0.9) & (co[:, 2] > 0.56) & (co[:, 2] < 0.9)
reps = np.unique(weld[cloth]); free = np.zeros(nv, bool); free[reps] = True
nbrs = {r: set() for r in reps}
for e in me.edges:
    a_, b_ = weld[e.vertices[0]], weld[e.vertices[1]]
    if a_ in nbrs: nbrs[a_].add(b_)
    if b_ in nbrs: nbrs[b_].add(a_)
wpos = co[weld].copy()  # position per vertex via its representative (identical for welded copies)
rp = {r: co[r].copy() for r in np.unique(weld)}
for it in range(SMOOTH_SKIRT * 2):
    lam = 0.5 if it % 2 == 0 else -0.53
    upd = {}
    for r in reps:
        nb = [rp[j] for j in nbrs[r] if j != r]
        if nb:
            upd[r] = rp[r] + lam * (np.mean(nb, axis=0) - rp[r])
    rp.update(upd)
sdisp = np.zeros((nv, 3))
for i in range(nv):
    if free[weld[i]]:
        sdisp[i] = rp[weld[i]] - co[i]
cl = np.where(cloth)[0]
if len(cl):
    from mathutils.kdtree import KDTree as _KD
    kd0 = _KD(len(cl))
    for k, i in enumerate(cl):
        kd0.insert(Vector(co[i]), k)
    kd0.balance()
    for pc in np.unique(piece[skirt & small]):
        members = np.where(piece == pc)[0]
        sdisp[members] = sdisp[cl[kd0.find(Vector(centre[pc]))[1]]]
co = co + sdisp
centre = {p: co[piece == p].mean(0) for p in np.unique(piece[skirt & small])}
at = np.array([centre[piece[i]] if skirt[i] and small[i] else co[i] for i in range(nv)])
smooth_max = float(np.linalg.norm(sdisp, axis=1).max())

# legs: vertices dominated by thigh/calf/foot weights and not driven by the cage
legw = np.array([sum(g.weight for g in v.groups if any(t in groups[g.group] for t in ('Thigh', 'Calf', 'Foot', 'Toe')))
                 for v in me.vertices])
# everything the skirt must cover: legs and the body's own hip/buttock skin under it (the skirt is fused into the main
# body piece; the narrowed rest skirt dipped inside the hips, which then showed through in a stair pattern)
under = ~skirt & ~small & (co[:, 2] < 0.95)
leg = under
leg_faces = [tuple(p.vertices) for p in me.polygons if all(under[i] for i in p.vertices)]
tree = BVHTree.FromPolygons([Vector(c) for c in co], leg_faces)
waist_taper = lambda z: 1.0 - smoothstep(0.86, 0.95, z)

# clearance push at rest: required outward push per panel vertex, gathered into one smooth radial field over
# (angle about the pelvis axis, height) and applied to every skirt vertex alike, so the skirt's outer and inner walls
# and the pieces on it move together (a per-vertex push drove the inner wall through the outer one)
panel = skirt & ~small
ax = np.array([rig.data.bones['B_Pelvis'].head_local.x, rig.data.bones['B_Pelvis'].head_local.y])
NA, ZB, Z0, Z1 = 72, 28, 0.46, 1.04
def cell(p):
    t = (np.arctan2(p[..., 1] - ax[1], p[..., 0] - ax[0]) % (2 * np.pi)) / (2 * np.pi) * NA
    h = (np.clip(p[..., 2], Z0, Z1 - 1e-6) - Z0) / (Z1 - Z0) * ZB
    return t, h
grid = np.zeros((NA, ZB))
pushed = 0; raw_max = 0.0
for i in np.where(panel)[0]:
    q, n, _, _ = tree.find_nearest(Vector(co[i]))
    if q is None:
        continue
    d = (Vector(co[i]) - q).dot(n)
    if d < CLEAR:
        rad = np.array([co[i][0] - ax[0], co[i][1] - ax[1], 0.0]); rad /= max(np.linalg.norm(rad), 1e-9)
        need = (CLEAR - d) / max(0.35, float(np.dot(rad, np.array(n)))) * waist_taper(co[i][2])
        t, h = cell(co[i]); a_, z_ = int(t) % NA, int(h)
        grid[a_, z_] = max(grid[a_, z_], need); pushed += 1; raw_max = max(raw_max, need)
# dilate one cell, then blur (angle wraps); never below the required push
dil = grid.copy()
for da in (-1, 0, 1):
    for dz in (-1, 0, 1):
        sh = np.roll(grid, da, axis=0)
        sh = np.roll(sh, dz, axis=1) if dz else sh
        if dz == 1: sh[:, 0] = 0
        if dz == -1: sh[:, -1] = 0
        dil = np.maximum(dil, sh)
field = dil.copy()
for _ in range(SMOOTH):
    nb = (np.roll(field, 1, 0) + np.roll(field, -1, 0) + np.vstack([field[:, :1].T, field[:, :-1].T]).T
          + np.vstack([field[:, 1:].T, field[:, -1:].T]).T) / 4
    field = np.maximum(0.5 * field + 0.5 * nb, grid)
def sample(p):
    t, h = cell(p); a0 = np.floor(t).astype(int) % NA; a1 = (a0 + 1) % NA; fa = t - np.floor(t)
    z0 = np.clip(np.floor(h - 0.5).astype(int), 0, ZB - 1); z1 = np.clip(z0 + 1, 0, ZB - 1); fz = np.clip(h - 0.5 - z0, 0, 1)
    return ((field[a0, z0] * (1 - fa) + field[a1, z0] * fa) * (1 - fz) + (field[a0, z1] * (1 - fa) + field[a1, z1] * fa) * fz)
final = np.zeros((nv, 3))
for i in np.where(skirt)[0]:
    p = at[i]; rad = np.array([p[0] - ax[0], p[1] - ax[1], 0.0]); rad /= max(np.linalg.norm(rad), 1e-9)
    final[i] = rad * sample(p) * min(1.0, cage[i] * 1.5)
keep_normals = np.array([c.vector[:] for c in me.corner_normals])
for i in np.where(skirt)[0]:
    me.vertices[i].co = Vector(co[i] + final[i])
# normals of the moved skirt: area-weighted face normals, merged across glTF seam copies only when the original
# vertex normals agree (the cloth is double-sided: outer and inner layers share positions with opposite winding, and a
# position-only merge cancelled them into a lighter stair pattern); every other corner keeps its imported normal
vn0 = np.zeros((nv, 3))
for p in me.polygons:
    for li in p.loop_indices:
        vn0[me.loops[li].vertex_index] += keep_normals[li]
vn0 /= np.linalg.norm(vn0, axis=1, keepdims=True).clip(1e-12)
side = {}
nkey = np.zeros(nv, int)
for i in range(nv):
    k = tuple(np.round(co[i], 6)); lst = side.setdefault(k, [])
    for gid, ref in lst:
        if np.dot(ref, vn0[i]) > 0.3:
            nkey[i] = gid; break
    else:
        gid = i; lst.append((gid, vn0[i])); nkey[i] = gid
pos = np.array([v.co[:] for v in me.vertices]); acc = np.zeros((nv, 3))
for p in me.polygons:
    vs = list(p.vertices); a, b, c = pos[vs[0]], pos[vs[1]], pos[vs[2]]
    fn = np.cross(b - a, c - a)
    for i in vs:
        acc[nkey[i]] += fn
acc /= np.linalg.norm(acc, axis=1, keepdims=True).clip(1e-12)
corner = keep_normals.copy()
for p in me.polygons:
    for li in p.loop_indices:
        vi = me.loops[li].vertex_index
        if skirt[vi]:
            corner[li] = acc[nkey[vi]]
me.normals_split_custom_set(corner.tolist())

# weights
for n in ('B_Pelvis', 'B_L_ThighSwing', 'B_R_ThighSwing'):
    if n not in body.vertex_groups:
        body.vertex_groups.new(name=n)
vg = {g.name: g for g in body.vertex_groups}
pel_x = rig.data.bones['B_Pelvis'].head_local.x
for i in np.where(skirt)[0].tolist():
    v = me.vertices[i]; s0 = cage[i]
    other = {groups[g.group]: g.weight * 1.0 for g in v.groups if not groups[g.group].startswith('Skirt_')}
    tot = sum(other.values())
    if tot > 0:
        other = {k: w / tot * (1 - s0) for k, w in other.items()}
    x, _, z = at[i]
    s = THIGH_MAX * smoothstep(TOP, BOTTOM, z); left = smoothstep(-SPLIT, SPLIT, x - pel_x)
    add = {'B_Pelvis': 1 - s, 'B_L_ThighSwing': s * left, 'B_R_ThighSwing': s * (1 - left)}
    for k, w in add.items():
        other[k] = other.get(k, 0) + w * s0
    for g in list(v.groups):
        body.vertex_groups[g.group].remove([i])
    for k, w in other.items():
        if w > 1e-4:
            vg[k].add([i], w, 'REPLACE')
for g in [g for g in body.vertex_groups if g.name.startswith('Skirt_')]:
    body.vertex_groups.remove(g)
body.name = 'Body'
for a in bpy.data.actions:
    a.use_fake_user = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print(f'SMOOTH skirt cloth {len(reps)} welded points, max move {smooth_max * 1000:.1f} mm')
print(f'SKIRT {int(skirt.sum())} verts re-skinned ({int((skirt & small).sum())} in small pieces); clearance push on '
      f'{pushed} panel verts, raw max {raw_max * 1000:.1f} mm, final max {np.linalg.norm(final, axis=1).max() * 1000:.1f} mm')
