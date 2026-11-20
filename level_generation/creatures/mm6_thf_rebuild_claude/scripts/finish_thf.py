"""After the paint (UVs frozen), on the rigged master (mm9_highwayman_claude/scripts/finish_hw.py adapted): nothing here touches the painted faces or their UVs.
- fists: fingers solved round each dagger grip per finger, the thumb over them; a wrist turn lines the knuckles up with MM9's weapon axis
  (stored as `hand_offset`, applied with the grip by finger_keys_thf.py), the dagger is built turned back by it so it points where MM9's
  sword (true right) and dagger (true left) point. Bone-local rotations in <hand poses json>.
- daggers: the approved MM6 daggers (2026-10-14, work/daggers.npz from extract_daggers.py) scaled with the body (x SCALE), face attribute
  `weapon` (1 right, 2 left), part 30, rigid on Ybasesword / Ybasedagger, which move to the grip (rest frames stay). UVs: the old painted
  dagger column turned into the body atlas's top strip (v 0.935..0.995), filled by compose_thf.py.
Args: <in blend> <out blend> <hand poses json>"""
import bpy, bmesh, sys, json, math, os
import numpy as np
from mathutils import Vector, Matrix
IN, OUT, POSES = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALE = 1.1664
STRIP = (0.935, 0.06)                      # v0, height of the dagger strip (Blender UV)
OLD_COL = (0.925, 0.07)                    # the old column: u0, width (glTF UV); along = v
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
Z = np.load(os.path.join(HERE, 'work', 'daggers.npz'))
# the dagger in its own frame: t along the blade (hilt -> tip), a across the flat, b through it; scaled with the body
DAG = {}
for S in 'RL':
    c, u, a, b = Z[S + '_frame']
    P = Z[S + '_P'] - c
    loc = np.c_[P @ u, P @ a, P @ b] * SCALE
    tg = float(Z[S + '_grip_t'][0]) * SCALE
    near = np.abs(loc[:, 0] - tg) < 0.02
    rg = float(np.percentile(np.hypot(loc[near, 1], loc[near, 2]), 70))
    DAG[S] = dict(loc=loc, T=Z[S + '_T'], UV=Z[S + '_UV'], tc=tg, r=rg)
    print('DAGGER', S, 'length', round(float(np.ptp(loc[:, 0])), 3), 'grip t', round(tg, 3), 'grip r', round(rg, 4))
# MM9's weapon axes at MM9's rest, Blender coordinates, true-handed (mm9_highwayman_claude/scripts/finish_hw.py)
WEAP = {'R': dict(bone='Ybasesword', u=np.array([0.0, -1.0, -0.002]), a=np.array([-0.576, 0.002, -0.818]), kid=1),
        'L': dict(bone='Ybasedagger', u=np.array([-0.001, -1.0, 0.003]), a=np.array([0.341, -0.003, -0.94]), kid=2)}
poses = dict(grip={}, relaxed={}, throw={}, hand_offset={})
placed = {}
for S, wp in WEAP.items():
    Dh = np.array(DELTA[f'Bip01 {S} Hand'])
    U0 = unit(Dh @ wp['u'])
    A0 = Dh @ wp['a']; A0 = unit(A0 - U0 * (A0 @ U0))
    J = {f: np.array([GJ[S][f'finger{k}-{j}'] for j in (1, 2, 3)] + [GJ[S][f'finger{k}-3_tip']]) for f, k in FN.items()}
    kn = unit(J['Index'][0] - J['Pinky'][0])
    f0 = unit(np.mean([J[f][1] - J[f][0] for f in FINGERS], 0)); f0 = unit(f0 - kn * (f0 @ kn))
    n0 = np.cross(kn, f0)
    if (np.mean([J[f][3] for f in FINGERS], 0) - np.mean([J[f][0] for f in FINGERS], 0)) @ n0 < 0: n0 = -n0
    v_ = np.cross(kn, U0); sn_ = np.linalg.norm(v_); th_ = math.atan2(sn_, kn @ U0)
    RD = rot(v_ / sn_, th_) if sn_ > 1e-6 else np.eye(3)
    BH = BR(f'Bip01 {S} Hand')
    Dloc = Matrix((BH.T @ RD @ BH).tolist()).to_quaternion()
    U = RD.T @ U0; Awv = unit(RD.T @ A0); B_ = np.cross(U, Awv)
    print('WRIST', S, 'turn deg', round(math.degrees(th_), 1), 'axis-knuckle now', round(math.degrees(math.acos(min(1, abs(kn @ U)))), 1))
    R_GRIP = DAG[S]['r']
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
    for th in np.radians(np.arange(-120, 121, 5)):
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
# --- daggers
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
part = bm.faces.layers.int['part']
weap = bm.faces.layers.int.get('weapon') or bm.faces.layers.int.new('weapon')
uvb = bm.loops.layers.uv['UVMap']; uvh = bm.loops.layers.uv.get('HeadUV')
dv = bm.verts.layers.deform.verify()
for S, wp in WEAP.items():
    g = body.vertex_groups.get(wp['bone']) or body.vertex_groups.new(name=wp['bone'])
    P_ = placed[S]; D_ = DAG[S]; org = P_['G'] - P_['U'] * D_['tc']
    new = []
    for t, a_, b_ in D_['loc']:
        x = bm.verts.new(Vector(org + P_['U'] * t + P_['A'] * a_ + P_['B'] * b_)); x[dv][g.index] = 1.0; new.append(x)
    bm.verts.ensure_lookup_table()
    made = []
    for tri in D_['T']:
        try:
            fc = bm.faces.new([new[int(i)] for i in tri])
        except ValueError:
            continue
        fc[weap] = wp['kid']; fc[part] = 30; fc.smooth = False
        for l, i in zip(fc.loops, tri):
            uo, vo = D_['UV'][int(i)]
            across = (uo - OLD_COL[0]) / OLD_COL[1]
            l[uvb].uv = (0.005 + vo * 0.99, STRIP[0] + across * STRIP[1])
            if uvh: l[uvh].uv = (0.0, 0.0)
        made.append(fc)
    # closed parts (welded by position, as check_winding.py sees them) with a negative volume are turned outside out
    key = {}; pid = {v: key.setdefault(tuple(round(c, 5) for c in v.co), len(key)) for f in made for v in f.verts}
    par = list(range(len(key)))
    def _f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for f in made:
        ids = [pid[v] for v in f.verts]
        for u in ids[1:]:
            ra, ru = _f(ids[0]), _f(u)
            if ra != ru: par[ru] = ra
    groups = {}
    for f in made: groups.setdefault(_f(pid[f.verts[0]]), []).append(f)
    flipped = 0
    for fs in groups.values():
        c = sum((v.co for f in fs for v in f.verts), Vector()) / (3 * len(fs))
        vol = sum((f.verts[0].co - c).dot((f.verts[1].co - c).cross(f.verts[2].co - c)) for f in fs) / 6
        if vol < 0:
            bmesh.ops.reverse_faces(bm, faces=fs); flipped += 1
    print('DAGGER parts', len(groups), 'flipped', flipped)
    print('DAGGER placed', S, len(made), 'faces')
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FINISH', len(me.polygons), 'tris')
