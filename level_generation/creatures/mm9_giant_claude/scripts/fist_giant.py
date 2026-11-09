"""Right fist round the mallet's handle (from mm9_highwayman_claude/scripts/finish_hw.py, fist part; frames from the graft json).
MM9's handle axis stays fixed in the right hand's frame in every clip (turn <= 2.8 deg, offset <= 2.1 cm, measured), sliding along
itself only, so one grip pose holds everywhere. Fingers solved round the axis per finger, the thumb over them; a constant wrist
turn lines the knuckles up with MM9's axis; the mallet is placed turned back by it about the grip so it still points where MM9's
points, and Xbase / Xhammer move to the grip (rest rotations unchanged). Bone-local rotations go to work/hand_poses.json
(finger_keys.py). Writes the mallet (work/mallet.npz) into the body: vertex attribute part 20, face attribute mat 3, rigid on
Xhammer, UVs in PartUV. Args: <in blend> <out blend> <hand poses json>"""
import bpy, bmesh, sys, json, math, os
import numpy as np
from mathutils import Vector, Matrix
IN, OUT, POSES = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
Wm = np.array(rig.matrix_world)
H = lambda n: (Wm @ np.r_[np.array(rig.data.bones[n].head_local), 1])[:3]
BR = lambda n: Wm[:3, :3] @ np.array(rig.data.bones[n].matrix_local)[:3, :3]
unit = lambda v: v / np.linalg.norm(v)
def rot(ax, a): return np.array(Matrix.Rotation(a, 3, Vector(ax)))
GJ = json.load(open(os.path.join(HERE, 'work', 'hands_v1.json')))['joints']
MZ = np.load(os.path.join(HERE, 'work', 'mallet.npz'))
M = MZ['M']; AXm = unit(M[:3, 1]); Om = M[:3, 3]           # MM9's handle axis and Xhammer origin, Blender, bind
FN = {'Thumb': 1, 'Index': 2, 'Middle': 3, 'Ring': 4, 'Pinky': 5}
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
gid = {g.index: g.name for g in body.vertex_groups}
dom = {}
for v in me.vertices:
    if v.groups:
        g = max(v.groups, key=lambda x: x.weight); dom.setdefault(gid[g.group], []).append(v.index)
COV = np.array([tuple(v.co) for v in me.vertices])
R_GRIP = float(os.environ.get('R_GRIP', '0.032'))      # MM9's handle: 3.0-3.6 cm half width
KO = float(os.environ.get('KO', '0.02'))              # offsets: this hand is about 1.5 x the highwayman's
poses = dict(grip={}, relaxed={}, hand_offset={})
S = 'R'
J = {f: np.array([GJ[S][f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[S][f'finger{k}-3_tip']]) for f, k in FN.items()}
kn = unit(J['Index'][0] - J['Pinky'][0])
U0 = AXm if AXm @ kn > 0 else -AXm
v_ = np.cross(kn, U0); sn_ = np.linalg.norm(v_); th_ = math.atan2(sn_, kn @ U0)
RD = rot(v_ / sn_, th_) if sn_ > 1e-6 else np.eye(3)
BH = BR(f'Bip01 {S} Hand')
Dloc = Matrix((BH.T @ RD @ BH).tolist()).to_quaternion()
print('WRIST', S, 'turn deg', round(math.degrees(th_), 1))
def solve(S):
    J = {f: np.array([GJ[S][f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[S][f'finger{k}-3_tip']]) for f, k in FN.items()}
    kn = unit(J['Index'][0] - J['Pinky'][0])
    f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
    n0 = np.cross(kn, f0)
    if (np.mean([J[f][3] for f in FINGERS], 0) - np.mean([J[f][0] for f in FINGERS], 0)) @ n0 < 0: n0 = -n0
    U = kn
    half = {}
    for f in FN:
        ids = sum((dom.get(f'Bip01 {S} {f}{i}', []) for i in (1, 2, 3)), [])
        Q = COV[ids]; pts = J[f]
        d = np.min([np.linalg.norm(np.cross(Q - a_, unit(b_ - a_)), axis=1) for a_, b_ in zip(pts[:-1], pts[1:])], axis=0)
        half[f] = float(np.median(d))
    palm = COV[dom.get(f'Bip01 {S} Hand', [])]
    mcp = np.mean([J[f][0] for f in FINGERS], 0)
    # fixed fist curls about the knuckle line (each finger's own flexion), tried on the skinned mesh in Blender: for each, the fist's
    # free hole across the knuckle line is searched (outside the skin by the nearest face's normal, surrounded by the hand's
    # vertices with no angular gap over 100 deg); the curl whose hole is closest to the handle radius + 3 mm wins, the handle runs
    # through the hole's centre.
    from mathutils.bvhtree import BVHTree
    AX = U
    CF = json.load(open(os.path.join(HERE, 'scripts', 'graft_giant.json')))['sides'][S]
    npm = np.array(CF['n_dir']); npm = unit(npm - AX * (npm @ AX)); e2 = unit(np.cross(AX, npm))
    tip0 = J['Middle'][3]
    hp_ = np.array(CF['h_dir']); hp_ = unit(hp_ - AX * (hp_ @ AX))
    heel = J['Middle'][0] + npm * 0.05 - hp_ * 0.08
    dd = lambda a: np.linalg.norm(J['Middle'][0] + rot(AX, a) @ (tip0 - J['Middle'][0]) - heel)
    sg = 1.0 if dd(0.5) < dd(-0.5) else -1.0
    def chain_pose(f, deltas):
        res = {}; prev = np.eye(3)
        for i, D in enumerate(deltas):
            n = f'Bip01 {S} {f}{i + 1}'; Rb = BR(n)
            B = Rb.T @ prev.T @ D @ Rb
            q = Matrix(B.tolist()).to_quaternion()
            res[n] = [q.x, q.y, q.z, q.w]; prev = D
        return res
    hand_bones = [b.name for b in rig.data.bones if f' {S} ' in b.name and any(k in b.name for k in ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
    def posed_hole(grip):
        for pb in rig.pose.bones: pb.matrix_basis.identity(); pb.rotation_mode = 'QUATERNION'
        for n, q in grip.items(): rig.pose.bones[n].rotation_quaternion = (q[3], q[0], q[1], q[2])
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); em = ev.to_mesh()
        Pp = np.array([tuple(body.matrix_world @ v.co) for v in em.vertices])
        tris = [tuple(p.vertices) for p in em.polygons]
        bvh = BVHTree.FromPolygons([Vector(p) for p in Pp], tris)
        ev.to_mesh_clear()
        gi = {g.index: g.name for g in body.vertex_groups}
        hv = np.array([v.index for v in me.vertices if v.groups and gi[max(v.groups, key=lambda x: x.weight).group] in hand_bones])
        HP = Pp[hv]; cen = HP.mean(0)
        best = None
        for du in np.arange(-0.10, 0.101, 0.004):
            for dv in np.arange(-0.04, 0.141, 0.004):
                G = mcp + e2 * du + npm * dv
                loc, nor, _, dist = bvh.find_nearest(Vector(G))
                if loc is None or (G - np.array(loc)) @ np.array(nor) < 0: continue
                q = HP - G; al = q @ AX; sl = np.abs(al) < 0.04; q = q[sl] - np.outer(al[sl], AX)
                r = np.linalg.norm(q, axis=1); near = r < 0.10
                if near.sum() < 10: continue
                ang = np.sort(np.arctan2(q[near] @ npm, q[near] @ e2))
                gap = np.degrees(np.max(np.diff(np.r_[ang, ang[0] + 2 * np.pi])))
                if gap > 100: continue
                if best is None or dist > best[0]: best = (dist, G, gap, du, dv)
        for pb in rig.pose.bones: pb.matrix_basis.identity()
        bpy.context.view_layer.update()
        return best
    mcp = np.mean([J[f][0] for f in FINGERS], 0)
    CURLS = [(10, 70, 45), (20, 70, 45), (10, 80, 55), (20, 80, 55), (0, 75, 50), (30, 75, 50), (15, 65, 40), (25, 85, 60)]
    results = []
    for c in CURLS:
        grip = {}
        for f in FINGERS:
            k = {'Index': 0, 'Middle': 0, 'Ring': 5, 'Pinky': 10}[f]
            a1, a2, a3 = np.radians(np.array(c) + np.array([k, k, 0]))
            grip.update(chain_pose(f, [rot(AX, sg * a1), rot(AX, sg * (a1 + a2)), rot(AX, sg * (a1 + a2 + a3))]))
        h = posed_hole(grip)
        if h is None: print('CURL', c, 'no hole'); continue
        print('CURL', c, 'hole r cm', round(h[0] * 100, 2), 'gap', round(h[2], 1), 'du dv cm', round(h[3] * 100, 1), round(h[4] * 100, 1))
        results.append((abs(h[0] - (R_GRIP + 0.003)), c, grip, h))
    _, curl, grip, hole = min(results, key=lambda x: x[0])
    G = hole[1]; R_HOLE = hole[0]
    print('GRIP', S, 'curl', curl, 'hole r cm', round(R_HOLE * 100, 2), 'G', np.round(G, 3))
    R_SHAFT = 0.027
    def radial0(p):
        v = p - G; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)
    def fk_s(j, a1, a2, a3):
        p1 = j[0] + rot(AX, sg * a1) @ (j[1] - j[0]); p2 = p1 + rot(AX, sg * (a1 + a2)) @ (j[2] - j[1]); p3 = p2 + rot(AX, sg * (a1 + a2 + a3)) @ (j[3] - j[2])
        pts = np.array([j[0], p1, p2, p3]); return pts, np.array([a + (b_ - a) * t for a, b_ in zip(pts[1:-1], pts[2:]) for t in np.linspace(0, 1, 6)])
    opened = {}
    for f in FINGERS:
        k = {'Index': 0, 'Middle': 0, 'Ring': 5, 'Pinky': 10}[f]
        a1, a2, a3 = np.radians(np.array(curl) + np.array([k, k, 0])); j = J[f]
        for d3, d2 in [(d3, d2) for d2 in range(0, 31, 5) for d3 in range(0, 46, 5)]:
            b2, b3 = a2 - np.radians(d2), max(a3 - np.radians(d3), 0)
            _, smp = fk_s(j, a1, b2, b3)
            if radial0(smp).min() >= R_SHAFT + half[f] * 0.9 + 0.002: break
        opened[f] = (d2, d3)
        grip.update(chain_pose(f, [rot(AX, sg * a1), rot(AX, sg * (a1 + b2)), rot(AX, sg * (a1 + b2 + b3))]))
    print('CLEAR', S, 'distal opening deg (PIP, DIP)', opened)
    posed = {}
    for f in FINGERS:
        k = {'Index': 0, 'Middle': 0, 'Ring': 5, 'Pinky': 10}[f]
        a1, a2, a3 = np.radians(np.array(curl) + np.array([k, k, 0])); j = J[f]; a2 -= np.radians(opened[f][0]); a3 = max(a3 - np.radians(opened[f][1]), 0)
        p1 = j[0] + rot(AX, sg * a1) @ (j[1] - j[0]); p2 = p1 + rot(AX, sg * (a1 + a2)) @ (j[2] - j[1]); p3 = p2 + rot(AX, sg * (a1 + a2 + a3)) @ (j[3] - j[2])
        posed[f] = np.array([j[0], p1, p2, p3])
    def radial(p):
        v = p - G; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)
    def samples(pts):
        s = []
        for a, b in zip(pts[:-1], pts[1:]):
            for t in (0.25, 0.5, 0.75, 1.0): s.append(a + (b - a) * t)
        return np.array(s)
    t = J['Thumb']
    target = posed['Middle'][2] + unit(posed['Middle'][2] - G) * (half['Middle'] + half['Thumb']) * 0.8
    want = R_GRIP + half['Thumb'] + 0.005
    best = None
    for th in np.radians(np.arange(-180, 180, 6)):
        R1 = rot(f0, th)
        for ph in np.radians(np.arange(-180, 180, 6)):
            R2 = rot(AX, ph) @ R1
            for ps in np.radians(np.arange(-30, 76, 8)):
                R3 = rot(AX, ps) @ R2
                p1 = t[0] + R2 @ (t[1] - t[0]); p2 = p1 + R3 @ (t[2] - t[1]); p3 = p2 + R3 @ (t[3] - t[2])
                s_ = samples(np.array([t[0], p1, p2, p3])); r = radial(s_)
                c = np.linalg.norm(p3 - target) + 60 * np.maximum(want - r, 0).sum()
                if best is None or c < best[0]: best = (c, (R2, R3), (th, ph, ps), p3)
    print('THUMB', S, np.round(np.degrees(best[2]), 0), 'tip to target', round(float(np.linalg.norm(best[3] - target)), 3))
    grip.update(chain_pose('Thumb', [best[1][0], best[1][1], best[1][1]]))
    return dict(grip=grip, G=G, R_HOLE=R_HOLE, curl=curl, AX=AX, sg=sg, J=J, half=half)

def solve2(S):
    """Third pass (2026-11-01, user: "the hammer isn't properly held ... not in the palms"): the Lich King's grip (mm9_lichking_claude
    grip_frame.py / grip_keys.py) on our hands. The shaft's axis runs along the knuckle line; its point is searched over palm-side and
    finger-direction offsets so the shaft's surface lies on the palm (palm-side vertices of the hand at R + 3 mm) with the knuckles outside the
    finger wrap. Each finger then curls joint by joint about the axis: the knuckle angle by search, the middle and last joints each until the
    next joint (or the tip) reaches the wrap radius (R + the finger's half thickness), capped at 85 deg; then the posed mesh is checked and
    any finger whose vertices enter the shaft is re-solved with a larger wrap radius (pads on the surface, none inside). The thumb closes over
    the fingers from the opposite side."""
    from mathutils.bvhtree import BVHTree
    J = {f: np.array([GJ[S][f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[S][f'finger{k}-3_tip']]) for f, k in FN.items()}
    kn = unit(J['Index'][0] - J['Pinky'][0])
    f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
    CF = json.load(open(os.path.join(HERE, 'scripts', 'graft_giant.json')))['sides'][S]
    npm = np.array(CF['n_dir']); npm = unit(npm - kn * (npm @ kn) - f0 * (npm @ f0))
    AX = kn
    half = {}
    for f in FN:
        ids = sum((dom.get(f'Bip01 {S} {f}{i}', []) for i in (1, 2, 3)), [])
        Q = COV[ids]; pts = J[f]
        d = np.min([np.linalg.norm(np.cross(Q - a_, unit(b_ - a_)), axis=1) for a_, b_ in zip(pts[:-1], pts[1:])], axis=0)
        half[f] = float(np.median(d))
    mcp = np.mean([J[f][0] for f in FINGERS], 0)
    RS = R_SHAFT2
    hid = dom.get(f'Bip01 {S} Hand', [])
    HV = COV[hid]
    def adist(P_, G_):
        d_ = np.atleast_2d(P_) - G_; return np.linalg.norm(d_ - np.outer(d_ @ AX, AX), axis=1)
    # the palm's own frame: p wrist -> knuckles across the knuckle line, q out of the palm (the thumb's side). The fingers' rest direction
    # is 38 deg off the palm, so the first grip searches (in the fingers' frame) put the shaft under the fingers
    wr = np.array(GJ[S]['wrist']); pp = mcp - wr; pp = unit(pp - AX * (pp @ AX)); qq = np.cross(AX, pp)
    if (J['Thumb'][3] - mcp) @ qq < 0: qq = -qq
    tipM = J['Middle'][3]; j0m = J['Middle'][0]
    sg = 1.0 if adist(j0m + rot(AX, 0.3) @ (tipM - j0m), mcp + qq * 0.06)[0] < adist(j0m + rot(AX, -0.3) @ (tipM - j0m), mcp + qq * 0.06)[0] else -1.0
    FV = {f: [COV[dom.get(f'Bip01 {S} {f}{i}', [])] for i in (1, 2, 3)] for f in FN}
    def fkv(f, a1, a2, a3):
        j = J[f]; R1 = rot(AX, sg * a1); R2 = rot(AX, sg * (a1 + a2)); R3 = rot(AX, sg * (a1 + a2 + a3))
        p1 = j[0] + R1 @ (j[1] - j[0]); p2 = p1 + R2 @ (j[2] - j[1])
        V1, V2, V3 = FV[f]
        return (j[0] + (V1 - j[0]) @ R1.T, p1 + (V2 - j[1]) @ R2.T, p2 + (V3 - j[2]) @ R3.T), (j[0], p1, p2, p2 + R3 @ (j[3] - j[2]))
    # the distal half of each phalanx (its pad end): a phalanx is "on the shaft" when its pad end rests on the surface (2026-11-01 review:
    # a touch anywhere let a finger stand straight with only its base against the shaft)
    def distal_mask(f, k):
        j = J[f]; a_, b_ = j[k], j[k + 1]; sd = b_ - a_; L_ = np.linalg.norm(sd); sd = sd / L_
        return ((FV[f][k] - a_) @ sd) / L_ > 0.35
    FVD = {f: [distal_mask(f, k) for k in range(3)] for f in FN}
    WRAPW = float(os.environ.get('WRAPW', '0.01')); SPAN = float(os.environ.get('GRIP_SPAN', '0')); PADTOL = float(os.environ.get('PADTOL', '0.0015'))
    def solve_finger(f, G_, GAP):
        """knuckle angle by search; the middle and last joints each curl until that phalanx's skin reaches the shaft's surface + GAP (r21).
        Tried on 2026-11-01 and dropped: pad ends only, tightest curl, a wrap reward: on this hand (8 cm thick at the knuckles, joints near its
        back) each either put the curled fingers in a fist beside the shaft or bent the knuckles backwards; see README third pass"""
        bestf = None; tgt = RS + GAP; ths = np.radians(np.arange(0, 111, 2.0))
        for a1 in np.radians(np.arange(0, 131, 2.0)):
            m1 = adist(fkv(f, a1, 0, 0)[0][0], G_).min()
            if m1 < RS: continue
            a2 = ths[-1]
            for t in ths:
                if adist(fkv(f, a1, t, 0)[0][1], G_).min() <= tgt: a2 = t; break
            a3 = ths[-1]
            for t in ths[:46]:
                if adist(fkv(f, a1, a2, t)[0][2], G_).min() <= tgt: a3 = t; break
            Vs, Jp = fkv(f, a1, a2, a3); ms = [adist(v, G_).min() for v in Vs]
            cost = abs(ms[0] - tgt) + 10 * sum(max(RS - m, 0) for m in ms) + 0.5 * sum(max(m - tgt - 0.003, 0) for m in ms[1:]) + 0.002 * abs(a1)
            if bestf is None or cost < bestf[0]: bestf = (cost, a1, a2, a3, ms, Jp)
        return bestf
    def solve_finger_pad(f, G_, GAP):
        """The finger's final pose (2026-11-01, user: "his pinky is not holding the hammer on either hand"). solve_finger stops a joint
        as soon as ANY vertex of the next phalanx is within reach, and the base of that phalanx sits at the joint, which already touches
        after a big knuckle bend: the ring's and pinky's middle joints stayed at 0 deg and the fingers stood off the shaft. Here every
        phalanx's pad end (distal_mask) must rest on the surface. The curl is about the shaft's own axis, so the search is 2D in the
        plane across it and exhaustive: knuckle 0-100, middle 0-110, last 0-100 deg in 2 deg steps; cost = penetration (any vertex
        inside the shaft) + each pad's distance from the surface + GAP + a light preference for an even middle/last curl."""
        tgt = RS + GAP
        e1 = unit(np.cross(AX, [0.0, 0.0, 1.0]) if abs(AX[2]) < 0.9 else np.cross(AX, [1.0, 0.0, 0.0])); e2 = np.cross(AX, e1)
        P2 = lambda X: np.c_[(np.atleast_2d(X) - G_) @ e1, (np.atleast_2d(X) - G_) @ e2]
        j2 = P2(J[f]); V = [P2(FV[f][k]) for k in range(3)]; Dm = FVD[f]
        # joints may also OPEN up to 40 deg: the MPFB pinky rests curled with its middle joint 4.0 cm from the axis (skin inside the
        # shaft), so with closing angles only the one clear pose was a 76 deg knuckle bend that threw the finger past the shaft
        NEG = 20; O = 3 * NEG
        st = np.radians(2.0); A1 = np.arange(-NEG, 51); A2 = np.arange(-NEG, 56); A3 = np.arange(-NEG, 51)
        th = sg * st * np.arange(-O, 160)
        Rt = np.stack([np.stack([np.cos(th), -np.sin(th)], -1), np.stack([np.sin(th), np.cos(th)], -1)], -2)       # (160, 2, 2)
        rotv = lambda k, X, piv: np.einsum('aij,nj->ani', Rt, X - piv)                                           # (160, n, 2)
        RV1, RV2, RV3 = rotv(0, V[0], j2[0]), rotv(1, V[1], j2[1]), rotv(2, V[2], j2[2])
        Rj1 = Rt @ (j2[1] - j2[0]); Rj2 = Rt @ (j2[2] - j2[1])
        def mins(X, m):                                                         # min radius over all vertices and over the pad end
            r = np.linalg.norm(X, axis=-1); return r.min(-1), r[..., m].min(-1)
        p1 = j2[0] + Rj1[A1 + O]                                                # (n1, 2)
        all1, pad1 = mins(j2[0] + RV1[A1 + O], Dm[0])                          # (n1,)
        c2 = A1[:, None] + A2[None, :] + O                                     # (n1, n2) cumulative angle index
        X2 = p1[:, None, None, :] + RV2[c2]                                    # (n1, n2, v2, 2)
        all2, pad2 = mins(X2, Dm[1])
        p2 = p1[:, None, :] + Rj2[c2]                                          # (n1, n2, 2)
        opn = lambda a: np.maximum(-a, 0) * st                                 # opening past rest (rad)
        best = None
        for k1, i1 in enumerate(A1):
            c3 = i1 + A2[:, None] + A3[None, :] + O                            # (n2, n3)
            X3 = p2[k1][:, None, None, :] + RV3[c3]                            # (n2, n3, v3, 2)
            all3, pad3 = mins(X3, Dm[2])
            pen = np.maximum(RS + 0.0005 - all1[k1], 0) + np.maximum(RS + 0.0005 - all2[k1], 0)[:, None] + np.maximum(RS + 0.0005 - all3, 0)
            cost = (40 * pen + 0.5 * abs(pad1[k1] - tgt) + np.abs(pad2[k1] - tgt)[:, None] + np.abs(pad3 - tgt)
                    + 0.001 * np.abs(st * (A2[:, None] - A3[None, :])) + 0.0005 * st * abs(i1)
                    + 0.004 * (opn(i1) + opn(A2)[:, None] + opn(A3)[None, :]))
            k = np.unravel_index(np.argmin(cost), cost.shape)
            if best is None or cost[k] < best[0]:
                best = (float(cost[k]), st * i1, st * A2[k[0]], st * A3[k[1]], (float(pad1[k1]), float(pad2[k1][k[0]]), float(pad3[k])))
        print('PADSOLVE', S, f, 'curl deg', [int(round(np.degrees(x))) for x in best[1:4]], 'pad gaps over the surface mm',
              [round((x - RS) * 1000, 1) for x in best[4]], 'target', round(GAP * 1000, 1))
        return best
    # templates of a natural fist (one curl for the four fingers, ring and pinky a little more), posed on the skinned mesh; the shaft goes
    # where the hole between the palm and the finger pads fits it: every finger's pads and the palm within a few mm of its surface
    def chain_pose0(f, a1, a2, a3):
        res = {}; prev = np.eye(3)
        for i, D in enumerate([rot(AX, sg * a1), rot(AX, sg * (a1 + a2)), rot(AX, sg * (a1 + a2 + a3))]):
            n = f'Bip01 {S} {f}{i + 1}'; Rb = BR(n); B = Rb.T @ prev.T @ D @ Rb; q = Matrix(B.tolist()).to_quaternion()
            res[n] = [q.x, q.y, q.z, q.w]; prev = D
        return res
    def posed_mesh0(grip):
        for pb in rig.pose.bones: pb.matrix_basis.identity(); pb.rotation_mode = 'QUATERNION'
        for n, q in grip.items(): rig.pose.bones[n].rotation_quaternion = (q[3], q[0], q[1], q[2])
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); em = ev.to_mesh()
        Pp = np.array([tuple(body.matrix_world @ v.co) for v in em.vertices]); ev.to_mesh_clear()
        for pb in rig.pose.bones: pb.matrix_basis.identity()
        bpy.context.view_layer.update()
        return Pp
    FIDS = {f: sum((dom.get(f'Bip01 {S} {f}{i}', []) for i in (2, 3)), []) for f in FINGERS}
    gx_, gy_ = np.meshgrid(np.arange(-0.10, 0.08, 0.004), np.arange(0.0, 0.16, 0.004)); GRD = np.c_[gx_.ravel(), gy_.ravel()]
    res = []
    for c in ([] if os.environ.get('GRIP_MODE', 'palm') == 'palm' else [(a1, a2, a3) for a1 in (0, 10, 20, 30, 40, 50) for a2 in (30, 45, 60, 75, 90) for a3 in (20, 40, 60)]):
        grip0 = {}
        for f in FINGERS:
            k = {'Index': 0, 'Middle': 0, 'Ring': 4, 'Pinky': 8}[f]
            grip0.update(chain_pose0(f, *np.radians([c[0] + k, c[1] + k, c[2]])))
        Pp = posed_mesh0(grip0)
        def xs(ids):
            P_ = Pp[ids] - mcp; al = P_ @ AX; return np.c_[P_ @ pp, P_ @ qq], al
        Hx, Ha = xs(hid); Fx = {f: xs(FIDS[f]) for f in FINGERS}
        allx = np.concatenate([Hx] + [Fx[f][0] for f in FINGERS] + [xs(sum((dom.get(f'Bip01 {S} {f}1', []) for f in FINGERS), []))[0]])
        r_all = np.min(np.linalg.norm(GRD[:, None, :] - allx[None, ::2, :], axis=2), axis=1)
        cand = np.where(np.abs(r_all - (RS + 0.002)) < 0.004)[0]
        best_c = None
        for gi in cand:
            g2 = GRD[gi]
            dd_ = allx - g2; rr_ = np.linalg.norm(dd_, axis=1); nb_ = dd_[rr_ < RS + 0.035]
            if len(nb_) < 20: continue
            an_ = np.sort(np.arctan2(nb_[:, 1], nb_[:, 0])); gap_ = np.degrees(np.max(np.diff(np.r_[an_, an_[0] + 2 * np.pi])))
            if gap_ > float(os.environ.get('FIST_GAP', '130')): continue            # enclosed: palm and fingers round it, not all on one side
            ph = np.linalg.norm(Hx - g2, axis=1).min() - RS
            fm = [np.linalg.norm(Fx[f][0] - g2, axis=1).min() - RS for f in FINGERS]
            sc_ = abs(ph - 0.003) + sum(abs(x - 0.002) for x in fm) + 0.0001 * gap_
            if best_c is None or sc_ < best_c[0]: best_c = (sc_, g2, ph, fm, gap_)
        if best_c: res.append((best_c[0], c, best_c))
    res.sort(key=lambda r: r[0])
    for r_ in res[:8]: print('FIST2', S, 'curl', r_[1], 'gap', round(r_[2][4]), 'at', np.round(r_[2][1] * 100, 1), 'score', round(r_[0] * 100, 2), 'palm gap cm', round(r_[2][2] * 100, 2), 'finger gaps cm', [round(x * 100, 2) for x in r_[2][3]])
    tcurl = None
    if res: _, tcurl, bc = res[0]; G = mcp + pp * bc[1][0] + qq * bc[1][1]; db, do, pm = -bc[1][0], bc[1][1], bc[2] + RS
    if res: print('GRIP2', S, 'template', tcurl, 'shaft centre along palm / out of palm cm', round(bc[1][0] * 100, 1), round(bc[1][1] * 100, 1))
    PALMMODE = os.environ.get('GRIP_MODE', 'palm') == 'palm'
    if PALMMODE:
        # the shaft against the palm (palm skin at R + 3 mm), the fingers wrapping its far side: each finger's knuckle by search, its middle and
        # last joints each until that phalanx's skin reaches the shaft's surface + 2 mm (the hand is thick at the knuckles: a closed fist has no
        # room for a 3 cm shaft, so the fingers lie round its front and underside)
        res = []
        PMAX = float(os.environ.get('PALM_GAP', '0.008'))
        for db in np.arange(float(os.environ.get('DB_MIN', '-0.01')), float(os.environ.get('DB_MAX', '0.061')), 0.005):
            for do in np.arange(0.02, 0.08, 0.004):
                G_ = mcp - pp * db + qq * do; pm = adist(HV, G_).min()
                if pm < RS + 0.0005 or pm > RS + PMAX: continue
                sol = {f: solve_finger(f, G_, 0.002) for f in FINGERS}
                if any(v is None for v in sol.values()): continue
                # the fingers must go round the shaft, not curl beside it: the joints' and fingertips' spread round the axis, with the palm
                jp_ = np.array([v[5][k] for v in sol.values() for k in (1, 2, 3)] + [HV[np.argmin(adist(HV, G_))]]) - G_
                jp_ = jp_ - np.outer(jp_ @ AX, AX); e1_ = unit(jp_[-1]); e2_ = np.cross(AX, e1_)
                an_ = np.sort(np.degrees(np.arctan2(jp_ @ e2_, jp_ @ e1_))); span = 360 - np.max(np.diff(np.r_[an_, an_[0] + 360]))
                res.append((sum(v[0] for v in sol.values()) + 2 * abs(pm - RS - 0.003) + 0.002 * max(SPAN - span, 0), db, do, pm))
        res.sort(key=lambda r: r[0])
        _, db, do, pm = res[0]; G = mcp - pp * db + qq * do
        print('GRIP2', S, 'palm mode: back from the knuckles cm', round(db * 100, 1), 'out of the palm cm', round(do * 100, 1), 'palm to axis cm', round(pm * 100, 2))
    dist = lambda p_: float(adist(p_, G)[0])
    def segsamp(pts):
        return np.array([a + (b_ - a) * t for a, b_ in zip(pts[:-1], pts[1:]) for t in np.linspace(0, 1, 7)])

    def chain_pose(f, deltas):
        res = {}; prev = np.eye(3)
        for i, D in enumerate(deltas):
            n = f'Bip01 {S} {f}{i + 1}'; Rb = BR(n)
            B = Rb.T @ prev.T @ D @ Rb
            q = Matrix(B.tolist()).to_quaternion()
            res[n] = [q.x, q.y, q.z, q.w]; prev = D
        return res
    def posed_mesh(grip):
        for pb in rig.pose.bones: pb.matrix_basis.identity(); pb.rotation_mode = 'QUATERNION'
        for n, q in grip.items(): rig.pose.bones[n].rotation_quaternion = (q[3], q[0], q[1], q[2])
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); em = ev.to_mesh()
        Pp = np.array([tuple(body.matrix_world @ v.co) for v in em.vertices]); ev.to_mesh_clear()
        for pb in rig.pose.bones: pb.matrix_basis.identity()
        bpy.context.view_layer.update()
        return Pp
    PADSOLVE = os.environ.get('PADSOLVE', '1') == '1'
    RW = {f: 0.002 for f in FINGERS}                # gap of the pads over the shaft's surface, adjusted on the skinned mesh
    ang = {}; adj = {}
    for it in range(int(os.environ.get('FIST_ITERS', '10'))):
        grip = {}
        for f in FINGERS:
            k_ = {'Index': 0, 'Middle': 0, 'Ring': 4, 'Pinky': 8}[f]
            if PALMMODE: ang[f] = (solve_finger_pad if PADSOLVE else solve_finger)(f, G, RW[f])[1:4]
            elif it == 0: ang[f] = tuple(np.radians([tcurl[0] + k_, tcurl[1] + k_, tcurl[2]]))
            else: ang[f] = adj.get(f, ang[f])
            a1, a2, a3 = ang[f]
            grip.update(chain_pose(f, [rot(AX, sg * a1), rot(AX, sg * (a1 + a2)), rot(AX, sg * (a1 + a2 + a3))]))
        Pp = posed_mesh(grip); done = True; rep = {}
        for f in FINGERS:
            ids = sum((dom.get(f'Bip01 {S} {f}{i}', []) for i in (1, 2, 3)), [])
            r = adist(Pp[ids], G); mn = float(r.min()); rep[f] = round(mn * 100, 2)
            a1, a2, a3 = ang[f]
            if PALMMODE:
                if mn < RS + 0.0005: RW[f] += RS + 0.0015 - mn; done = False
                elif mn > RS + 0.005: RW[f] = max(RW[f] - (mn - RS - 0.003), 0.0); done = False
            elif mn < RS + 0.0005: adj[f] = (a1, max(a2 - np.radians(3), 0), max(a3 - np.radians(4), 0)); done = False      # open a little
            elif mn > RS + 0.005 and not PALMMODE: adj[f] = (a1, a2 + np.radians(3), a3 + np.radians(4)); done = False                  # close a little
        print('FINGERS2', S, 'iter', it, 'min vertex to axis cm', rep, 'curl deg', {f: tuple(int(round(np.degrees(x))) for x in ang[f]) for f in FINGERS})
        if done: break
    # thumb: over the fingers from the opposite side, its pad near the middle finger's middle phalanx, never inside the shaft
    posed = {f: np.array(fkv(f, *ang[f])[1]) for f in FINGERS}
    t = J['Thumb']
    # the thumb closes on the shaft on its own side, opposite the curled fingers, at the index end
    dT = J['Thumb'][1] - G; dT = unit(dT - AX * (dT @ AX))           # the thumb's own side of the shaft (towards its base), its pad on the surface
    target = G + dT * (RS + half['Thumb'] * 0.9) + AX * ((posed['Index'][1] - G) @ AX)
    wantT = RS + half['Thumb'] * 0.8
    bestt = None
    for th in np.radians(np.arange(-180, 180, 6)):
        R1 = rot(f0, th)
        for ph in np.radians(np.arange(-180, 180, 6)):
            R2 = rot(AX, ph) @ R1
            for ps in np.radians(np.arange(-20, 81, 8)):
                R3 = rot(AX, ps) @ R2
                p1 = t[0] + R2 @ (t[1] - t[0]); p2 = p1 + R3 @ (t[2] - t[1]); p3 = p2 + R3 @ (t[3] - t[2])
                s_ = segsamp(np.array([t[0], p1, p2, p3])); r = adist(s_, G)
                c = np.linalg.norm(p3 - target) + 60 * np.maximum(wantT - r, 0).sum()
                if bestt is None or c < bestt[0]: bestt = (c, (R2, R3), (th, ph, ps), p3)
    grip.update(chain_pose('Thumb', [bestt[1][0], bestt[1][1], bestt[1][1]]))
    Pp = posed_mesh(grip)
    tid = sum((dom.get(f'Bip01 {S} Thumb{i}', []) for i in (1, 2, 3)), [])
    allf = sum((dom.get(f'Bip01 {S} {f}{i}', []) for f in FN for i in (1, 2, 3)), [])
    rr = adist(Pp[allf], G); pv = adist(Pp[hid], G)
    # wrap: angular spread round the axis of the finger joints 2 and 3 (as the Lich King's gate)
    jp = np.array([fkv(f, *ang[f])[1][k] for f in FINGERS for k in (1, 2)] + [bestt[3]])
    d_ = jp - G; e1 = d_[2] - (d_[2] @ AX) * AX; e1 = unit(e1); e2 = np.cross(AX, e1)
    angs = np.degrees(np.arctan2(d_ @ e2, d_ @ e1))
    print('THUMB2', S, np.round(np.degrees(bestt[2]), 0), 'tip to target cm', round(float(np.linalg.norm(bestt[3] - target)) * 100, 2), 'thumb min to axis cm', round(float(adist(Pp[tid], G).min()) * 100, 2))
    print('GRIPGATE', S, 'R cm', RS * 100, 'finger+thumb vertices min to axis cm', round(float(rr.min()) * 100, 2), 'palm min cm', round(float(pv.min()) * 100, 2), 'joint wrap deg', round(float(np.ptp(angs)), 0))
    return dict(grip=grip, G=G, R_HOLE=RS, curl={f: [round(float(np.degrees(x)), 1) for x in ang[f]] for f in FINGERS}, AX=AX, sg=sg, J=J, half=half)
R_SHAFT2 = float(os.environ.get('R_SHAFT', '0.030'))
SOL = {s_: solve2(s_) for s_ in ('R', 'L')}
poses['grip'].update(SOL['R']['grip']); G = SOL['R']['G']
poses['gripL'] = SOL['L']['grip']
WL = H('Bip01 L Hand'); BL = BR('Bip01 L Hand')
poses['holeL'] = {'G_world': SOL['L']['G'].tolist(), 'axis_world': SOL['L']['AX'].tolist(), 'R_HOLE': SOL['L']['R_HOLE']}          # Blender rest world
WR = H('Bip01 R Hand'); BRr = BR('Bip01 R Hand')
# third pass: keep the mallet where the second pass had it (MM9's axis shifted by D_KEEP: the left hand, the bumps and the swing were fitted to
# that line; the palm grip would have moved the shaft 9 cm and its end into the chest). The hand rolls about the shaft's axis through the
# wrist instead (that keeps the knuckle line on the shaft) until the palm grip lands on the kept line; it slides along it freely.
D_KEEP = np.array([float(x) for x in os.environ.get('D_KEEP', '-0.0188,0.0066,0.0668').split(',')])
if os.environ.get('KEEP_SHAFT', '0') == '1':        # off: the roll could not reach the line (7 cm off) and moved MM9's left mitten away
    Gs = SOL['R']['G']; L0 = Om + D_KEEP
    def off_line(ph):
        Rt = rot(AXm, ph) @ RD; g2 = WR + Rt @ (Gs - WR); v = g2 - L0; return np.linalg.norm(v - AXm * (v @ AXm))
    phs = np.radians(np.arange(-90, 90.1, 0.5)); errs = [off_line(p_) for p_ in phs]; ph = float(phs[int(np.argmin(errs))])
    RD = rot(AXm, ph) @ RD
    Dloc = Matrix((BRr.T @ RD @ BRr).tolist()).to_quaternion()
    print('ROLL R about the shaft deg', round(np.degrees(ph), 1), 'grip off the kept line cm', round(min(errs) * 100, 2))
poses['holeR'] = {'G_world': SOL['R']['G'].tolist(), 'G_turned_world': (WR + RD @ (SOL['R']['G'] - WR)).tolist()}
poses['hand_offset'][f'Bip01 {S} Hand'] = [Dloc.x, Dloc.y, Dloc.z, Dloc.w]
# left hand: flexion frame for finger_keys_giant.py (curl amounts from MM9's left finger joints per frame)
JL = {f: np.array([GJ['L'][f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ['L'][f'finger{k}-3_tip']]) for f, k in FN.items()}
knL = unit(JL['Index'][0] - JL['Pinky'][0])
CFL = json.load(open(os.path.join(HERE, 'scripts', 'graft_giant.json')))['sides']['L']
npL = np.array(CFL['n_dir']); npL = unit(npL - knL * (npL @ knL)); hpL = np.array(CFL['h_dir']); hpL = unit(hpL - knL * (hpL @ knL))
heelL = JL['Middle'][0] + npL * 0.05 - hpL * 0.08
ddL = lambda a: np.linalg.norm(JL['Middle'][0] + rot(knL, a) @ (JL['Middle'][3] - JL['Middle'][0]) - heelL)
sgL = 1.0 if ddL(0.5) < ddL(-0.5) else -1.0
poses['flexL'] = {'AX': knL.tolist(), 'sg': sgL, 'Rb': {b.name: BR(b.name).tolist() for b in rig.data.bones if b.name.startswith('Bip01 L ') and any(k in b.name for k in FINGERS + ('Thumb',))}}
print('FLEXL sg', sgL, 'kn', np.round(knL, 3))
json.dump(poses, open(POSES, 'w'), indent=0)
# mallet: MM9's, unrotated, shifted so its axis runs through the fist's hole AFTER the wrist turn (G' = the grip turned by RD about
# the wrist). finger_keys_giant.py takes the wrist turn back out of Xbase's keys, so the mallet spins and slides on MM9's own axis.
Wr = H(f'Bip01 {S} Hand')
G2 = Wr + RD @ (G - Wr)
W0 = MZ['V'] @ M[:3, :3].T + M[:3, 3]
Gm = Om + AXm * ((G2 - Om) @ AXm); D = G2 - Gm
Pw = W0 + D
print('MALLET shift cm', np.round(D * 100, 2), 'grip along handle', round(float((G2 - Om) @ AXm), 3))
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mi = np.linalg.inv(Wm)
for nm in ('Xbase', 'Xhammer'):
    eb = rig.data.edit_bones[nm]; d = Mi[:3, :3] @ D; eb.head += Vector(d); eb.tail += Vector(d)
bpy.ops.object.mode_set(mode='OBJECT')
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.int['part']; dv = bm.verts.layers.deform.verify()
gi = body.vertex_groups.find('Xhammer')
if gi < 0: gi = body.vertex_groups.new(name='Xhammer').index
nv = [bm.verts.new(p.tolist()) for p in Pw]
for x in nv: x[lay] = 20; x[dv][gi] = 1.0
uvl = bm.loops.layers.uv.get('PartUV'); mt = bm.faces.layers.int.get('mat')
flip = np.linalg.det(M[:3, :3]) < 0
for fidx, f in enumerate(MZ['F']):
    tri = (f[0], f[2], f[1]) if flip else tuple(f)
    try:
        q = bm.faces.new([nv[i] for i in tri]); q.smooth = False
    except ValueError: continue
    if uvl is not None:
        if 'UVc' in MZ.files:              # uv_atlas.py layout, per corner (uv_mallet.py)
            fi = fidx; cs = (0, 2, 1) if flip else (0, 1, 2)
            for l, cidx in zip(q.loops, cs): l[uvl].uv = (float(MZ['UVc'][fi, cidx, 0]), float(MZ['UVc'][fi, cidx, 1]))
        else:
            for l, i in zip(q.loops, tri): l[uvl].uv = (float(MZ['UV'][i, 0]), float(MZ['UV'][i, 1]))
    if mt is not None: q[mt] = 3
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FISTDONE')
