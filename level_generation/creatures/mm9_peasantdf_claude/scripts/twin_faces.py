"""Back-side twins for the single-sided open shells of the shared body (see-through gate v1, 2026-11-02: the game culls
back faces, so through the gap between face and hair, under the hair, along the apron's side edge, through the wrist
rings and into the boot tops the view met only back faces = background).

Each selected face is duplicated `offset` behind itself along the area-weighted vertex normal, flipped, with its own
UVs (both layers), face attributes and weights: the inside of the hair shows hair, the apron's back shows apron, the
inside of a wrist ring or a boot shows that garment. Selections (all on the rest pose):
  hair   - the hair/hood loose part (the largest loose part above 1.0 m apart from the head shell), offset 2 mm;
  apron  - body faces of the front skirt (Blender y < -0.02, z -0.36..-0.05) whose normal ray (backwards) meets other
           body cloth within 3 cm (the apron layer lying on the skirt), offset 1 mm;
  wrist  - body faces (no head/hand) within 7 cm of each forearm's cut ring (s -0.10..-0.025 along forearm -> hand),
           offset 2 mm;
  boots  - faces of the two boot loose parts within 5 cm below their top rim, offset 2 mm;
  skirt  - (v2, default instead of apron) every body face 0.42..0.02 m below the root: skirt and apron, offset 1.5 mm;
  legs   - (v2) the stocking pieces inside the skirt, offset 2 mm;
  sleeves- (v2) body faces mostly weighted to an upper arm (the puffed sleeves), offset 2 mm.
Twin vertices are kept behind any surface their offset meets within 1 cm (at most 40 % of that distance). Twin faces get
the face attribute `twin` = 1 (the shadow meshes and the arm/hand gate's inside test may leave them out).
Geometry is added only: existing faces, UVs, weights and attributes are unchanged, so the paid paints stay valid.
Args (Blender): <in blend> <out blend> [sets hair,apron,wrist,boots]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
SETS = (a[2] if len(a) > 2 else 'hair,skirt,legs,sleeves,wrist,boots').split(',')
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; M = body.matrix_world; Mi = M.inverted()
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lh = bm.faces.layers.int.get('hand'); lk = bm.faces.layers.int.get('head')
lt = bm.faces.layers.int.get('twin') or bm.faces.layers.int.new('twin')
dl = bm.verts.layers.deform.active
W = lambda v: M @ v.co
# loose parts
comp = {}; parts = []
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = len(parts); cur = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            o = e.other_vert(x)
            if o not in comp: comp[o] = len(parts); st.append(o); cur.append(o)
    parts.append(cur)
bvh = BVHTree.FromBMesh(bm)
sel = {}
rep = {}
if 'hair' in SETS:
    big = max(range(len(parts)), key=lambda i: len(parts[i]))
    cand = [i for i in range(len(parts)) if i != big and len(parts[i]) > 200
            and np.mean([W(v).z for v in parts[i]]) > 0.38]
    hair = max(cand, key=lambda i: len(parts[i]))
    fs = {f for v in parts[hair] for f in v.link_faces}
    for f in fs: sel[f] = 0.002
    rep['hair'] = len(fs)
if 'apron' in SETS:
    n = 0
    for f in bm.faces:
        if (lk and f[lk]) or (lh and f[lh]): continue
        c = M @ f.calc_center_median(); nw = (M.to_3x3() @ f.normal).normalized()
        if not (c.y < -0.02 and -0.36 < c.z < -0.05): continue
        hit = bvh.ray_cast(Mi @ (c - nw * 0.002), Mi.to_3x3() @ -nw, 0.03)
        if hit[0] is not None:
            sel[f] = 0.001; n += 1
    rep['apron'] = n
if 'wrist' in SETS:
    n = 0
    for side in 'LR':
        a0 = rig.matrix_world @ rig.data.bones[f'Bip01 {side} Forearm'].head_local
        a1 = rig.matrix_world @ rig.data.bones[f'Bip01 {side} Hand'].head_local
        ax = (a1 - a0).normalized()
        for f in bm.faces:
            if (lk and f[lk]) or (lh and f[lh]): continue
            c = M @ f.calc_center_median(); s = (c - a1).dot(ax); r = ((c - a1) - ax * s).length
            if -0.10 < s < -0.025 and r < 0.06:
                sel[f] = 0.002; n += 1
    rep['wrist'] = n
if 'skirt' in SETS:          # v2: the whole skirt and apron (the apron's flared side edge and a flipped face mid-apron)
    n = 0
    for f in bm.faces:
        if (lk and f[lk]) or (lh and f[lh]): continue
        if -0.42 < (M @ f.calc_center_median()).z < -0.02:
            sel[f] = 0.0015; n += 1
    rep['skirt'] = n
if 'legs' in SETS:           # v2: the stocking pieces inside the skirt (their tops show when a leg swings back)
    n = 0
    for i in range(len(parts)):
        zs = [W(v).z for v in parts[i]]
        if 50 < len(parts[i]) < 300 and -0.48 < np.mean(zs) < -0.33:
            for f in {f for v in parts[i] for f in v.link_faces}:
                sel[f] = 0.002; n += 1
    rep['legs'] = n
if 'sleeves' in SETS:        # v2: the puffed sleeves (faces mostly weighted to an upper arm), seen into at the elbow end
    n = 0
    gi = {g.index for g in body.vertex_groups if 'UpperArm' in g.name}
    for f in bm.faces:
        if (lk and f[lk]) or (lh and f[lh]): continue
        w = [sum(wt for k, wt in v[dl].items() if k in gi) for v in f.verts]
        if np.mean(w) > 0.5:
            sel[f] = 0.002; n += 1
    rep['sleeves'] = n
if 'boots' in SETS:
    n = 0
    boots = [i for i in range(len(parts)) if 100 < len(parts[i]) < 400 and np.mean([W(v).z for v in parts[i]]) < -0.45]
    for i in boots:
        top = max(W(v).z for v in parts[i])
        for f in {f for v in parts[i] for f in v.link_faces}:
            if (M @ f.calc_center_median()).z > top - 0.05:
                sel[f] = 0.002; n += 1
    rep['boots'] = n
faces = [f for f in sel if not f[lt]]
vs = {v for f in faces for v in f.verts}
nrm = {}
for v in vs:
    acc = Vector()
    for f in v.link_faces:
        if f in sel: acc += f.normal * f.calc_area()
    nrm[v] = acc.normalized() if acc.length > 1e-12 else v.normal
newv = {}
for v in vs:
    off = max(sel[f] for f in v.link_faces if f in sel)
    d = -nrm[v]
    hit = bvh.ray_cast(v.co + d * 1e-4, d, 0.01)
    if hit[0] is not None:
        off = min(off, 0.4 * (hit[0] - v.co).length)
    nv = bm.verts.new(v.co + d * off)
    if dl is not None:
        for k, w in v[dl].items(): nv[dl][k] = w
    newv[v] = nv
bm.verts.index_update()
uvls = list(bm.loops.layers.uv.values())
flayers = list(bm.faces.layers.int.values())
made = 0
for f in faces:
    loops = list(f.loops)[::-1]
    try:
        nf = bm.faces.new([newv[l.vert] for l in loops])
    except ValueError:
        continue
    nf.material_index = f.material_index; nf.smooth = f.smooth
    for L in flayers: nf[L] = f[L]
    nf[lt] = 1
    for nl, ol in zip(nf.loops, loops):
        for U in uvls: nl[U].uv = ol[U].uv
    made += 1
bm.normal_update()
bm.to_mesh(me); me.update()
rep['twin_faces'] = made
rep['tris'] = sum(len(p.vertices) - 2 for p in me.polygons)
print('TWINS', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
