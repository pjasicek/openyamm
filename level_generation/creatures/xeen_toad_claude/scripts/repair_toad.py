"""D-118 repair of the Giant Toad (F57, no Meshy): reads the UV master work/anim_base.blend, writes
work/anim_repair.blend, which anim_toad.py keys the clips on. Mesh, UV layout and textures stay; three changes:

1. Hind legs. The heat weights gave each fused thigh/shin lobe mostly to Foot and Toes (0.39 / 0.35 of the piece), so
   a heel lift swung the whole lobe up over the back and tore it. New weights on the two hind-leg pieces: Toes and
   Foot own only the low front of the piece (the toes and the sole in front of the lobe); the lobe is Thigh with a
   share of Shin by distance to the bones; the inner rim keeps some Body so the hip stays on the trunk; then a few
   smoothing passes over the piece.
2. Mouth. The lip crease is painted near black; when the lips part the crease walls read as black slits. The crease
   faces (dark texels within 3 cm of the lip line, found from the paint: the lowest dark band per slice
   in front of the head) move to their own material `Mouth` (a small
   gradient texture, textures/toad_mouth.png: dark at the lip edge, red-brown deeper), with UVs (v = depth into the
   crease, by distance to the lip line) on that material only. The shell stays closed, so the crease becomes a
   closed cavity behind the lips.
   A `Jaw` bone (child of Head, hinge at the mouth corners) takes the lower lip and the lower crease wall, fading
   into the chin over 9 cm; the upper wall is Head. The mouth thus rides on the head (no opening when the head
   rears) and opens only where Attack keys the Jaw. Jaw, not Throat: the Throat bone's puff scale would push the
   lower lip about by up to 12 cm.
3. (anim_toad.py) the lower rear in Attack, limited heel lift in the hops, the tongue and throat kept in in Death.
"""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work'); TEX = os.path.join(HERE, 'textures')

bpy.ops.wm.open_mainfile(filepath=os.path.join(WORK, 'anim_base.blend'))
mesh = bpy.data.objects['Toad']; rig = bpy.data.objects['Toad_Rig']; me = mesh.data
co = np.array([v.co[:] for v in me.vertices]); NV = len(co)
names = [g.name for g in mesh.vertex_groups]
Wt = np.zeros((NV, len(names)))
for v in me.vertices:
    for g in v.groups:
        Wt[v.index, g.group] = g.weight


def gi(name):
    if name not in names:
        mesh.vertex_groups.new(name=name); names.append(name)
        global Wt
        Wt = np.hstack([Wt, np.zeros((NV, 1))])
    return names.index(name)


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)


def seg_dist(p, a, b):
    a = np.asarray(a); b = np.asarray(b); ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1), t


bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
nbr = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
comp = np.full(NV, -1); nc = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    stack = [v.index]; comp[v.index] = nc
    while stack:
        x = stack.pop()
        for o in nbr[x]:
            if comp[o] < 0:
                comp[o] = nc; stack.append(o)
    nc += 1

bones = rig.data.bones
B = {b.name: (np.array(b.head_local[:]), np.array(b.tail_local[:])) for b in bones}


def smooth(idx, cols, passes):
    """Average the weight columns over neighbours inside the vertex set idx."""
    inset = np.zeros(NV, bool); inset[idx] = True
    for _ in range(passes):
        new = Wt[:, cols].copy()
        for i in idx:
            nb = [j for j in nbr[i] if inset[j]]
            if nb:
                new[i] = 0.5 * Wt[i, cols] + 0.5 * Wt[nb][:, cols].mean(0)
        Wt[:, cols] = new


# ---------------------------------------------------------------- 1. hind legs
for s in ('L', 'R'):
    foot = gi(f'Foot_{s}')
    piece = np.bincount(comp, weights=Wt[:, foot] + Wt[:, gi(f'Toes_{s}')], minlength=nc)
    k = int(np.argmax(piece / np.bincount(comp, minlength=nc)))
    idx = np.where(comp == k)[0]; p = co[idx]
    cols = [gi(n) for n in ('Body', f'Thigh_{s}', f'Shin_{s}', f'Foot_{s}', f'Toes_{s}')]
    toeb = B[f'Toes_{s}'][0]
    dT, _ = seg_dist(p, *B[f'Thigh_{s}']); dS, _ = seg_dist(p, *B[f'Shin_{s}'])
    # toes: in front of the toe base and low; foot: the sole, fading out over 25 cm behind the toe base so that the
    # lobe and the sole part gradually (a hard seam there tore in the first trial); the rest is the lobe, Thigh with a
    # share of Shin by distance
    toes = ss(toeb[1] + 0.04, toeb[1] - 0.04, p[:, 1]) * (1 - ss(0.06, 0.11, p[:, 2]))
    sole = (1 - ss(toeb[1] + 0.04, toeb[1] + 0.30, p[:, 1])) * (1 - ss(0.05, 0.14, p[:, 2])) * (1 - toes)
    lobe = 1 - toes - sole
    w = np.zeros((len(idx), 5))
    t_ = 1.0 / (dT + 0.03) ** 4; s_ = 0.6 / (dS + 0.03) ** 4
    w[:, 1] = lobe * t_ / (t_ + s_); w[:, 2] = lobe * s_ / (t_ + s_)
    w[:, 3] = sole; w[:, 4] = toes
    w /= w.sum(1, keepdims=True)
    hip = B[f'Thigh_{s}'][0]
    dh = np.linalg.norm(p - hip, axis=1)
    body = 0.6 * (1 - ss(0.06, 0.22, dh))                   # the hip rim stays with the trunk
    w[:, 1:] *= (1 - body)[:, None]; w[:, 0] = body
    Wt[idx] = 0.0
    Wt[np.ix_(idx, cols)] = w
    smooth(idx, cols, 8)
    tot = Wt[idx][:, cols].sum(0) / len(idx)
    print('LEG', s, 'piece', k, 'verts', len(idx), 'share', {names[c]: round(float(t), 2) for c, t in zip(cols, tot)})

# ---------------------------------------------------------------- 2. mouth
body_piece = int(np.argmax(np.bincount(comp)))
img = bpy.data.images.load(os.path.join(TEX, 'toad_basecolor_graded.png')); IW, IH = img.size
px = np.empty(IW * IH * 4, np.float32); img.pixels.foreach_get(px)
lum = px.reshape(IH, IW, 4)[:, :, :3].mean(2)               # row 0 = bottom (v = 0)
uvl = me.uv_layers.active.data
fc = np.array([f.center[:] for f in me.polygons])
flum = np.empty(len(fc))
for f in me.polygons:
    u = np.mean([uvl[li].uv[0] for li in f.loop_indices]); v = np.mean([uvl[li].uv[1] for li in f.loop_indices])
    flum[f.index] = lum[min(IH - 1, int(v * IH)), min(IW - 1, int(u * IW))]
fbody = np.array([comp[f.vertices[0]] == body_piece for f in me.polygons])
# the lip line from the paint (work/lip.json from lip_detect.py follows the brow and eye creases at the sides, z up
# to 0.76). The painted crease is one clean band (review: a scatter of dark faces): z 0.675 at the snout falling to
# about 0.59 at the corners (y -0.5, x +-0.38). Dark faces within 3.5 cm of that rough line, per 5-degree slice about
# the head axis, give the line.
zg = 0.59 + np.clip((-0.52 - fc[:, 1]) / 0.42, 0, 1) * 0.085
dark = fbody & (flum < 0.16) & (fc[:, 1] < -0.49) & (np.abs(fc[:, 2] - zg) < 0.035)
rel = fc - np.array([0.0, -0.50, 0.0])
az = np.degrees(np.arctan2(rel[:, 0], -rel[:, 1]))
pts = []
for a0 in range(-110, 111, 5):
    sel = np.where(dark & (np.abs(az - a0) < 2.5))[0]
    if len(sel) >= 3:
        pts.append(np.median(fc[sel], axis=0))
LIP = np.array(pts)
LIP = np.array([LIP[max(0, i - 1):i + 2].mean(0) for i in range(len(LIP))])
print('LIP points', len(LIP), 'z', round(float(LIP[:, 2].min()), 3), '..', round(float(LIP[:, 2].max()), 3),
      'ends', np.round(LIP[0], 3), np.round(LIP[-1], 3), 'front', np.round(LIP[np.argmin(LIP[:, 1])], 3))
dl = np.full(NV, 9.0); zl = np.zeros(NV)
for a, b in zip(LIP[:-1], LIP[1:]):
    d, t = seg_dist(co, a, b)
    better = d < dl
    dl[better] = d[better]; zl[better] = (a + t[:, None] * (b - a))[better, 2]
mouth = set()
for f in me.polygons:
    vs = list(f.vertices)
    if fbody[f.index] and dl[vs].mean() < 0.025 and flum[f.index] < 0.16:
        mouth.add(f.index)
# close small gaps, drop specks: a face joins when two of its edge neighbours are in, leaves when none is
for _ in range(2):
    add = set()
    for f in bm.faces:
        if f.index in mouth or dl[[v.index for v in f.verts]].mean() > 0.04:
            continue
        if sum(1 for e in f.edges for g in e.link_faces if g is not f and g.index in mouth) >= 2:
            add.add(f.index)
    mouth |= add
mouth = {i for i in mouth if any(g.index in mouth for e in bm.faces[i].edges for g in e.link_faces
                                 if g.index != i)}
mverts = sorted({v.index for i in mouth for v in bm.faces[i].verts})
# depth into the crease: edge hops from the region's rim (vertices shared with skin faces)
rim = [v for v in mverts if any(f.index not in mouth for f in bm.verts[v].link_faces)]
depth = {v: 0 for v in rim}; front_q = list(rim)
inm = set(mverts)
while front_q:
    nxt = []
    for v in front_q:
        for o in nbr[v]:
            if o in inm and o not in depth:
                depth[o] = depth[v] + 1; nxt.append(o)
    front_q = nxt
dmax = max(depth.values()) if depth else 1
print('MOUTH faces', len(mouth), 'verts', len(mverts), 'rim', len(rim), 'depth max', dmax)

# Mouth material slot 1 (export_glb.py builds the real materials by slot)
while len(me.materials) < 1:
    me.materials.append(bpy.data.materials.new('Toad_A'))
mm = bpy.data.materials.get('Mouth') or bpy.data.materials.new('Mouth')
me.materials.append(mm)
slot = len(me.materials) - 1
assert slot == 1, f'expected the body on slot 0 alone, got {len(me.materials)} slots'
for i in mouth:
    me.polygons[i].material_index = slot
    for li in me.polygons[i].loop_indices:
        vi = me.loops[li].vertex_index
        # u along the mouth (x), v into the crease (1 on the lip line, the crease bottom); a constant u made zero-area UV triangles that the far-LOD
        # texture transfer (lod_repair_claude) cannot rasterize
        uvl[li].uv = (0.5 + 0.9 * float(co[vi, 0]), float(np.clip(1 - dl[vi] / 0.025, 0, 1)))

# gradient texture: v = 0 at the lip edge (near the crease paint), v = 1 inside
TW, TH = 16, 64
grad = np.zeros((TH, TW, 4), np.float32)
edge = np.array([0.20, 0.11, 0.09]); deep = np.array([0.52, 0.25, 0.22])   # sRGB
rng = np.random.default_rng(118)
for r in range(TH):
    t = r / (TH - 1)
    c = edge + (deep - edge) * (t ** 0.8)
    grad[r, :, :3] = c * (1 + 0.06 * rng.standard_normal((TW, 1)))
grad[:, :, 3] = 1
gi_ = bpy.data.images.new('toad_mouth', TW, TH, alpha=False)
gi_.pixels.foreach_set(grad.ravel())
gi_.filepath_raw = os.path.join(TEX, 'toad_mouth.png'); gi_.file_format = 'PNG'
gi_.save()
print('MOUTH texture', gi_.filepath_raw)

# Jaw bone: hinge between the mouth corners, tail at the front of the lower lip
corners = LIP[[0, -1]]
hinge = Vector((0.0, float(corners[:, 1].mean()) + 0.02, float(corners[:, 2].mean()) - 0.02))
fr = LIP[np.argmin(LIP[:, 1])]
tip = Vector((0.0, float(fr[1]) + 0.04, float(fr[2]) - 0.05))
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
jb = rig.data.edit_bones.new('Jaw'); jb.head = hinge; jb.tail = tip; jb.align_roll(Vector((0, 0, 1)))
jb.parent = rig.data.edit_bones['Head']; jb.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
rig.pose.bones['Jaw'].rotation_mode = 'QUATERNION'
print('JAW', tuple(round(x, 3) for x in hinge), '->', tuple(round(x, 3) for x in tip))

jaw = gi('Jaw'); head = gi('Head')
# side of the lip line: upper / lower by height, the crease walls by their faces' normals
mside = {}
for i in mouth:
    nz = me.polygons[i].normal.z
    for v in me.polygons[i].vertices:
        mside.setdefault(v, []).append(nz)
dz = co[:, 2] - zl
inbody = comp == body_piece
chest = gi('Chest')
# near the lip line (fading over 3-10 cm, and behind the hinge) the Chest share moves to Head above the line and the
# Chest and Head shares move to Jaw below it; Throat (the puff) and the upper arms keep theirs. No hard assignment,
# so the cheeks keep their blend.
region = np.where(inbody & (dl < 0.10) & (co[:, 1] < hinge.y + 0.06))[0]
for v in region:
    if v in mside:
        lower = ss(-0.25, 0.25, float(np.mean(mside[v])))   # the lower crease wall faces up
    else:
        lower = 1 - ss(-0.004, 0.006, dz[v])
    f = (1 - ss(0.03, 0.10, dl[v])) * (1 - ss(hinge.y - 0.02, hinge.y + 0.06, co[v, 1]))
    if f <= 0:
        continue
    to_jaw = lower * f * (Wt[v, chest] + Wt[v, head])
    to_head = (1 - lower) * f * Wt[v, chest]
    Wt[v, chest] *= 1 - f
    Wt[v, head] *= 1 - lower * f
    Wt[v, head] += to_head
    Wt[v, jaw] += to_jaw
smooth(region[dl[region] > 0.012], list(range(len(names))), 2)

# ---------------------------------------------------------------- write groups
Wt[Wt < 1e-3] = 0
Wt /= np.maximum(Wt.sum(1, keepdims=True), 1e-9)
for gidx, g in enumerate(mesh.vertex_groups):
    col = Wt[:, names.index(g.name)]
    zero = np.where(col == 0)[0].tolist()
    if zero:
        g.remove(zero)
    for v in np.where(col > 0)[0]:
        g.add([int(v)], float(col[v]), 'REPLACE')
print('JAW verts', int((Wt[:, jaw] > 0.01).sum()), 'full', int((Wt[:, jaw] > 0.99).sum()))
empty = int((Wt.sum(1) == 0).sum())
print('UNWEIGHTED', empty)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'anim_repair.blend'))
print('SAVED anim_repair.blend')
