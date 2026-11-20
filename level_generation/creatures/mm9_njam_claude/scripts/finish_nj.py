"""After the paint (UVs frozen; nothing here moves painted faces or their UVs). From mm9_highwayman_claude/scripts/finish_hw.py's lining:
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
fs = {f for f in bm.faces if f[part] == 1 and abs(f.calc_center_median().x) > 0.36 and f.calc_center_median().z < 0.26}
cur = set()
for e in bm.edges:
    if e.is_boundary and e.link_faces and e.link_faces[0] in fs: cur.update(e.verts)
print('LINING cuff rim verts', len(cur))
for _ in range(2):
    nf = {f for v in cur for f in v.link_faces if f in fs}
    sel |= nf
    cur = {v for f in nf for v in f.verts}
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
HIP, KNEE = np.array([0.09, 0.0, 0.0]), np.array([0.135, 0.045, -0.39])
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
ztop = sk[:, 2].max(); zc = ztop - 0.045
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
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FINISH', len(me.polygons), 'tris')
