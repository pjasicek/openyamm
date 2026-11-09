"""PeasantM2 (from mm9_njam_claude/scripts/finish_nj.py): skirt lining, three rings up each bell sleeve from the cuff, trousers narrowed
under the hem, a dark cap inside the skirt, and a hair lining (an inner copy of the hair 2 mm in, flipped, with the hair's own paint, so
the hair reads as hair from below and behind instead of showing the culled inside).
After the paint (UVs frozen; nothing here moves painted faces or their UVs). From mm9_highwayman_claude/scripts/finish_hw.py's lining:
- lining: the whole coat skirt (part 7) and two face rings up each sleeve from the cuff, an inner copy 3 mm in, flipped, same weights,
  on the set's dark texel (work/dark_texel.json). A corpse seen from the feet shows a dark inside, not the back faces' void.
- cap: a plain dark disc across the inside of the skirt tube just under the belt, on the Spine, so nothing shows up the skirt but the
  hose tops and the dark (the brief's dark cap from the feet).
Args: <in blend> <out blend>"""
import bpy, bmesh, sys, json, os
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
DT = json.load(open(os.path.join(HERE, 'work', 'dark_texel.json')))
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
part = bm.faces.layers.int['part']; mat = bm.faces.layers.int['mat']
uvp_ = bm.loops.layers.uv['PartUV']
lin = bm.faces.layers.int.new('lining')
dv = bm.verts.layers.deform.verify()
sel = {f for f in bm.faces if f[part] == 7}
print('LINING skirt faces', len(sel))
# Meshy's short inner hem inside each bell cuff faces outward (its back showed from inside the opening): sleeve faces within 12 cm of the
# wrist with another tunic face less than 3 cm out along their normal are that inner layer; they go (the dark lining below replaces them)
from mathutils.bvhtree import BVHTree
rig0 = body.parent
HW = [np.array(rig0.matrix_world @ rig0.data.bones[f'Bip01 {s_} Hand'].head_local) for s_ in 'LR']
tf = [f for f in bm.faces if f[part] == 1]
bvh = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces])
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
hem = []
for f in tf:
    c = f.calc_center_median()
    if min(np.linalg.norm(np.array(c[:]) - h) for h in HW) > 0.12: continue
    loc, nrm, idx, dist = bvh.ray_cast(c + f.normal * 0.0005, f.normal, 0.03)
    if idx is not None and bm.faces[idx][part] == 1: hem.append(f)
bmesh.ops.delete(bm, geom=hem, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.faces.ensure_lookup_table()
print('LINING inner hem faces removed', len(hem))
# the same inner hem hangs a little below the outer rim at the front, so its back showed from the front: those faces (normal toward the
# arm axis, within 10 cm of the wrist) get a flipped copy 1 mm outward with their own paint (a two-sided hem)
hem2 = []
for f in bm.faces:
    if f[part] != 1: continue
    c = np.array(f.calc_center_median()[:])
    for s_ in 'LR':
        fa_ = np.array(rig0.matrix_world @ rig0.data.bones[f'Bip01 {s_} Forearm'].head_local); hd_ = HW['LR'.index(s_)]
        if np.sign(c[0]) != np.sign(hd_[0]) or np.linalg.norm(c - hd_) > 0.10: continue
        d = (hd_ - fa_) / np.linalg.norm(hd_ - fa_); r = c - (fa_ + d * ((c - fa_) @ d))
        if np.dot(np.array(f.normal[:]), r) / (np.linalg.norm(r) + 1e-9) < -0.3: hem2.append(f)
dh = bmesh.ops.duplicate(bm, geom=hem2)
nf2 = [x for x in dh['geom'] if isinstance(x, bmesh.types.BMFace)]
vn2 = {}
for f in nf2:
    for v in f.verts: vn2.setdefault(v, Vector()); vn2[v] += f.normal
for v, n_ in vn2.items():
    if n_.length > 1e-12: v.co = v.co - n_.normalized() * 0.001
bmesh.ops.reverse_faces(bm, faces=nf2)
bm.faces.ensure_lookup_table()
print('LINING two-sided hem faces', len(nf2))
# bell cuffs (Meshy closed the rim with a short inner hem, no boundary): the outer sleeve wall within 15 cm of the wrist gets the lining
rig = body.parent
JW = {s_: (np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s_} Forearm'].head_local), np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s_} Hand'].head_local)) for s_ in 'LR'}
nc = 0
for f in bm.faces:
    if f[part] != 1: continue
    c = np.array(f.calc_center_median()[:])
    if abs(c[0]) < 0.24: continue
    fa_, hd_ = JW['L' if c[0] > 0 else 'R']
    d = (hd_ - fa_) / np.linalg.norm(hd_ - fa_); t = (c - fa_) @ d; foot = fa_ + d * t; r = c - foot
    if np.linalg.norm(c - hd_) < 0.21 and np.dot(np.array(f.normal[:]), r) > 0:
        sel.add(f); nc += 1
print('LINING cuff faces', nc)
sel = list(sel)
vn = {}
for f in sel:
    for v in f.verts: vn.setdefault(v, Vector()); vn[v] += f.normal * f.calc_area()
d = bmesh.ops.duplicate(bm, geom=sel)
vmap = d['vert_map']; newf = [x for x in d['geom'] if isinstance(x, bmesh.types.BMFace)]
for v, n_ in vn.items():
    nv = vmap.get(v)
    if nv is not None and n_.length > 1e-12: nv.co = v.co - n_.normalized() * 0.003
bmesh.ops.reverse_faces(bm, faces=newf)
for f in newf:
    f[lin] = 1
    k = {0: 'limbs', 1: 'torso', 2: 'head'}[f[mat]]
    for l in f.loops: l[uvp_].uv = (DT[k]['u'], 1 - DT[k]['v'])
print('LINING new faces', len(newf))
# hose under the skirt: the Meshy hose tops stood 1.2 cm out through the skirt at the hips already at rest (skirt gate, r2). Under the
# hem the hose narrows toward each leg's axis (hip -> knee), up to 22 % by z = 0; the part below the hem is untouched
HIP, KNEE = np.array([0.09, 0.0, 0.0]), np.array([0.15, 0.02, -0.38])
moved = 0
for v in {v for f in bm.faces if f[part] == 5 for v in f.verts}:
    z = v.co.z
    t = np.clip((z + 0.075) / 0.07, 0, 1); k = 0.22 * t * t * (3 - 2 * t)
    if k <= 0: continue
    p = np.array(v.co[:]); qs = []
    for sx in ((1.0, -1.0) if abs(p[0]) < 1e-4 else (np.sign(p[0]),)):      # the crotch seam (x = 0): both legs' pull, averaged, stays on x = 0
        a, b = HIP * [sx, 1, 1], KNEE * [sx, 1, 1]
        u = (b - a) / np.linalg.norm(b - a); foot = a + u * ((p - a) @ u)
        qs.append(foot + (p - foot) * (1 - k))
    v.co = Vector(np.mean(qs, 0)); moved += 1
print('LINING hose verts narrowed', moved)
# cap: the skirt's cross-section 2.5 cm under its top, 1.2 cm inside it
sk = np.array([v.co[:] for f in bm.faces if f[part] == 7 and not f[lin] for v in f.verts])
ztop = sk[:, 2].max(); zc = 0.11   # PeasantM2: the skirt top is uneven (front 0.19); 0.11 is a full ring under the belt
band = sk[np.abs(sk[:, 2] - zc) < 0.012]
cx, cy = 0.0, 0.5 * (band[:, 1].min() + band[:, 1].max())
N = 32; ring = []
sp = body.vertex_groups['Bip01 Spine'].index
for k in range(N):
    a = 2 * np.pi * k / N; dvec = np.array([np.cos(a), np.sin(a)])
    proj = (band[:, :2] - [cx, cy]) @ dvec
    ang = np.arctan2(band[:, 1] - cy, band[:, 0] - cx)
    near = np.abs(((ang - a + np.pi) % (2 * np.pi)) - np.pi) < 0.3
    r = (proj[near].max() if near.any() else proj.max()) - 0.012
    v = bm.verts.new(Vector((cx + r * dvec[0], cy + r * dvec[1], zc))); v[dv][sp] = 1.0; ring.append(v)
c = bm.verts.new(Vector((cx, cy, zc))); c[dv][sp] = 1.0
cap = []
for k in range(N):
    f = bm.faces.new((ring[k], c, ring[(k + 1) % N]))
    if f.normal.z > 0: f.normal_flip()          # faces down, toward the feet
    f[part] = 7; f[mat] = 1; f[lin] = 2; f.smooth = False
    for l in f.loops: l[uvp_].uv = (DT['torso']['u'], 1 - DT['torso']['v'])
    cap.append(f)
print('CAP z', round(zc, 3), 'centre y', round(cy, 3), 'faces', len(cap))
hair = [f for f in bm.faces if f[part] == 21 and not f[lin]]
vn = {}
for f in hair:
    for v in f.verts: vn.setdefault(v, Vector()); vn[v] += f.normal * f.calc_area()
d = bmesh.ops.duplicate(bm, geom=hair)
vmap = d['vert_map']; newf = [x for x in d['geom'] if isinstance(x, bmesh.types.BMFace)]
for v, n_ in vn.items():
    nv = vmap.get(v)
    if nv is not None and n_.length > 1e-12: nv.co = v.co - n_.normalized() * 0.002
bmesh.ops.reverse_faces(bm, faces=newf)
for f in newf: f[lin] = 3
print('LINING hair faces', len(newf))
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FINISH', len(me.polygons), 'tris')
