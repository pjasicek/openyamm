"""After the paint (UVs frozen), on the rigged master; nothing here touches the painted faces or their UVs.
- fists (mm9_guard_claude/scripts/finish_guard.py): fingers solved round each grip per finger, the thumb over them; a constant wrist turn lines the knuckles up with MM9's weapon axis, the weapon is built turned back by the same angle in the
  hand's frame so it still points where MM9's points. Bone-local rotations in work/hand_poses.json, keyed by finger_keys.py.
- weapons (work/weapons.npz): faces attribute `weapon` (1 sword, 2 dagger), rigid on Ybasesword / Ybasedagger, which move to the grip; rest frames stay.
- lining: the skirt whole, three face rings from the other open rims (yoke, boot flares, sleeve ends), an inner copy, flipped, same weights, on one dark texel of the set (work/dark_texel.json).
Args: <in blend> <out blend> <hand poses json>"""
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
DELTA = json.load(open(os.path.join(HERE, 'work', 'fit_v1.blend.delta.json')))
GJ = json.load(open(os.path.join(HERE, 'work', 'hands_v1.json')))['joints']
FN = {'Thumb': 1, 'Index': 2, 'Middle': 3, 'Ring': 4, 'Pinky': 5}
FINGERS = ('Index', 'Middle', 'Ring', 'Pinky')
gid = {g.index: g.name for g in body.vertex_groups}
dom = {}
for v in me.vertices:
    if v.groups:
        g = max(v.groups, key=lambda x: x.weight); dom.setdefault(gid[g.group], []).append(v.index)
COV = np.array([tuple(v.co) for v in me.vertices])
Z = np.load(os.path.join(HERE, 'work', 'weapons.npz'))
# MM9's axes at MM9's rest, Blender coordinates, true-handed: blade direction, across the flat; grip centre on the weapon's own t
WEAP = {'R': dict(bone='Ybasesword', u=np.array([0.0, -1.0, -0.002]), a=np.array([-0.576, 0.002, -0.818]), tc=-0.125, r=0.0165, key='sword', kid=1)}
SOLVE = dict(WEAP); SOLVE['L'] = dict(fist=True, r=0.0115)      # the left hand holds nothing (MM9's `dagger` piece is one empty face): the same solver round a thin virtual grip on the knuckle line, thumb over the fingers
poses = dict(grip={}, relaxed={}, throw={}, hand_offset={})
placed = {}
for S, wp in SOLVE.items():
    Dh = np.array(DELTA[f'Bip01 {S} Hand'])
    J = {f: np.array([GJ[S][f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[S][f'finger{k}-3_tip']]) for f, k in FN.items()}
    kn = unit(J['Index'][0] - J['Pinky'][0])
    U0 = kn if wp.get('fist') else unit(Dh @ wp['u'])           # hilt to tip, our rest
    A0 = np.cross(U0, [0.0, 0.0, 1.0]) if wp.get('fist') else Dh @ wp['a']; A0 = unit(A0 - U0 * (A0 @ U0))
    f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
    n0 = np.cross(kn, f0)
    if (np.mean([J[f][3] for f in FINGERS], 0) - np.mean([J[f][0] for f in FINGERS], 0)) @ n0 < 0: n0 = -n0
    # the least turn of the hand from the knuckle line to the axis
    v_ = np.cross(kn, U0); sn_ = np.linalg.norm(v_); th_ = math.atan2(sn_, kn @ U0)
    RD = rot(v_ / sn_, th_) if sn_ > 1e-6 else np.eye(3)
    BH = BR(f'Bip01 {S} Hand')
    Dloc = Matrix((BH.T @ RD @ BH).tolist()).to_quaternion()
    U = RD.T @ U0; Awv = unit(RD.T @ A0); B_ = np.cross(U, Awv)
    print('WRIST', S, 'turn deg', round(math.degrees(th_), 1), 'axis-knuckle now', round(math.degrees(math.acos(min(1, abs(kn @ U)))), 1))
    R_GRIP = wp['r']
    half = {}
    for f in FN:
        ids = sum((dom.get(f'Bip01 {S} {f}{i}', []) for i in (1, 2, 3)), [])
        Q = COV[ids]; pts = J[f]
        d = np.min([np.linalg.norm(np.cross(Q - a_, unit(b_ - a_)), axis=1) for a_, b_ in zip(pts[:-1], pts[1:])], axis=0)
        half[f] = float(np.median(d))
    palm = COV[dom.get(f'Bip01 {S} Hand', [])]
    mcp = np.mean([J[f][0] for f in FINGERS], 0)
    G = mcp + f0 * 0.012 + n0 * (R_GRIP + 0.012)
    AX = U
    def _rad(p, c):
        v = p - c; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)
    near = np.linalg.norm(palm - mcp, axis=1) < 0.075
    for step in range(9):
        if _rad(palm[near], G).min() >= R_GRIP + 0.004: break
        G = G + n0 * 0.001
    print('GRIP', S, np.round(G, 3), 'palm step mm', step, 'half cm', {k: round(v * 100, 2) for k, v in half.items()})
    def radial(p):
        v = p - G; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)
    def fk(j, angs, sign):
        pts = [j[0]]; total = 0.0; p = j[0]
        for i, a in enumerate(angs):
            total += a
            p = p + rot(AX, sign * total) @ (j[i + 1] - j[i])
            pts.append(p)
        return np.array(pts)
    def samples(pts):
        s = []
        for a, b in zip(pts[:-1], pts[1:]):
            for t in (0.25, 0.5, 0.75, 1.0): s.append(a + (b - a) * t)
        return np.array(s)
    tip0 = J['Middle'][3]
    sg = 1.0 if ((rot(AX, 0.3) @ (tip0 - J['Middle'][0])) - (tip0 - J['Middle'][0])) @ n0 > 0 else -1.0
    out = {}; posed = {}
    for f in FINGERS:
        j = J[f]; best = None; want = R_GRIP + half[f] + 0.005
        for a1 in np.radians(np.arange(0, 96, 4)):
            for a2 in np.radians(np.arange(0, 111, 5)):
                for a3 in np.radians(np.arange(0, 81, 5)):
                    if a3 > a2 + 1e-6: continue
                    p = fk(j, (a1, a2, a3), sg); s_ = samples(p); r = radial(s_)
                    c = ((r - want) ** 2).sum() + 400 * (np.minimum(r - (want - 0.001), 0) ** 2).sum()
                    c += 0.0002 * ((a1 - a2) ** 2 + (a2 - 1.6 * a3) ** 2)
                    if best is None or c < best[0]: best = (c, (a1, a2, a3), p)
        out[f] = best[1]; posed[f] = best[2]
        print('FIST', S, f, np.round(np.degrees(best[1]), 0), 'r', np.round(radial(samples(best[2]))[[1, 5, 9, 11]], 3), 'want', round(want, 3), 'cost', round(best[0], 6))
    def chain_pose(f, deltas):
        res = {}; prev = np.eye(3)
        for i, D in enumerate(deltas):
            n = f'Bip01 {S} {f}{i + 1}'; Rb = BR(n)
            B = Rb.T @ prev.T @ D @ Rb
            q = Matrix(B.tolist()).to_quaternion()
            res[n] = [q.x, q.y, q.z, q.w]; prev = D
        return res
    for f in FINGERS:
        a1, a2, a3 = out[f]
        poses['grip'].update(chain_pose(f, [rot(AX, sg * a1), rot(AX, sg * (a1 + a2)), rot(AX, sg * (a1 + a2 + a3))]))
    t = J['Thumb']
    target = posed['Middle'][2] + unit(posed['Middle'][2] - G) * (half['Middle'] + half['Thumb']) * 0.8
    want = R_GRIP + half['Thumb'] + 0.005
    best = None
    for th in np.radians(np.arange(-60, 101, 5)):
        R1 = rot(f0, th)
        for ph in np.radians(np.arange(-100, 101, 5)):
            R2 = rot(AX, ph) @ R1
            for ps in np.radians(np.arange(0, 76, 6)):
                R3 = rot(AX, ps) @ R2
                p1 = t[0] + R2 @ (t[1] - t[0]); p2 = p1 + R3 @ (t[2] - t[1]); p3 = p2 + R3 @ (t[3] - t[2])
                s_ = samples(np.array([t[0], p1, p2, p3])); r = radial(s_)
                c = np.linalg.norm(p3 - target) + 60 * np.maximum(want - r, 0).sum()
                if best is None or c < best[0]: best = (c, (R2, R3), (th, ph, ps), p3)
    print('THUMB', S, np.round(np.degrees(best[2]), 0), 'tip to target', round(float(np.linalg.norm(best[3] - target)), 3))
    poses['grip'].update(chain_pose('Thumb', [best[1][0], best[1][1], best[1][1]]))
    if wp.get('fist'): continue
    poses['hand_offset'][f'Bip01 {S} Hand'] = [Dloc.x, Dloc.y, Dloc.z, Dloc.w]
    placed[S] = dict(G=G, U=U, A=Awv, B=B_)
json.dump(poses, open(POSES, 'w'), indent=0)
# weapon bones on the grip, rest rotation unchanged
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mi = np.linalg.inv(Wm)
for S, wp in WEAP.items():
    eb = rig.data.edit_bones[wp['bone']]; d = Mi[:3, :3] @ (placed[S]['G'] - H(wp['bone']))
    eb.head += Vector(d); eb.tail += Vector(d)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
# the sleeve ends: Meshy's sawtooth rim, relaxed along itself and rounded about the forearm axis
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
part = bm.faces.layers.int['part']
for _ in range(6):
    mv = {}
    for e in bm.edges:
        pass
    for v in bm.verts:
        if abs(v.co.x) < 0.6: continue
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary and e.link_faces[0][part] == 3]
        if len(nb) == 2: mv[v] = v.co * 0.4 + (nb[0].co + nb[1].co) * 0.3
    for v, c in mv.items(): v.co = c
bm.to_mesh(me); bm.free()
# --- lining
DT = json.load(open(os.path.join(HERE, 'work', 'dark_texel.json')))
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
part = bm.faces.layers.int['part']; mat = bm.faces.layers.int['mat']
uvb, uvh, uvp_ = bm.loops.layers.uv['UVMap'], bm.loops.layers.uv['HeadUV'], bm.loops.layers.uv['PartUV']
lin = bm.faces.layers.int.new('lining'); weap = bm.faces.layers.int.new('weapon')
sel = set()
RIMS = {8: 1, 13: 1}
rims = {}
for pid, rings in RIMS.items():
    fs = {f for f in bm.faces if f[part] == pid}
    cur = set()
    for e in bm.edges:
        if e.is_boundary and e.link_faces and e.link_faces[0] in fs:
            c_ = (e.verts[0].co + e.verts[1].co) / 2
            if pid == 8 and abs(c_.x) < 0.15 and c_.z > 0.5: continue    # the collar: the neck fills it, a lining there came through the skin when the head turned
            cur.update(e.verts)
    rims[pid] = len(cur)
    for _ in range(rings):
        nf = {f for v in cur for f in v.link_faces if f in fs}
        sel |= nf
        cur = {v for f in nf for v in f.verts}
# sleeve ends: three rings up the sleeve from the hand
fs = {f for f in bm.faces if f[part] == 3 and abs(f.calc_center_median().x) > 0.6}
cur = set()
for e in bm.edges:
    if e.is_boundary and e.link_faces and e.link_faces[0] in fs: cur.update(e.verts)
for _ in range(1):
    nf = {f for v in cur for f in v.link_faces if f in fs}
    sel |= nf
    cur = {v for f in nf for v in f.verts}
sel = list(sel)
print('LINING rim verts', rims, 'faces', len(sel))
vn = {}
for f in sel:
    for v in f.verts: vn.setdefault(v, Vector()); vn[v] += f.normal * f.calc_area()
d = bmesh.ops.duplicate(bm, geom=sel)
vmap = d['vert_map']; newf = [x for x in d['geom'] if isinstance(x, bmesh.types.BMFace)]
for v, n_ in vn.items():
    nv = vmap[v] if v in vmap else None
    if nv is not None and n_.length > 1e-12: nv.co = v.co - n_.normalized() * 0.003
bmesh.ops.reverse_faces(bm, faces=newf)
for f in newf:
    f[lin] = 1
    k = {0: 'limbs', 1: 'torso', 2: 'head'}[f[mat]]
    u_ = (DT[k]['u'], 1 - DT[k]['v'])
    for l in f.loops: l[uvp_].uv = u_
print('LINING new faces', len(newf))
# a dark core inside the chest: looking past the mantle into the arm hole you would otherwise see out through the culled far wall of the tunic (the Guard's white fleck, Meshy's shell is hollow)
coreg = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0, matrix=Matrix.Identity(4))
corev = coreg['verts']
tun = np.array([v.index for v in bm.verts if v not in corev and v.link_faces and all(f[part] in (1, 8) for f in v.link_faces) and f'{v.co.x}'[0] and v.co.z > 0.15], int)
bm.verts.ensure_lookup_table()
TP = np.array([bm.verts[int(i)].co[:] for i in tun])
dv0 = bm.verts.layers.deform.verify()
for v in corev:
    x = np.array(v.co[:]) * np.array([0.165, 0.125, 0.24]) + np.array([0.0, 0.025, 0.42])
    v.co = Vector(x)
    near = np.argsort(np.linalg.norm(TP - x, axis=1))[:6]
    acc_ = {}
    for j in near:
        for g_, w_ in bm.verts[int(tun[j])][dv0].items(): acc_[g_] = acc_.get(g_, 0.0) + w_ / 6
    top = sorted(acc_.items(), key=lambda kv: -kv[1])[:4]; tot = sum(w for _, w in top)
    for g_, w_ in top: v[dv0][g_] = w_ / tot
for f in {f for v in corev for f in v.link_faces}:
    f[lin] = 1; f[part] = 31; f[mat] = 1; f.smooth = True
    for l in f.loops: l[uvp_].uv = (DT['torso']['u'], 1 - DT['torso']['v'])
print('CORE faces', len({f for v in corev for f in v.link_faces}))
# a low dark funnel inside the skirt, on the skirt's own weights (a copy of the whole skirt cost 774 triangles)
from mathutils.bvhtree import BVHTree
skf = [f for f in bm.faces if f[part] == 7]
T_ = bmesh.new(); vm = {}
for f in skf:
    for v in f.verts:
        if v not in vm: vm[v] = T_.verts.new(v.co)
    try: T_.faces.new([vm[v] for v in f.verts])
    except ValueError: pass
bvs = BVHTree.FromBMesh(T_)
skv = list({v for f in skf for v in f.verts}); SP_ = np.array([v.co[:] for v in skv])
cy = 0.5 * (SP_[:, 1].min() + SP_[:, 1].max()); ztop = 0.125
NA = 32; RINGS = 4
ang = 2 * np.pi * (np.arange(NA) + 0.5) / NA
vsk = np.arctan2(SP_[:, 1] - cy, SP_[:, 0])
hem = np.array([SP_[np.abs(((vsk - a + np.pi) % (2 * np.pi)) - np.pi) < 0.25, 2].min() for a in ang])
ring = []
for r_ in range(RINGS):
    row = []
    for k, a in enumerate(ang):
        z = ztop + (hem[k] + 0.012 - ztop) * r_ / (RINGS - 1)
        d = Vector((math.cos(a), math.sin(a), 0)); o = Vector((0, cy, z))
        loc, *_ = bvs.ray_cast(o, d, 0.5)
        if loc is None:
            k_ = min(range(len(SP_)), key=lambda i: ((SP_[i] - np.array([0.2 * math.cos(a), cy + 0.15 * math.sin(a), z])) ** 2).sum())
            loc = Vector(SP_[k_])
        row.append(loc - d * 0.005)
    ring.append(row)
dv1 = bm.verts.layers.deform.verify()
nv = [[bm.verts.new(p) for p in row] for row in ring]
for row in nv:
    for v in row:
        near = np.argsort(np.linalg.norm(SP_ - np.array(v.co[:]), axis=1))[:3]
        acc_ = {}
        for j in near:
            for g_, w_ in skv[int(j)][dv1].items(): acc_[g_] = acc_.get(g_, 0.0) + w_ / 3
        top = sorted(acc_.items(), key=lambda kv: -kv[1])[:4]; tot = sum(w for _, w in top)
        for g_, w_ in top: v[dv1][g_] = w_ / tot
nfun = 0
for r_ in range(RINGS - 1):
    for k in range(NA):
        a_, b_, c_, d_ = nv[r_][k], nv[r_][(k + 1) % NA], nv[r_ + 1][(k + 1) % NA], nv[r_ + 1][k]
        for tri_ in ((a_, b_, c_), (a_, c_, d_)):                   # faces toward the axis
            f = bm.faces.new(tri_)
            f[lin] = 1; f[part] = 32; f[mat] = 1; f.smooth = True
            for l in f.loops: l[uvp_].uv = (DT['torso']['u'], 1 - DT['torso']['v'])
            nfun += 1
T_.free()
print('FUNNEL faces', nfun, 'hem', np.round(hem.min(), 3), np.round(hem.max(), 3))
# a dark well under the collar: beside the neck the yoke's rim stands off the skin and the viewer's background showed through (Meshy's shell is hollow, far walls culled). A strip from the rim down and in toward the neck axis, on the rim's weights
dv2 = bm.verts.layers.deform.verify()
rimv = {}
for e in bm.edges:
    if e.is_boundary and e.link_faces and e.link_faces[0][part] == 8:
        c_ = (e.verts[0].co + e.verts[1].co) / 2
        if abs(c_.x) < 0.15 and c_.z > 0.5:
            for x in e.verts: rimv[x] = np.array(x.co[:])
rl = list(rimv); RP = np.array([rimv[x] for x in rl])
ax0 = np.array([0.0, RP[:, 1].mean(), 0.0])
angr = np.arctan2(RP[:, 1] - ax0[1], RP[:, 0])
NC = 32; angc = 2 * np.pi * (np.arange(NC) + 0.5) / NC - np.pi
top = []; low = []
for a in angc:
    dd = np.abs(((angr - a + np.pi) % (2 * np.pi)) - np.pi); k = np.argsort(dd)[:3]; p0 = RP[k].mean(0)
    p1 = p0 + np.array([0, 0, -0.006]); r0 = p1 - np.r_[0, ax0[1], p1[2]]
    top.append(p1); low.append(p1 + np.array([-r0[0] * 0.55, -r0[1] * 0.55, -0.03]))
nvt = []
for row in (top, low):
    rr = []
    for p_ in row:
        v = bm.verts.new(Vector(p_))
        k = np.argsort(np.linalg.norm(RP - np.array(p_), axis=1))[:4]; acc_ = {}
        for j in k:
            for g_, w_ in rl[int(j)][dv2].items(): acc_[g_] = acc_.get(g_, 0.0) + w_ / 4
        topw = sorted(acc_.items(), key=lambda kv: -kv[1])[:4]; tot = sum(w for _, w in topw)
        for g_, w_ in topw: v[dv2][g_] = w_ / tot
        rr.append(v)
    nvt.append(rr)
nwell = 0
for k in range(NC):
    a_, b_, c_, d_ = nvt[0][k], nvt[0][(k + 1) % NC], nvt[1][(k + 1) % NC], nvt[1][k]
    for tri_ in ((a_, c_, b_), (a_, d_, c_)):
        f = bm.faces.new(tri_); f.normal_update()
        if f.normal.z < 0: f.normal_flip()
        f[lin] = 1; f[part] = 32; f[mat] = 1; f.smooth = True
        for l in f.loops: l[uvp_].uv = (DT['torso']['u'], 1 - DT['torso']['v'])
        nwell += 1
print('FINISH well faces', nwell, 'rim verts', len(rl))
# --- weapons
dv = bm.verts.layers.deform.verify()
bm.verts.ensure_lookup_table()
for S, wp in WEAP.items():
    a0, a1, f0_, f1 = [int(x) for x in Z[wp['key']]]
    g = body.vertex_groups.get(wp['bone']) or body.vertex_groups.new(name=wp['bone'])
    P_ = placed[S]; org = P_['G'] - P_['U'] * wp['tc']
    new = []
    for i in range(a0, a1):
        t, a_, b_ = Z['v'][i]
        p = org + P_['U'] * t + P_['A'] * a_ + P_['B'] * b_
        x = bm.verts.new(Vector(p)); x[dv][g.index] = 1.0; new.append(x)
    bm.verts.ensure_lookup_table()
    for tri in Z['f'][f0_:f1]:
        try:
            fc = bm.faces.new([new[int(i) - a0] for i in tri])
        except ValueError:
            continue
        fc[weap] = wp['kid']; fc[mat] = 3; fc[part] = 30; fc.smooth = True
        for l, i in zip(fc.loops, tri): l[uvp_].uv = tuple(Z['uv'][int(i)])
    wf = [f for f in bm.faces if f[weap] == wp['kid']]
    bmesh.ops.recalc_face_normals(bm, faces=wf)
# the helmet's cheek bars: rigid on Head they parted from the coif and the neck skin when the head turned (detached audit). They take the skin's weights under them, so the lower ends stay on it
seen = set(); bars = []
for v in bm.verts:
    if v in seen or not v.link_faces or v.link_faces[0][mat] != 2: continue
    st = [v]; seen.add(v); isl = []
    while st:
        x = st.pop(); isl.append(x)
        for e in x.link_edges:
            y_ = e.other_vert(x)
            if y_ not in seen: seen.add(y_); st.append(y_)
    c_ = np.array([x.co[:] for x in isl])
    if len(isl) < 60 and np.ptp(c_[:, 2]) > 0.15 and 0.08 < np.abs(c_[:, 0]).mean() < 0.13: bars.append(isl)
bv = {x for isl in bars for x in isl}
hv = [v for v in bm.verts if v not in bv and v.link_faces and v.link_faces[0][mat] == 2 and v.co.z > 0.5]
HP = np.array([v.co[:] for v in hv])
new_w = {}
for x in bv:
    near = np.argsort(np.linalg.norm(HP - np.array(x.co[:]), axis=1))[:8]
    acc_ = {}
    for j in near:
        for g_, w_ in hv[int(j)][dv].items(): acc_[g_] = acc_.get(g_, 0.0) + w_ / 8
    top = sorted(acc_.items(), key=lambda kv: -kv[1])[:4]; tot = sum(w for _, w in top)
    new_w[x] = {g_: w_ / tot for g_, w_ in top}
for x, w_ in new_w.items():
    x[dv].clear()
    for g_, w2 in w_.items(): x[dv][g_] = w2
# their lower ends rest on the collar at bind, which does not hold them: raised clear of it, so the bars hang from the helmet (Head) alone
BAR_GAP = 0.012      # 1.2 cm over the collar (run 2): at 3 mm the audit took the collar for the bar's holder and saw it lift off with the head bowed (Sleep, 5.0 cm)
TV = np.array([v.co[:] for v in bm.verts if v.link_faces and v.link_faces[0][mat] == 1])
for isl in bars:
    c_ = np.array([x.co[:] for x in isl]); dm = np.array([np.linalg.norm(TV - p, axis=1).min() for p in c_])
    zmin = c_[:, 2].min(); zc = c_[:, 2].max() - 0.133              # the collar's top, 1.705 m at bind
    top = zc + 0.03
    for x in isl:
        if x.co.z < top: x.co.z = zc + BAR_GAP + (x.co.z - zmin) / (top - zmin) * (top - zc - BAR_GAP)
    print('BAR lifted', round(float(zc - zmin), 3))
print('FINISH bars', len(bars), len(bv))
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FINISH', len(me.polygons), 'tris')
