"""After the paint (UVs frozen), on the rigged master; nothing here touches the painted faces or their UVs.
- fists (mm9_guard_claude/scripts/finish_guard.py): fingers solved round each grip per finger, the thumb over them; a constant wrist turn lines the knuckles up with MM9's weapon axis, the weapon is built turned back by the same angle in the
  hand's frame so it still points where MM9's points. Bone-local rotations in work/hand_poses.json, keyed by finger_keys.py.
- the axe (work/weapons.npz): faces attribute `weapon`, rigid on RHand1, which moves to the grip; rest frames stay.
- lining: the skirt whole, rings from the other open rims (boot cuffs, helmet), an inner copy, flipped, same weights, on one dark texel of the set (work/dark_texel.json).
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
AX = json.load(open(os.path.join(HERE, 'work', 'axe_axes.json')))
# MM9's axes at MM9's rest, Blender coordinates, true-handed: haft direction, toward the edge; grip centre on the weapon's own s. The left hand is a fist round nothing (MM9's mitt).
WEAP = {'R': dict(bone='RHand1', u=np.array(AX['u']), a=np.array(AX['a']), tc=0.035, r=0.0125, key='axe', kid=1),
        'L': dict(bone=None, u=None, tc=0.0, r=0.011, key=None, kid=2)}
poses = dict(grip={}, relaxed={}, throw={}, hand_offset={})
placed = {}
for S, wp in WEAP.items():
    Dh = np.array(DELTA[f'Bip01 {S} Hand'])
    J = {f: np.array([GJ[S][f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[S][f'finger{k}-3_tip']]) for f, k in FN.items()}
    kn = unit(J['Index'][0] - J['Pinky'][0])
    f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
    n0 = np.cross(kn, f0)
    if (np.mean([J[f][3] for f in FINGERS], 0) - np.mean([J[f][0] for f in FINGERS], 0)) @ n0 < 0: n0 = -n0
    if wp['u'] is not None:
        U0 = unit(Dh @ wp['u'])                                 # hilt to tip, our rest
        A0 = Dh @ wp['a']; A0 = unit(A0 - U0 * (A0 @ U0))
    else:
        U0 = kn; A0 = f0                                        # the shield's handle runs along the knuckles: no wrist turn
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
    G = mcp + f0 * 0.012 + n0 * (R_GRIP + 0.018)
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
    poses['hand_offset'][f'Bip01 {S} Hand'] = [Dloc.x, Dloc.y, Dloc.z, Dloc.w]
    placed[S] = dict(G=G, U=U, A=Awv, B=B_)
json.dump(poses, open(POSES, 'w'), indent=0)
# weapon bones on the grip, rest rotation unchanged
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
Mi = np.linalg.inv(Wm)
eb = rig.data.edit_bones['RHand1']; d = Mi[:3, :3] @ (placed['R']['G'] - H('RHand1'))
eb.head += Vector(d); eb.tail += Vector(d)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
# --- lining
DT = json.load(open(os.path.join(HERE, 'work', 'dark_texel.json')))
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
part = bm.faces.layers.int['part']; mat = bm.faces.layers.int['mat']
uvb, uvh, uvp_ = bm.loops.layers.uv['UVMap'], bm.loops.layers.uv['HeadUV'], bm.loops.layers.uv['PartUV']
lin = bm.faces.layers.int.new('lining'); weap = bm.faces.layers.int.new('weapon')
sel = {f for f in bm.faces if f[part] == 7}
print('LINING skirt faces', len(sel))
RIMS = {11: 2}                                           # the helmet has its own inner wall
rims = {}
for pid, rings in RIMS.items():
    fs = {f for f in bm.faces if f[part] == pid}
    cur = set()
    for e in bm.edges:
        if e.is_boundary and e.link_faces and e.link_faces[0] in fs: cur.update(e.verts)
    if pid == 21:                                       # the helmet: only its lower rim and face opening, not the small holes under the horn collars
        cur = {v for v in cur if v.co.z < 0.44}
    rims[pid] = len(cur)
    for _ in range(rings):
        nf = {f for v in cur for f in v.link_faces if f in fs}
        sel |= nf
        cur = {v for f in nf for v in f.verts}
sel = list(sel)
# the bracer's end: the voxel skin's cap, smeared paint where a bent wrist shows it. On the dark texel
capn = 0
DTc = json.load(open(os.path.join(HERE, 'work', 'dark_texel.json')))['torso']
for S_ in 'RL':
    W_ = Vector(H(f'Bip01 {S_} Hand')); E_ = Vector(H(f'Bip01 {S_} Forearm')); d_ = (W_ - E_).normalized()
    for f in bm.faces:
        if f[part] != 1: continue
        c_ = f.calc_center_median() - W_
        if c_.dot(d_) > -0.015 and (c_ - d_ * c_.dot(d_)).length < 0.075 and f.normal.dot(d_) > 0.45:
            for l in f.loops: l[uvp_].uv = (DTc['u'], 1 - DTc['v'])
            capn += 1
for f in bm.faces:                                       # the skin's cap under the belt shows in the gap when the skirt lifts
    if f[part] == 1 and f.normal.z < -0.5 and f.calc_center_median().z < 0.06 and abs(f.calc_center_median().x) < 0.23:
        for l in f.loops: l[uvp_].uv = (DTc['u'], 1 - DTc['v'])
        capn += 1
print('LINING cap faces', capn)
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
# --- weapons
json.dump({S: dict(G=placed[S]['G'].tolist(), U=placed[S]['U'].tolist()) for S in placed}, open(os.path.join(HERE, 'work', 'grips.json'), 'w'), indent=0)
dv = bm.verts.layers.deform.verify()
bm.verts.ensure_lookup_table()
def put(a0, a1, f0_, f1, kid, group, xf):
    g = body.vertex_groups.get(group) or body.vertex_groups.new(name=group)
    new = []
    for i in range(a0, a1):
        x = bm.verts.new(Vector(xf(Z['v'][i]))); x[dv][g.index] = 1.0; new.append(x)
    bm.verts.ensure_lookup_table()
    made = []
    for tri in Z['f'][f0_:f1]:
        try:
            fc = bm.faces.new([new[int(i) - a0] for i in tri])
        except ValueError:
            continue
        fc[weap] = kid; fc[mat] = 3; fc[part] = 30; fc.smooth = True; made.append(fc)
        for l, i in zip(fc.loops, tri): l[uvp_].uv = tuple(Z['uv'][int(i)])
    return made
wp = WEAP['R']; P_ = placed['R']; org = P_['G'] - P_['U'] * wp['tc']
a0, a1, f0_, f1 = [int(x) for x in Z['axe']]
made = put(a0, a1, f0_, f1, 1, wp['bone'], lambda q: org + P_['U'] * q[0] + P_['A'] * q[1] + P_['B'] * q[2])
if P_['U'] @ np.cross(P_['A'], P_['B']) < 0: bmesh.ops.reverse_faces(bm, faces=made)
bm.to_mesh(me); bm.free()
# the skirt's lining in fewer triangles: only its faces collapse
n0 = len(me.polygons)
la = np.zeros(n0, int); me.attributes['lining'].data.foreach_get('value', la)
fpt = np.zeros(n0, int); me.attributes['part'].data.foreach_get('value', fpt)
free = set(int(v) for p in me.polygons if la[p.index] and fpt[p.index] == 7 for v in p.vertices)
g = body.vertex_groups.new(name='lining_keep')
g.add([v.index for v in me.vertices if v.index not in free], 1.0, 'REPLACE')
for o_ in bpy.data.objects: o_.select_set(o_ is body)
bpy.context.view_layer.objects.active = body
dm = body.modifiers.new('LD', 'DECIMATE'); dm.ratio = (n0 - float(os.environ.get('LINE_DROP', 460))) / n0; dm.vertex_group = 'lining_keep'; dm.invert_vertex_group = True; dm.vertex_group_factor = 1000; dm.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='LD')
body.vertex_groups.remove(body.vertex_groups['lining_keep'])
print('LINING reduced', n0, len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FINISH', len(me.polygons), 'tris')
