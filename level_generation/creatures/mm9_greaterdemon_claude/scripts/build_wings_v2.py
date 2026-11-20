"""Wings v2 (2026-10-30 rework after the user's review): bony wing arms grown out of the back and a modelled bat
membrane, both on the MM9 wing chain, joined into the weighted 'Body'.

Args: <rig blend> <out blend> <report json> <config json>

v1 used MM9's own wing faces, but only the faces whose three vertices belong to wing bones: that dropped MM9's root
web (the faces that join the wing to the spine), so the wing floated 0.35 m behind the back, and its folded panels were
flat-shaded. v2 builds the wing on the same bones, so MM9's flap motion is unchanged:

- Bones (piece 4, body material, smooth): tubes along the chain joints (bone heads). The leading arm starts 8 cm inside
  the shoulder blade (the body surface point nearest the Xwing joint), runs through Xwing, XwingA, XwingB, XwingC
  and ends in a point at XwingD; two finger spars run from XwarmCpiv / XwarmBpiv to the trailing tips XwarmC / XwarmB;
  a thumb claw sits on the XwingB joint. Weights: each segment rigid to the bone whose head starts it, blended over a
  short zone at each joint; the root segment blends from the body's own weights at the anchor to Xwing, so the root
  bends with the back and never leaves it.
- Membrane (piece 3, own material): three Coons patches between the bones (outer: leading arm XwingA..XwingD and
  finger C; middle: forearm, finger C, finger B; inner: humerus, finger B, the hip tip XwarmA and a line along the back
  that is snapped onto the body surface and tucked 2 cm inside). Trailing edges between the tips are scalloped. Patch
  weights are the same Coons blend of the boundary weights, so the membrane edges move exactly with the bone tubes
  and the body line moves with the body. Solidified to a thin closed shell, smooth with sharp rims.
"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
RIG, OUT, REP, CFGF = argv
cfg = json.load(open(CFGF))
bpy.ops.wm.open_mainfile(filepath=RIG)
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
mw = body.matrix_world
# the body has groups only for the bones it is weighted to: add the wing bones (and any other rig bone) first, or
# the wing weights below would have nowhere to go
for b in arm.data.bones:
    if b.name not in body.vertex_groups:
        body.vertex_groups.new(name=b.name)
GN = [g.name for g in body.vertex_groups]
BI = {n: i for i, n in enumerate(GN)}
NV = len(me.vertices)
W = np.zeros((NV, len(GN)), np.float32)
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
me.calc_loop_triangles()
TRI = np.array([tuple(t.vertices) for t in me.loop_triangles])
# body BVH over the main shell only (piece 0), so spikes do not catch the anchors
piece = np.array([d.value for d in me.attributes['piece'].data])
TRI0 = TRI[(piece[TRI] == 0).all(1)]
bvh = BVHTree.FromPolygons([tuple(c) for c in CO], [tuple(t) for t in TRI0])


def bone_vec(name):
    return np.zeros(len(GN), np.float32) if name not in BI else np.eye(len(GN), dtype=np.float32)[BI[name]]


def body_at(p, inset):
    """Nearest body-surface point, pushed `inset` inside, and the body weights there (barycentric)."""
    loc, nrm, fi, _ = bvh.find_nearest(Vector(p))
    a, b, c = (CO[i] for i in TRI0[fi])
    v0, v1, v2 = b - a, c - a, np.array(loc) - a
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    l1 = (d11 * d20 - d01 * d21) / den if abs(den) > 1e-14 else 1 / 3
    l2 = (d00 * d21 - d01 * d20) / den if abs(den) > 1e-14 else 1 / 3
    bc = np.clip([1 - l1 - l2, l1, l2], 0, 1)
    bc /= bc.sum()
    w = sum(bc[k] * W[TRI0[fi][k]] for k in range(3))
    return np.array(loc) - np.array(nrm) * inset, w, np.array(nrm)


def resample(pts, n):
    """n+1 points at equal arclength along the polyline pts (k x 3)."""
    pts = np.asarray(pts, float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n + 1)
    return np.stack([np.interp(t, s, pts[:, k]) for k in range(3)], 1), t / s[-1], s


def smoothstep(e0, e1, x):
    x = np.clip((x - e0) / (e1 - e0), 0, 1)
    return x * x * (3 - 2 * x)


def chain_weights(joints, bones, svals, blend, base_w=None, root_blend=None):
    """Weights along a joint chain at arclength params svals (0..total): segment i rigid to bones[i], linear blend of
    +-blend around interior joints. base_w: weights of an extra first point (the body anchor) blended into bones[0]
    over the first segment (root_blend = (t0, t1) fractions of that segment)."""
    J = np.asarray(joints, float)
    sj = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(J, axis=0), axis=1))])
    out = []
    for s in svals:
        i = int(np.clip(np.searchsorted(sj, s, side='right') - 1, 0, len(bones) - 1))
        w = bone_vec(bones[i])
        # blend with the previous segment's bone near joint i
        if i > 0 and s - sj[i] < blend:
            f = 0.5 + 0.5 * (s - sj[i]) / blend
            w = f * w + (1 - f) * bone_vec(bones[i - 1])
        if i + 1 < len(bones) and sj[i + 1] - s < blend:
            f = 0.5 + 0.5 * (sj[i + 1] - s) / blend
            w = f * w + (1 - f) * bone_vec(bones[i + 1])
        if base_w is not None and i == 0:
            t = (s - sj[0]) / max(sj[1] - sj[0], 1e-9)
            k = smoothstep(root_blend[0], root_blend[1], t)
            w = k * w + (1 - k) * base_w
        out.append(w)
    return np.array(out)


rep = {}
bm = bmesh.new()
dl = bm.verts.layers.deform.verify()
pl = bm.verts.layers.int.new('piece')
al = bm.verts.layers.int.new('anchor')   # 1: attachment vertex (body line of the membrane, buried root of the arm)
SEG = cfg.get('segment', 0.12)


def add_vert(p, w, pc, anchor=0):
    v = bm.verts.new(Vector(p))
    v[al] = anchor
    w = np.clip(w, 0, None)
    order = np.argsort(-w)[:4]
    s = w[order].sum()
    for k in order:
        if w[k] > 1e-4 and s > 0:
            v[dl][int(k)] = float(w[k] / s)
    v[pl] = pc
    return v


def tube(path, radii, weights, sides, cap_start=True, point_end=True, root_k=None, root_bone=None):
    """Closed tube along path (k x 3) with radius per point and weight per point (ring vertices copy it). With root_k
    (per point, < 1 on the root segment): ring vertices there take k * root_bone + (1 - k) * the body weights at their
    own nearest body point, so the buried root follows the local body surface; k == 0 rings are anchors."""
    path = np.asarray(path, float)
    tang = np.gradient(path, axis=0)
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    ref = np.array([0, 0, 1.0]) if abs(tang[0][2]) < 0.9 else np.array([1.0, 0, 0])
    nrm = np.cross(tang[0], ref); nrm /= np.linalg.norm(nrm)
    rings = []
    last = len(path) - 1 if point_end else len(path)
    for k in range(len(path)):
        if k:
            # parallel transport of the frame
            nrm = nrm - tang[k] * (nrm @ tang[k]); nrm /= np.linalg.norm(nrm)
        bn = np.cross(tang[k], nrm)
        if k == last:
            rings.append([add_vert(path[k], weights[k], 4)])
            break
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides
            q = path[k] + radii[k] * (math.cos(a) * nrm + math.sin(a) * bn)
            if root_k is not None and root_k[k] < 1:
                sp, wb, sn = body_at(q, 0.0)
                inside = (q - sp) @ sn < -0.01
                ring.append(add_vert(q, root_k[k] * root_bone + (1 - root_k[k]) * wb, 4, int(root_k[k] < 1e-3 and inside)))
            else:
                ring.append(add_vert(q, weights[k], 4))
        rings.append(ring)
    faces = []
    for k in range(len(rings) - 1):
        r0, r1 = rings[k], rings[k + 1]
        for j in range(sides):
            if len(r1) == 1:
                faces.append(bm.faces.new((r0[j], r0[(j + 1) % sides], r1[0])))
            else:
                faces.append(bm.faces.new((r0[j], r0[(j + 1) % sides], r1[(j + 1) % sides], r1[j])))
    if cap_start:
        c = add_vert(path[0], weights[0] if root_k is None else body_at(path[0], 0.0)[1], 4, int(root_k is not None))
        r0 = rings[0]
        for j in range(sides):
            faces.append(bm.faces.new((r0[(j + 1) % sides], r0[j], c)))
    return faces


def densify(joints, step):
    """Polyline through joints with points every <= step (joints kept), plus the arclength of each point."""
    pts = [np.asarray(joints[0], float)]
    for a, b in zip(joints[:-1], joints[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        n = max(1, int(math.ceil(np.linalg.norm(b - a) / step)))
        for k in range(1, n + 1):
            pts.append(a + (b - a) * k / n)
    pts = np.array(pts)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    return pts, s


def joint_rings(joints, step, blend):
    """Tube path: dense points plus extra rings at +-blend around interior joints (so the bend has geometry)."""
    pts, s = densify(joints, step)
    J = np.asarray(joints, float)
    sj = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(J, axis=0), axis=1))])
    extra = [x for j in sj[1:-1] for x in (j - blend, j + blend)]
    S = np.unique(np.round(np.concatenate([s, extra]), 5))
    S = S[(S >= 0) & (S <= s[-1])]
    path = np.stack([np.interp(S, s, pts[:, k]) for k in range(3)], 1)
    return path, S, sj


H = lambda n: np.array(arm.matrix_world @ arm.data.bones[n].head_local)
mem_faces_all = []
for side in ('', '01'):
    sgn = 1 if side == '01' else -1
    b = lambda n: n + side
    W0, WA, WB, WC, WD = (H(b(n)) for n in ('Xwing', 'XwingA', 'XwingB', 'XwingC', 'XwingD'))
    CP, TC = H(b('XwarmCpiv')), H(b('XwarmC'))
    BP, TB = H(b('XwarmBpiv')), H(b('XwarmB'))
    TA = H(b('XwarmA'))
    # shoulder anchor: body surface nearest the wing joint
    S, wS, nS = body_at(W0, 0.0)
    S_in = S - nS * cfg['root_depth']
    # --- bone tubes
    blend = cfg['joint_blend']
    lead_j = [S_in, W0, WA, WB, WC, WD]
    lead_b = ['__body__', b('Xwing'), b('XwingA'), b('XwingB'), b('XwingC')]
    path, sv, sj = joint_rings(lead_j, cfg['ring_step'], blend)
    # the first segment (inside the body to the Xwing joint): body weights blended into Xwing
    wl = chain_weights(lead_j[1:], lead_b[1:], np.maximum(sv - sj[1], 0), blend)
    t0 = np.clip(sv / sj[1], 0, 1)
    k = smoothstep(cfg['root_blend'][0], cfg['root_blend'][1], t0)[:, None]
    wl = np.where((sv < sj[1])[:, None], k * bone_vec(b('Xwing')) + (1 - k) * wS, wl)
    rad = np.interp(sv, sj, cfg['lead_radii'])
    # knuckles: a little thicker at the interior wing joints
    for j in sj[2:-1]:
        rad *= 1 + cfg['knuckle'] * np.exp(-((sv - j) / 0.05) ** 2)
    rk = np.where(sv < sj[1], k[:, 0], 1.0)
    tube(path, rad, wl, cfg['lead_sides'], root_k=rk, root_bone=bone_vec(b('Xwing')))
    # finger spars start on the arm joints (XwarmCpiv / XwarmBpiv sit 10 cm off them), so the membrane loops close
    for base, tip, bn, parent in ((WA, TC, b('XwarmCpiv'), b('XwingA')), (W0, TB, b('XwarmBpiv'), b('Xwing'))):
        fj = [base, tip]
        fpath, fs, fsj = joint_rings(fj, cfg['ring_step'], blend)
        fw = np.array([bone_vec(bn) for _ in fs])
        kb = np.clip(fs / blend, 0, 1)[:, None] * 0.5 + 0.5
        fw = kb * fw + (1 - kb) * bone_vec(parent)
        tube(fpath, np.interp(fs, [0, fsj[-1]], cfg['finger_radii']), fw, cfg['finger_sides'])
    # thumb claw on the XwingB joint
    cd = np.array(cfg['claw_dir'], float) * np.array([sgn, 1, 1]); cd /= np.linalg.norm(cd)
    cpath = np.array([WB - cd * 0.02 + cd * cfg['claw_len'] * t + np.array([0, 0.02, 0]) * t * t for t in np.linspace(0, 1, 5)])
    tube(cpath, np.linspace(cfg['claw_radius'], 0, 5), np.array([bone_vec(b('XwingA'))] * 5), 6)
    # --- membrane curves (points and weights)
    def straight(p, q, wp, wq, n, scallop=0.0, inward=None):
        t = np.linspace(0, 1, n + 1)
        pts = p[None] + (q - p)[None] * t[:, None]
        if scallop:
            pts = pts + inward[None] * (scallop * np.linalg.norm(q - p) * np.sin(math.pi * t))[:, None]
        return pts, np.array([(1 - x) * wp + x * wq for x in t])

    def chain(joints, bones, n, parent=None):
        pts, tt, s = resample(joints, n)
        J = np.asarray(joints, float)
        sj = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(J, axis=0), axis=1))])
        w = chain_weights(joints, bones, tt * sj[-1], blend)
        if parent is not None:
            kb = np.clip(tt * sj[-1] / blend, 0, 1)[:, None] * 0.5 + 0.5
            w = kb * w + (1 - kb) * bone_vec(parent)
        return pts, w

    n_of = lambda length: max(2, int(math.ceil(length / SEG)))
    L = lambda *ps: sum(np.linalg.norm(np.asarray(q) - np.asarray(p)) for p, q in zip(ps[:-1], ps[1:]))
    nF = max(n_of(L(WA, TC)), n_of(L(W0, TB)), n_of(L(WC, WD)))
    # lower back line: from the hip tip to a body anchor, then up the back (snapped, tucked in) to the shoulder anchor
    low_t = np.array(cfg['low_anchor']) * np.array([sgn, 1, 1])
    Lp, wL, _ = body_at(low_t, cfg['inset'])
    S_t, wS_t, _ = body_at(S, cfg['inset'])
    # inner panel side D (TA -> L -> S): free part then the body line
    n_free = max(1, int(round(nF * L(TA, Lp) / (L(TA, Lp) + L(Lp, S_t)))))
    dp, dw = straight(TA, Lp, bone_vec(b('XwarmA')), wL, n_free)
    line = []
    for x in np.linspace(0, 1, nF - n_free + 1)[1:]:
        q, wq, _ = body_at(Lp + (S_t - Lp) * x, cfg['inset'])
        line.append((q, wq))
    # inner panel side A: the humerus from the tucked shoulder point to the wing joint, weighted as the root tube
    nA3 = n_of(max(L(S_t, W0), L(TB, TA)))
    ta = np.linspace(0, 1, nA3 + 1)
    pA = S_t[None] + (W0 - S_t)[None] * ta[:, None]
    t0 = np.clip(np.linalg.norm(pA - S_in, axis=1) / np.linalg.norm(W0 - S_in), 0, 1)
    kA = smoothstep(cfg['root_blend'][0], cfg['root_blend'][1], t0)[:, None]
    A3 = (pA, kA * bone_vec(b('Xwing')) + (1 - kA) * wS)
    line[-1] = (A3[0][0], A3[1][0])
    D3 = (np.vstack([dp] + [q[None] for q, _ in line]), np.vstack([dw] + [w[None] for _, w in line]))
    fB = chain([W0, TB], [b('XwarmBpiv')], nF, parent=b('Xwing'))
    fC = chain([WA, TC], [b('XwarmCpiv')], nF, parent=b('XwingA'))
    centroid = lambda *ps: np.mean(ps, 0)

    def inward(p, q, c):
        m = (p + q) / 2
        d = c - m
        e = (q - p) / np.linalg.norm(q - p)
        d = d - e * (d @ e)
        return d / np.linalg.norm(d)
    # panel 3 (inner): S -> W0 -> TB -> TA -> (L) -> S
    c3 = centroid(S_t, W0, TB, TA)
    C3 = straight(TB, TA, bone_vec(b('XwarmB')), bone_vec(b('XwarmA')), nA3, cfg['scallop'], inward(TB, TA, c3))
    # panel 2 (middle): W0 -> WA -> TC -> TB
    nA2 = n_of(max(L(W0, WA), L(TC, TB)))
    A2 = chain([W0, WA], [b('Xwing')], nA2)
    c2 = centroid(W0, WA, TC, TB)
    C2 = straight(TC, TB, bone_vec(b('XwarmC')), bone_vec(b('XwarmB')), nA2, cfg['scallop'], inward(TC, TB, c2))
    # panel 1 (outer): WA -> WB -> WC -> WD -> TC
    nA1 = n_of(max(L(WA, WB, WC), L(WD, TC)))
    A1 = chain([WA, WB, WC], [b('XwingA'), b('XwingB')], nA1)
    B1 = chain([WC, WD], [b('XwingC')], nF)
    c1 = centroid(WA, WC, WD, TC)
    C1 = straight(WD, TC, bone_vec(b('XwingD')), bone_vec(b('XwarmC')), nA1, cfg['scallop'], inward(WD, TC, c1))
    rev = lambda c: (c[0][::-1], c[1][::-1])

    def coons(A, B, C, D, anchor_side=False, anchor_upto=-1):
        """Sides in loop order P0->P1 (A), P1->P2 (B), P2->P3 (C), P3->P0 (D); len(A) == len(C), len(B) == len(D)."""
        c0, c1 = A, rev(C)
        d0, d1 = rev(D), B
        nu, nv = len(c0[0]) - 1, len(d0[0]) - 1
        assert len(c1[0]) - 1 == nu and len(d1[0]) - 1 == nv, (nu, len(c1[0]) - 1, nv, len(d1[0]) - 1)
        grid = {}
        for k in range(2):  # 0 positions, 1 weights
            P00, P10, P11, P01 = c0[k][0], c0[k][-1], c1[k][-1], c1[k][0]
            G = np.zeros((nu + 1, nv + 1) + c0[k].shape[1:])
            for i in range(nu + 1):
                u = i / nu
                for j in range(nv + 1):
                    v = j / nv
                    G[i, j] = ((1 - v) * c0[k][i] + v * c1[k][i] + (1 - u) * d0[k][j] + u * d1[k][j]
                               - ((1 - u) * (1 - v) * P00 + u * (1 - v) * P10 + u * v * P11 + (1 - u) * v * P01))
            grid[k] = G
        vs = [[add_vert(grid[0][i, j], grid[1][i, j], 3, int(anchor_side and i == 0 and j <= anchor_upto))
               for j in range(nv + 1)] for i in range(nu + 1)]
        fs = []
        for i in range(nu):
            for j in range(nv):
                fs.append(bm.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1])))
        return fs
    # D3 is the u = 0 side read backwards: j <= len(line) are its body-line points (S end first, then L)
    mem_faces_all += coons(A3, fB, C3, D3, anchor_side=True, anchor_upto=len(line))
    mem_faces_all += coons(A2, fC, C2, rev(fB))
    mem_faces_all += coons(A1, B1, C1, rev(fC))
    rep[f'side{side or "00"}'] = {'shoulder_anchor': np.round(S, 3).tolist(), 'low_anchor': np.round(Lp, 3).tolist(),
                                  'root_len': round(float(np.linalg.norm(W0 - S)), 3), 'nF': nF}
# weld the shared membrane curves
mem_verts = list({v for f in mem_faces_all for v in f.verts})
bmesh.ops.remove_doubles(bm, verts=mem_verts, dist=1e-5)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
# solidify the membrane only: copy it out, solidify with a modifier, and bring it back
mem = bpy.data.meshes.new('Membrane')
bmm = bm.copy()
bmesh.ops.delete(bmm, geom=[f for f in bmm.faces if f.verts[0][bmm.verts.layers.int['piece']] != 3], context='FACES')
bmesh.ops.delete(bmm, geom=[v for v in bmm.verts if not v.link_faces], context='VERTS')
bmesh.ops.triangulate(bmm, faces=bmm.faces[:], quad_method='BEAUTY')
bmm.to_mesh(mem); bmm.free()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.verts[0][pl] == 3], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bones_me = bpy.data.meshes.new('WingBones')
bm.to_mesh(bones_me); bm.free()
objs = []
for nm, data in (('Membrane', mem), ('WingBones', bones_me)):
    ob = bpy.data.objects.new(nm, data)
    bpy.context.scene.collection.objects.link(ob)
    for g in GN:
        ob.vertex_groups.new(name=g)
    objs.append(ob)
mob, bob = objs
for o in bpy.data.objects:
    o.select_set(o == mob)
bpy.context.view_layer.objects.active = mob
mod = mob.modifiers.new('solid', 'SOLIDIFY')
mod.thickness = cfg['thickness']; mod.offset = 0.0; mod.use_rim = True; mod.use_even_offset = True
bpy.ops.object.modifier_apply(modifier='solid')
bm2 = bmesh.new(); bm2.from_mesh(mob.data)
bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces[:])
bm2.to_mesh(mob.data); bm2.free()
# smooth shading, sharp edges only where the surface turns more than sharp_deg (the membrane rims)
for ob in objs:
    d = ob.data
    for p in d.polygons:
        p.use_smooth = True
    sharp = d.attributes.get('sharp_edge') or d.attributes.new('sharp_edge', 'BOOLEAN', 'EDGE')
    bm3 = bmesh.new(); bm3.from_mesh(d); bm3.edges.ensure_lookup_table()
    lim = math.radians(cfg['sharp_deg'])
    vals = [bool(len(e.link_faces) == 2 and e.calc_face_angle(0) > lim) for e in bm3.edges]
    bm3.free()
    sharp.data.foreach_set('value', vals)
rep['membrane_tris'] = len(mob.data.polygons)
rep['bone_tris'] = len(bob.data.polygons)
for ob in objs:
    for nm in ('side',):
        a = ob.data.attributes.new(nm, 'INT', 'POINT')
        a.data.foreach_set('value', [0 if abs(v.co.x) < 0.04 else (1 if v.co.x > 0 else -1) for v in ob.data.vertices])
    if 'bone' in body.data.color_attributes:
        col = ob.data.color_attributes.new('bone', 'FLOAT_COLOR', 'POINT')
        for i in range(len(ob.data.vertices)):
            col.data[i].color = (0.2, 0.2, 0.9, 1)
    ob.parent = arm
for o in bpy.data.objects:
    o.select_set(o in (body, mob, bob))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
rep['body_tris'] = sum(len(p.vertices) - 2 for p in body.data.polygons)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('WINGS ' + json.dumps(rep))
