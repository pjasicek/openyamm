"""After the paint (UVs frozen), on the rigged master; nothing here touches the painted faces or their UVs.
- fists (mm9_guard_claude/scripts/finish_guard.py): fingers solved round each grip per finger, the thumb over them; a constant wrist turn lines the knuckles up with MM9's weapon axis, the weapon is built turned back by the same angle in the
  hand's frame so it still points where MM9's points. Bone-local rotations in work/hand_poses.json, keyed by finger_keys.py.
- weapons (work/weapons.npz): faces attribute `weapon` (1 sword, 2 shield), rigid on Ybasesword / Ybaseshield, which move to the grip; rest frames stay.
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
WEAP = {'R': dict(bone='Ybasesword', u=np.array([0.0, -1.0, -0.001]), a=np.array([0.54, -0.001, 0.841]), tc=-0.087, r=0.0155, key='sword', kid=1),
        'L': dict(bone='Ybaseshield', u=None, tc=0.0, r=0.0155, key='shield', kid=2)}
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
    G = mcp + f0 * 0.012 + n0 * (R_GRIP + 0.016)
    AX = U
    def _rad(p, c):
        v = p - c; return np.linalg.norm(v - np.outer(v @ AX, AX), axis=-1)
    near = np.linalg.norm(palm - mcp, axis=1) < 0.075
    for step in range(20):
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
        if abs(v.co.x) < 0.7: continue
        nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary and e.link_faces[0][part] == 1]
        if len(nb) == 2: mv[v] = v.co * 0.4 + (nb[0].co + nb[1].co) * 0.3
    for v, c in mv.items(): v.co = c
bm.to_mesh(me); bm.free()
# the sash's two tails end in a fin that stands off the coat: pulled up into a short stub, UVs and paint unchanged
bm = bmesh.new(); bm.from_mesh(me); part = bm.faces.layers.int['part']
for v in {v for f in bm.faces if f[part] == 9 for v in f.verts}:
    if v.co.z < 0.14: v.co.z = 0.14 + (v.co.z - 0.14) * 0.22
bm.to_mesh(me); bm.free()
# the waist: garments were reduced apart, so a jagged gap ran along the sash's lower edge. The sash now laps over the skirt: its lower rim down and out, the skirt's top rim up and in, both on the Spine block
bm = bmesh.new(); bm.from_mesh(me); part = bm.faces.layers.int['part']; bm.verts.ensure_lookup_table()
rc = {v for e in bm.edges if e.is_boundary and e.link_faces[0][part] == 1 for v in e.verts if 0.05 < v.co.z < 0.17 and abs(v.co.x) < 0.33}
rs = {v for e in bm.edges if e.is_boundary and e.link_faces[0][part] == 7 for v in e.verts if v.co.z > 0.06}
def ring1(vs, p): return {e.other_vert(v) for v in vs for e in v.link_edges if any(f[part] == p for f in e.other_vert(v).link_faces)} - vs
n1c, n1s = ring1(rc, 1), ring1(rs, 7)
Cw = Vector((0, 0.02, 0))
def rad(v, k):
    d = Vector((v.co.x, v.co.y, 0)) - Cw; v.co.x, v.co.y = (Cw + d * k).x, (Cw + d * k).y
for v in rc: v.co.z -= 0.024; rad(v, 1.03)
for v in n1c: v.co.z -= 0.010
for v in rs: v.co.z += 0.022; rad(v, 0.93)
for v in n1s: v.co.z += 0.008; rad(v, 0.97)
print('FINISH waist rims', len(rc), len(rs))
bm.to_mesh(me); bm.free()
# --- lining
DT = json.load(open(os.path.join(HERE, 'work', 'dark_texel.json')))
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
part = bm.faces.layers.int['part']; mat = bm.faces.layers.int['mat']
uvb, uvh, uvp_ = bm.loops.layers.uv['UVMap'], bm.loops.layers.uv['HeadUV'], bm.loops.layers.uv['PartUV']
lin = bm.faces.layers.int.new('lining'); weap = bm.faces.layers.int.new('weapon')
sel = {f for f in bm.faces if f[part] == 7}
print('LINING skirt faces', len(sel))
RIMS = {}
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
fs = {f for f in bm.faces if f[part] == 1 and abs(f.calc_center_median().x) > 0.68}
cur = set()
for e in bm.edges:
    if e.is_boundary and e.link_faces and e.link_faces[0] in fs: cur.update(e.verts)
for _ in range(2):
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
a0, a1, f0_, f1 = [int(x) for x in Z['sword']]
made = put(a0, a1, f0_, f1, 1, wp['bone'], lambda q: org + P_['U'] * q[0] + P_['A'] * q[1] + P_['B'] * q[2])
bmesh.ops.recalc_face_normals(bm, faces=made)
# the shield: MM9's pose against the hand, turned with the hand's rest
fr = json.load(open(os.path.join(HERE, 'work', 'shield_frame.json')))
C_ = lambda g: np.array([g[0], -g[2], g[1]])                     # glTF to Blender axes
Dh = np.array(DELTA['Bip01 L Hand'])
GL = placed['L']['G']; tip_m, L_m, W_m, n_m, h_m = C_(fr['tip']), C_(fr['L']), C_(fr['W']), C_(fr['n']), C_(fr['handle'])
HAND_OUT = float(os.environ.get('SHIELD_OUT', 0.012))
TIP = GL + Dh @ (tip_m - h_m); Ls, Ws, Ns = Dh @ L_m, Dh @ W_m, Dh @ n_m; Ws = np.cross(Ns, Ls)
TIP = TIP + Ns * HAND_OUT
a0, a1, f0_, f1 = [int(x) for x in Z['shield']]
made = put(a0, a1, f0_, f1, 2, 'Ybaseshield', lambda q: TIP + Ls * q[0] + Ws * q[1] + Ns * q[2])      # winding built in make_weapons.py: outer, inner and rim are separate islands, recalc turned the inner plate outward
# handle along the knuckles, two struts to the plate
U = placed['L']['U']; A = unit(np.cross(U, Ns)); B = np.cross(U, A)
a0, a1, f0_, f1 = [int(x) for x in Z['bar']]
BL = 0.20
put(a0, a1, f0_, f1, 2, 'Ybaseshield', lambda q: GL + U * q[0] * BL + A * q[1] + B * q[2])
plate = lambda p: float((TIP - p) @ Ns)
for sgn in (-1, 1):
    e = GL + U * sgn * BL * 0.46; d_ = plate(e) + 0.02
    A2 = unit(np.cross(Ns, U)); B2 = np.cross(Ns, A2)
    put(a0, a1, f0_, f1, 2, 'Ybaseshield', lambda q: e + Ns * (q[0] + 0.5) * d_ + A2 * q[1] * 0.8 + B2 * q[2] * 1.2)
print('SHIELD plate from grip', round(plate(GL), 3), 'tip', np.round(TIP, 3), 'L', np.round(Ls, 3), 'n', np.round(Ns, 3))
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FINISH', len(me.polygons), 'tris')
