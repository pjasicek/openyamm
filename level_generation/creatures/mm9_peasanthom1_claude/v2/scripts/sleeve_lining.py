"""Sleeve lining and forearm inside the sleeve (2026-10-30, user on Yrsa: "hands - cut off, floating?").

Args (Blender): <master blend> <out blend> <report json> <bone prefix: FHP | Bip01> <head set base colour png>
                body_png=<body base colour png> orm_png=<body ORM png> [key=value: offset 0.003, end 0.06, radius_end 0.03, sides LR,
                bones Forearm,UpperArm,Hand, lining 1, forearm 1, near 0 (m from the wrist), dark_pct 25]

Why: the Meshy sleeves are single-sided cloth (back faces culled), and graft_hands.py ends the MPFB hand in a short open
stub at the cuff, so a view into a wide sleeve showed the background through the sleeve and a hand cut off at the
wrist.
- Lining (the mm6_cle_claude skirt_shell.py add_inside technique, see the "Meshy cloth lining" note): the sleeve
  faces (the loose part holding most of them; body faces whose every vertex is weighted mostly to that side's `bones`)
  that face away from the arm are duplicated `offset` behind themselves along the area-weighted vertex normal, flipped,
  with their twins' weights (the deform layer is duplicated), so the inside follows the outside exactly under any
  pose. Sleeve faces that already face the arm (Meshy's own inner layer, with an arm painted on it and pale slivers at
  the cuff) keep their place and take the lining's texel, one dark texel of the sleeve's own paint (the face whose centre
  texel is the roughest among the darkest 25 % of the sleeve faces). Open edges (the cuff) are closed by a rim strip
  between each boundary edge and its twin, facing out of the sleeve, on the same dark texel, so no slot between
  the two layers shows the background.
- Forearm: the hand stub's open ring (the hand faces' boundary loop nearest the wrist) continues up the sleeve along
  a straight centre line to `end` from the elbow on the forearm axis, in four rings that go from the stub's own tilted
  shape to true circles of radius up to `radius_end`, and is capped. Weights go from the ring's own to the forearm
  alone at half the length. New faces are hand faces (head + hands material); each column repeats the rim texels
  of the stub above it, so the skin continues without a colour step.
Geometry elsewhere, weights and textures are unchanged; among existing faces only the sleeve's inner layer changes
its UVs. Run after the last vertex move.
"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP, TOK, HEADPNG = argv[:5]
opt = dict(a.split('=', 1) for a in argv[5:])
OFFSET = float(opt.get('offset', 0.003))
END = float(opt.get('end', 0.06))
R_END = float(opt.get('radius_end', 0.03))
SIDES = opt.get('sides', 'LR')
BONES = opt.get('bones', 'Forearm,UpperArm,Hand').split(',')
LINING = opt.get('lining', '1') == '1'
FOREARM = opt.get('forearm', '1') == '1'
NEAR = float(opt.get('near', 0))        # lining only within this distance of the wrist (0: the whole sleeve)
DARK_PCT = float(opt.get('dark_pct', 25))
TS = (0.12, 0.3, 0.6, 1.0)                # ring positions along the new forearm

bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
M, Mi = body.matrix_world, body.matrix_world.inverted()
names = [g.name for g in body.vertex_groups]
gi = {n: i for i, n in enumerate(names)}


def smooth(x):
    return x * x * (3 - 2 * x)


def pixels(path):
    img = bpy.data.images.load(path, check_existing=True)
    px = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(img.size[1], img.size[0], 4)[..., :3]


bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
dl = bm.verts.layers.deform.active
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
uvb, uvh = bm.loops.layers.uv['UVMap'], bm.loops.layers.uv['HeadUV']
comp = {}
cid = 0
for v in bm.verts:
    if v in comp:
        continue
    st = [v]; comp[v] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in comp:
                comp[y] = cid; st.append(y)
    cid += 1


def dominant(v):
    w = v[dl]
    return names[max(w.items(), key=lambda kv: kv[1])[0]] if len(w) else ''


def centre_uv(f, layer):
    return sum((Vector(tuple(l[layer].uv)) for l in f.loops), Vector((0, 0))) / len(f.loops)


def texel(px, uv):
    H, W = px.shape[:2]
    return px[min(H - 1, max(0, int(uv.y * H))), min(W - 1, max(0, int(uv.x * W)))]


BODY_PX = pixels(opt['body_png'])
ORM_PX = pixels(opt['orm_png'])
HEAD_PX = pixels(HEADPNG)
report = {}
for S in SIDES:
    bones = {f'{TOK} {S} {b}' for b in BONES}
    elbow = rig.matrix_world @ rig.data.bones[f'{TOK} {S} Forearm'].head_local
    wrist = rig.matrix_world @ rig.data.bones[f'{TOK} {S} Hand'].head_local
    axis = (wrist - elbow).normalized()
    # ---- lining
    cand = [f for f in bm.faces if not f[lh] and not f[lk] and all(dominant(v) in bones for v in f.verts)]
    part = np.bincount([comp[f.verts[0]] for f in cand]).argmax()      # the garment the sleeve belongs to
    sleeve = [f for f in cand if comp[f.verts[0]] == part]
    lum = np.array([texel(BODY_PX, centre_uv(f, uvb)) @ np.array([0.299, 0.587, 0.114]) for f in sleeve])
    order = np.argsort(lum)[:max(1, int(len(lum) * DARK_PCT / 100))]
    # the roughest of the dark faces: a smooth texel shines grey inside the sleeve in a PBR viewer
    dark_face = sleeve[int(max(order, key=lambda i: texel(ORM_PX, centre_uv(sleeve[i], uvb))[1]))]
    dark_uv = tuple(centre_uv(dark_face, uvb))
    shoulder = rig.matrix_world @ rig.data.bones[f'{TOK} {S} UpperArm'].head_local
    tip = wrist + axis * 0.05

    def radial(p):
        """from the arm's centre line (shoulder - elbow - wrist) to a point"""
        best = None
        for x, y in ((shoulder, elbow), (elbow, tip)):
            d = y - x
            t = min(1.0, max(0.0, (p - x).dot(d) / d.dot(d)))
            r = p - (x + d * t)
            if best is None or r.length < best.length:
                best = r
        return best

    inner = [f for f in sleeve if (M.to_3x3() @ f.normal).normalized().dot(radial(M @ f.calc_center_median())
                                                                           .normalized()) < -0.2]
    iset = set(inner)
    outer = [f for f in sleeve if f not in iset]
    if NEAR:
        outer = [f for f in outer if ((M @ f.calc_center_median()) - wrist).length < NEAR]
        inner = [f for f in inner if ((M @ f.calc_center_median()) - wrist).length < NEAR]
    if not LINING:
        outer, inner = [], []
    for f in inner:              # Meshy's own inner layer (a painted arm, pale slivers at the cuff): the same dark cloth
        for l in f.loops:
            l[uvb].uv = dark_uv
    normal = {}
    for f in outer:
        for v in f.verts:
            normal[v] = normal.get(v, Vector()) + f.normal * f.calc_area()
    out = bmesh.ops.duplicate(bm, geom=outer) if outer else {'vert_map': {}, 'geom': []}
    vmap = out['vert_map']
    for v, n in normal.items():
        vmap[v].co = Mi @ ((M @ v.co) - (M.to_3x3() @ n).normalized() * OFFSET)
    lining = [g for g in out['geom'] if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.reverse_faces(bm, faces=lining)
    for f in lining:
        for l in f.loops:
            l[uvb].uv = dark_uv; l[uvh].uv = dark_uv
    # rim between the sleeve's open edges and their twins
    oset = set(outer)
    rim = []
    for e in list(bm.edges):
        if not e.is_boundary or e.link_faces[0] not in oset:
            continue
        f0 = e.link_faces[0]
        a, b = e.verts
        a2, b2 = vmap[a], vmap[b]
        for tri in ((a, b, b2), (a, b2, a2)):
            f = bm.faces.new(tri)
            f[lh] = 0; f[lk] = 0; f.material_index = f0.material_index; f.smooth = f0.smooth
            f.normal_update()
            # face out of the sleeve: away from the owning face's centre
            if f.normal.dot(f.calc_center_median() - f0.calc_center_median()) < 0:
                f.normal_flip()
            for l in f.loops:
                l[uvb].uv = dark_uv; l[uvh].uv = dark_uv
            rim.append(f)
    report[S] = {'sleeve_faces': len(sleeve), 'inner_faces_darkened': len(inner), 'lining_faces': len(lining),
                 'rim_faces': len(rim), 'dark_rgb': [round(float(x), 3) for x in texel(BODY_PX, Vector(dark_uv))]}
    if not FOREARM:
        continue
    # ---- forearm inside the sleeve: extrude the hand stub's open ring
    wrist_l = Mi @ wrist
    hand_edges = [e for e in bm.edges if e.is_boundary and e.link_faces[0][lk]]
    loops, seen = [], set()
    for e in hand_edges:
        if e in seen:
            continue
        lp, st = [], [e]
        while st:
            x = st.pop()
            if x in seen:
                continue
            seen.add(x); lp.append(x)
            for v in x.verts:
                st += [y for y in v.link_edges if y.is_boundary and y.link_faces[0][lk] and y not in seen]
        loops.append(lp)
    ring_edges = min(loops, key=lambda lp: (sum((v.co for x in lp for v in x.verts), Vector())
                                            / (2 * len(lp)) - wrist_l).length)
    # ordered ring
    vs = [ring_edges[0].verts[0]]
    left = set(ring_edges)
    while left:
        nxt = next((x for x in left if vs[-1] in x.verts), None)
        if nxt is None:
            break
        left.discard(nxt)
        o = nxt.other_vert(vs[-1])
        if o is vs[0]:
            break
        vs.append(o)
    c0 = sum((M @ v.co for v in vs), Vector()) / len(vs)
    r0 = float(np.mean([((M @ v.co) - c0).length for v in vs]))
    s0 = (c0 - elbow).dot(axis)
    rim_faces = {f for v in vs for f in v.link_faces if f[lk]}
    cols = np.array([texel(HEAD_PX, centre_uv(f, uvh)) for f in rim_faces])
    med = np.median(cols, 0)
    skin_face = min(rim_faces, key=lambda f: float(np.linalg.norm(texel(HEAD_PX, centre_uv(f, uvh)) - med)))
    skin_uv = tuple(centre_uv(skin_face, uvh))
    fa = gi[f'{TOK} {S} Forearm']
    # centre line from the stub to `end` on the forearm axis; rings go from the stub's own (tilted) shape to true circles
    c_end = elbow + axis * END
    path = c_end - c0
    d_axis = path.normalized()
    U = d_axis.orthogonal().normalized()
    V = d_axis.cross(U)
    off = [(M @ v.co) - c0 for v in vs]
    theta = [math.atan2(o.dot(V), o.dot(U)) for o in off]
    rings = [vs]
    for t in TS:
        c = c0 + path * t
        r = r0 + (R_END - r0) * smooth(t)
        shape = smooth(min(1.0, t / 0.3))
        tw = smooth(min(1.0, t / 0.5))
        ring = []
        for v, o, th in zip(vs, off, theta):
            p = c + o * (1 - shape) + (U * math.cos(th) + V * math.sin(th)) * r * shape
            nv = bm.verts.new(Mi @ p)
            w = {g: wt * (1 - tw) for g, wt in v[dl].items() if not names[g].startswith('MP_')}
            w[fa] = w.get(fa, 0.0) + tw
            tot = sum(w.values())
            for g, wt in w.items():
                nv[dl][g] = wt / tot
            ring.append(nv)
        rings.append(ring)
    n = len(vs)
    # skin: every column of the forearm repeats the stub's rim texels (taken 30 % into the rim face, off the island edge)
    col_uv = []
    for i in range(n):
        e = bm.edges.get((vs[i], vs[(i + 1) % n]))
        f = next(x for x in e.link_faces if x[lk])
        c = centre_uv(f, uvh)
        uv = {l.vert: Vector(tuple(l[uvh].uv)).lerp(c, 0.3) for l in f.loops}
        col_uv.append((tuple(uv[vs[i]]), tuple(uv[vs[(i + 1) % n]])))
    new = []
    tmpl = skin_face
    for ra, rb in zip(rings[:-1], rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            for tri in ((ra[i], rb[i], rb[j]), (ra[i], rb[j], ra[j])):
                new.append((bm.faces.new(tri), i))
    if opt.get('cap', '1') == '1':                # cap=0: an open tube end, hidden in the sleeve (closed tubes invert in the low shadow LODs)
        cap_c = bm.verts.new(Mi @ c_end)
        for g, wt in rings[-1][0][dl].items():
            cap_c[dl][g] = wt
        for i in range(n):
            new.append((bm.faces.new((rings[-1][i], rings[-1][(i + 1) % n], cap_c)), None))
    # orientation: away from the centre line (cap: towards the elbow)
    columns = {}
    for ring in rings:
        columns.update({v: k for k, v in enumerate(ring)})
    for f, i in new:
        f.normal_update()
        cen = M @ f.calc_center_median()
        h = max(0.0, min(1.0, (cen - c0).dot(path) / path.dot(path)))
        rad = cen - (c0 + path * h)
        want = rad if i is not None else d_axis
        if (M.to_3x3() @ f.normal).dot(want) < 0:
            f.normal_flip()
        for l in f.loops:
            if i is None:
                uv = skin_uv
            else:
                uv = col_uv[i][0] if columns[l.vert] == i else col_uv[i][1]
            l[uvh].uv = uv; l[uvb].uv = uv
        f[lk] = 1; f[lh] = 0; f.material_index = tmpl.material_index; f.smooth = tmpl.smooth
    report[S].update(stub_ring_vertices=len(vs), stub_radius=round(r0, 4), stub_along_forearm=round(s0, 4),
                     forearm_length=round((wrist - elbow).length, 4), extension_end=END, forearm_faces=len(new))
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('SLEEVE_LINING', json.dumps(report))
json.dump(report, open(REP, 'w'), indent=1)
