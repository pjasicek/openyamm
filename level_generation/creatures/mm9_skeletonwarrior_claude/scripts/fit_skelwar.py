"""Rigid-piece fit of the Meshy armoured skeleton to the MM9 SKELETONWARRIOR rig (true handedness, mirror_source.py).

Bones do not bend, so every piece is rigid on one joint where it can be (the MM6 skeleton's rule) and MM9's joints move onto
the places where Meshy's pieces meet: joints are translated only, rest rotations stay, so MM9's local rotations play
unchanged (the Dagrell's joint-fix lesson: a rigid piece turns about its own pivot, so a pivot off the piece's end swings
the piece away from its neighbour by offset x angle).
- arms: shoulder at the top of the humerus, elbow in the elbow cap, wrist at the top of the gauntlet;
- legs: hip at the femur head, knee at the femur condyles, ankle in the boot on the shaft line;
- spine column blended between Spine/Spine1/Spine2 (one piece, it may flex), neck between Neck and Head;
- cuirass rigid on Spine3, belt rigid on Spine (the parent of the thighs in MM9), helmet and skull rigid on Head;
- skirt plates: one smooth field of height and side, belt -> thighs, so overlapping plates stay together;
- boots: Calf -> Foot blended round the ankle (MM9 never keys Toe0);
- gauntlets: five fingers by connectivity (mm6_gob2_claude/scripts/fit_fingers.py), 15 bones per side: MM9's hands are rigid
  mittens with a thumb key in one clip, so these only hold a pose (the grip, the relaxed hand, the throw).
The HD pose is not MM9's bind (MM9's legs slant back, its torso forward, the hands turn in round the scimitar handle), and a
rest offset of 10 degrees would stay in every clip, so each piece is then turned onto the MM9 bone direction about its own
joint, chain by chain, keeping our lengths. Per bone: M_b(v) = J_rest + C_b (v - J_fit); a vertex takes the blend of its
bones' M_b. The HD-pose position stays in the POINT attribute `fitco`: the upload for Meshy is exported in it, so the
paint matches the masters.
Writes object 'Body' parented to 'MM9_Rig', report json. Args: <sym blend> <out blend> <report json>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
MID = -0.0037
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Parts']; rig = bpy.data.objects['MM9_Rig']; me = body.data
assert rig.matrix_world.is_identity or True
body.name = 'Body'; me.name = 'Body'
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
pid = np.zeros(len(co), np.int32); me.attributes['pid'].data.foreach_get('value', pid)
E = np.zeros(len(me.edges) * 2, np.int32); me.edges.foreach_get('vertices', E); E = E.reshape(-1, 2)
adj = [[] for _ in co]
for a, b in E:
    adj[a].append(b); adj[b].append(a)
W = rig.matrix_world
IW = W.inverted()
RJ = lambda n: np.array(W @ rig.data.bones[n].head_local)
rep = {}


def pts(*ids):
    return co[np.isin(pid, ids)]


def pca_ends(v, frac=0.08):
    c = v.mean(0); u, s, vt = np.linalg.svd(v - c, full_matrices=False); a = vt[0]
    if a[2] < 0: a = -a
    t = (v - c) @ a
    hi = v[t > t.max() - (t.max() - t.min()) * frac].mean(0)
    lo = v[t < t.min() + (t.max() - t.min()) * frac].mean(0)
    return hi, lo, a


def around(v, z, h=0.02):
    m = np.abs(v[:, 2] - z) < h
    return v[m].mean(0) if m.any() else v[np.argmin(np.abs(v[:, 2] - z))]


T = {}
spine = pts(0); neck = pts(18)
col = lambda z: around(spine, z, 0.03)
for n in ('Bip01 Pelvis', 'Bip01 Spine', 'Bip01 Spine1', 'Bip01 Spine2'):
    p = RJ(n); q = col(np.clip(p[2], 0.05, 0.31)); T[n] = np.array([MID, q[1], p[2]])
for n in ('Bip01 Spine3', 'Bip01 Neck', 'Bip01 Head'):
    p = RJ(n); q = around(neck, np.clip(p[2], 0.56, 0.66), 0.03); T[n] = np.array([MID, q[1], p[2]])
# right side (-X), mirrored onto the left
hum = pts(6); elb = pts(23); hand = pts(7); fem = pts(3); knee = pts(37); boot = pts(12)
sh, eh, _ = pca_ends(hum)
top_e = elb[elb[:, 2] > elb[:, 2].max() - 0.025].mean(0)
elbow = (eh + top_e) / 2
wr = hand[hand[:, 2] > hand[:, 2].max() - 0.02].mean(0)
hi, lo, _ = pca_ends(fem)
kn = (lo + knee[knee[:, 2] > knee[:, 2].max() - 0.03].mean(0)) / 2
floor = co[:, 2].min()
ank_z = RJ('Bip01 R Foot')[2]
shaft = boot[(boot[:, 2] > -0.85) & (boot[:, 2] < -0.6)]
ch, cl, a = pca_ends(shaft)
ank = cl + a * (ank_z - cl[2]) / a[2]
sole = boot[boot[:, 2] < floor + 0.06]
c = sole[:, :2].mean(0); u, s, vt = np.linalg.svd(sole[:, :2] - c, full_matrices=False); fw = vt[0]
if fw[1] > 0: fw = -fw
t = (sole[:, :2] - ank[:2]) @ fw
ball = np.array([*(ank[:2] + fw * t.max() * 0.62), floor + 0.035])
R = dict(UpperArm=sh, Forearm=elbow, Hand=wr, Thigh=hi, Calf=kn, Foot=ank, Toe0=ball)
for k, p in R.items():
    T[f'Bip01 R {k}'] = p
    T[f'Bip01 L {k}'] = p * [-1, 1, 1] + [2 * MID, 0, 0]
nk = T['Bip01 Neck']
for s, sg in (('R', -1), ('L', 1)):
    T[f'Bip01 {s} Clavicle'] = np.array([MID + sg * 0.05, nk[1], nk[2]])
rep['joints'] = {k: np.round(v, 4).tolist() for k, v in T.items()}
rep['moved_cm'] = {k: round(float(np.linalg.norm(v - RJ(k))) * 100, 1) for k, v in T.items()}
print('MOVED', rep['moved_cm'])

# fingers on the right gauntlet (pid 7), by connectivity; the left is its mirror (pid 107)
idx = np.where(pid == 7)[0]; local = {int(i): k for k, i in enumerate(idx)}
hv = co[idx]
F = (hv.mean(0) - wr); F /= np.linalg.norm(F)
u, s, vt = np.linalg.svd(hv - hv.mean(0), full_matrices=False)
F = vt[0] if vt[0] @ F > 0 else -vt[0]
depth = (hv - wr) @ F


def comps(mask):
    m = set(np.where(mask)[0].tolist()); out = []
    while m:
        st = [m.pop()]; c = [st[0]]
        while st:
            x = st.pop()
            for y in adj[idx[x]]:
                y = local.get(int(y))
                if y in m:
                    m.remove(y); st.append(y); c.append(y)
        out.append(np.array(c))
    return out


tmax = depth.max(); thumb = None
for t in np.arange(0.02, tmax, 0.002):
    cs = [c for c in comps(depth > t) if len(c) >= 10]
    if len(cs) >= 2:
        cs.sort(key=len); thumb = cs[0]; tt = t; break
print('thumb cut', round(float(tt), 3), [len(c) for c in cs])
rest = np.ones(len(hv), bool); rest[thumb] = False
fingers = None
for t in np.arange(tt, tmax, 0.002):
    cs = [c for c in comps((depth > t) & rest) if len(c) >= 8]
    if len(cs) == 4:
        fingers = cs; ft = t; break
print('finger cut', round(float(ft), 3), [len(c) for c in fingers])
J0 = [(thumb, 'Thumb')]
nrm = np.cross(F, hv[fingers[0]].mean(0) - hv[fingers[-1]].mean(0))
# order index .. pinky from the thumb side
th_c = hv[thumb].mean(0)
order = sorted(fingers, key=lambda c: np.linalg.norm(hv[c].mean(0) - th_c))
NAMES = ['Index', 'Middle', 'Ring', 'Pinky']
chains = {}; verts_of = {}


def centreline(c):
    p = hv[c]; d = (p - wr) @ F
    base_i = np.argsort(d)[: max(3, len(c) // 12)]
    base = p[base_i].mean(0)
    # geodesic-free: the piece's own principal axis from the base
    a = p.mean(0) - base; a /= np.linalg.norm(a)
    u, s, vt = np.linalg.svd(p - p.mean(0), full_matrices=False)
    a = vt[0] if vt[0] @ a > 0 else -vt[0]
    t = (p - base) @ a
    bins = np.linspace(t.min(), t.max() + 1e-6, 7)
    line = [p[(t >= bins[i]) & (t < bins[i + 1])].mean(0) for i in range(6) if ((t >= bins[i]) & (t < bins[i + 1])).any()]
    return base, np.array(line), a, float(t.max() - t.min())


for c, name in [(thumb, 'Thumb')] + list(zip(order, NAMES)):
    base, line, a, L = centreline(c)
    web = 0.28 if name != 'Thumb' else 0.10
    root = line[0] - a * L * web
    pts_ = np.vstack([root, line])
    tip = hv[c][np.argmax((hv[c] - base) @ a)]
    pts_ = np.vstack([pts_, tip])
    seg = np.linalg.norm(np.diff(pts_, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)]); tot = s[-1]
    fr = (0.0, 0.42, 0.70, 1.0) if name != 'Thumb' else (0.0, 0.48, 1.0)
    jp = [np.array([np.interp(f * tot, s, pts_[:, i]) for i in range(3)]) for f in fr]
    if name == 'Thumb':
        jp = [jp[0], jp[1], (jp[1] + jp[2]) / 2 + 0 * jp[0], jp[2]]
        jp[1] = (jp[0] * 0.6 + jp[1] * 0.4)
    chains[name] = jp; verts_of[name] = idx[c]
    print('FINGER', name, len(c), 'len', round(tot, 3), np.round(jp[0], 3))
rep['fingers'] = {k: [np.round(p, 4).tolist() for p in v] for k, v in chains.items()}

# rest rotations: our pieces onto the MM9 bone directions
def rotmin(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    return np.array(Vector(a).rotation_difference(Vector(b)).to_matrix())


def slerp_i(R, t):
    q = Matrix(R.tolist()).to_quaternion(); ax, an = q.to_axis_angle()
    from mathutils import Quaternion
    return np.array(Quaternion(ax, an * t).to_matrix())


MIR = lambda p: p * [-1, 1, 1] + [2 * MID, 0, 0]
SM = np.diag([-1.0, 1, 1])
bones = rig.data.bones
follow = {'Bip01 R Finger0': 'Bip01 R Hand', 'Bip01 L Finger0': 'Bip01 L Hand', 'RHand1': 'Bip01 R Hand', 'LHand1': 'Bip01 L Hand',
          'Bone01': 'Bip01 R Hand', 'Box01': 'Bip01 Spine', 'Box02': 'Bip01 Spine', 'Box05': 'Bip01 Spine', 'Box06': 'Bip01 Spine'}
JF = dict(T)
for k, v in follow.items():
    JF[k] = RJ(k) + (T[v] - RJ(v))
JF['Scene Root'] = RJ('Scene Root')
FNAMES = list(chains)
for name, jp in chains.items():
    for i in range(3):
        JF[f'Bip01 R {name}{i + 1}'] = jp[i]; JF[f'Bip01 L {name}{i + 1}'] = MIR(jp[i])
CR = {}
up = rotmin(T['Bip01 Neck'] - T['Bip01 Spine'], RJ('Bip01 Neck') - RJ('Bip01 Spine'))
print('torso turn deg', round(np.degrees(np.arccos(np.clip((np.trace(up) - 1) / 2, -1, 1))), 1))
for n, R_ in (('Bip01 Spine1', slerp_i(up, 0.5)), ('Bip01 Spine2', up), ('Bip01 Spine3', up), ('Bip01 Neck', up),
              ('Bip01 R Clavicle', up), ('Bip01 L Clavicle', up)):
    CR[n] = R_
for s_ in 'RL':
    for a_, b_ in (('UpperArm', 'Forearm'), ('Forearm', 'Hand'), ('Thigh', 'Calf'), ('Calf', 'Foot'), ('Foot', 'Toe0')):
        A, B = f'Bip01 {s_} {a_}', f'Bip01 {s_} {b_}'
        CR[A] = rotmin(T[B] - T[A], RJ(B) - RJ(A))
# the hand: knuckle line (pinky -> index) along the MM9 handle, fingers across it toward the MM9 hand bone's direction
hilt = np.array([-0.34, -0.242, -0.057]) - np.array([-0.335, -0.163, -0.161]); hilt /= np.linalg.norm(hilt)
F9 = RJ('Bip01 R Finger0') - RJ('Bip01 R Hand'); F9 -= hilt * (F9 @ hilt); F9 /= np.linalg.norm(F9)
kn = chains['Index'][0] - chains['Pinky'][0]; kn /= np.linalg.norm(kn)
fo = chains['Middle'][1] - chains['Middle'][0] + chains['Ring'][1] - chains['Ring'][0]; fo -= kn * (fo @ kn); fo /= np.linalg.norm(fo)
Ro = np.array([kn, fo, np.cross(kn, fo)]).T; Rt = np.array([hilt, F9, np.cross(hilt, F9)]).T
CR['Bip01 R Hand'] = Rt @ Ro.T; CR['Bip01 L Hand'] = SM @ CR['Bip01 R Hand'] @ SM
ang = lambda R_: round(float(np.degrees(np.arccos(np.clip((np.trace(R_) - 1) / 2, -1, 1)))), 1)
rep['rest_turn_deg'] = {k: ang(v) for k, v in CR.items()}
print('TURNS', rep['rest_turn_deg'])
for s_ in 'RL':
    for name in FNAMES:
        for i in (1, 2, 3):
            CR[f'Bip01 {s_} {name}{i}'] = CR[f'Bip01 {s_} Hand']
    CR[f'Bip01 {s_} Finger0'] = CR[f'Bip01 {s_} Hand']; CR[f'{s_}Hand1'] = CR[f'Bip01 {s_} Hand']
CR['Bone01'] = CR['Bip01 R Hand']
I3 = np.eye(3)
JR = {}
FPAR = {}
for s_ in 'RL':
    for name in FNAMES:
        FPAR[f'Bip01 {s_} {name}1'] = f'Bip01 {s_} Hand'
        FPAR[f'Bip01 {s_} {name}2'] = f'Bip01 {s_} {name}1'; FPAR[f'Bip01 {s_} {name}3'] = f'Bip01 {s_} {name}2'


def rest_of(n):
    if n in JR: return JR[n]
    par = FPAR.get(n) or (bones[n].parent.name if bones[n].parent else None)
    if par is None or n == 'Bip01 Pelvis':
        JR[n] = RJ(n) if n in bones else JF[n]
    else:
        JR[n] = rest_of(par) + CR.get(par, I3) @ (JF[n] - JF[par])
    return JR[n]


for n in list(bones.keys()) + list(FPAR):
    rest_of(n)
rep['rest_joints'] = {k: np.round(v, 4).tolist() for k, v in JR.items()}
for s_, sg in (('R', 1), ('L', -1)):
    print('REST', s_, {k: np.round(JR[f'Bip01 {s_} {k}'], 3).tolist() for k in ('UpperArm', 'Hand', 'Calf', 'Foot', 'Toe0')}, 'MM9 foot', np.round(RJ(f'Bip01 {s_} Foot'), 3))
# fingertips, for the tails
TIPS = {}
for name, jp in chains.items():
    TIPS[f'Bip01 R {name}3'] = JR[f'Bip01 R {name}3'] + CR['Bip01 R Hand'] @ (jp[3] - jp[2])
    TIPS[f'Bip01 L {name}3'] = JR[f'Bip01 L {name}3'] + CR['Bip01 L Hand'] @ (MIR(jp[3]) - MIR(jp[2]))

bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
ebs = rig.data.edit_bones
for n in bones.keys():
    if n in JR:
        eb = ebs[n]; d = Vector(IW @ Vector(JR[n])) - eb.head
        eb.head += d; eb.tail += d
for s_ in 'RL':
    for name in FNAMES:
        par = ebs[f'Bip01 {s_} Hand']
        for i in (1, 2, 3):
            eb = ebs.new(f'Bip01 {s_} {name}{i}')
            n = f'Bip01 {s_} {name}{i}'
            eb.head = IW @ Vector(JR[n])
            eb.tail = IW @ Vector(JR[f'Bip01 {s_} {name}{i + 1}'] if i < 3 else TIPS[n])
            eb.parent = par; eb.use_connect = False
            par = eb
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# weights
for g in list(body.vertex_groups): body.vertex_groups.remove(g)
n = len(co)
WT = {}                                                     # bone -> weight array


def add(bone, ids, w=1.0):
    WT.setdefault(bone, np.zeros(n))[ids] += w


def side_bone(p):
    return ('R', p) if p < 100 else ('L', p - 100)


rigid = {3: 'Thigh', 6: 'UpperArm', 36: 'UpperArm', 35: 'UpperArm', 17: 'UpperArm', 59: 'UpperArm', 23: 'Forearm',
         10: 'Forearm', 37: 'Calf'}
for p, b in rigid.items():
    add(f'Bip01 R {b}', np.where(pid == p)[0]); add(f'Bip01 L {b}', np.where(pid == p + 100)[0])
HEAD = [11, 15, 19, 21, 22, 26, 40, 45, 46, 54, 55, 63]
add('Bip01 Head', np.where(np.isin(pid, HEAD + [p + 100 for p in HEAD]) | (pid >= 200))[0])
add('Bip01 Spine3', np.where(pid == 8)[0])
add('Bip01 Spine', np.where(np.isin(pid, (9, 44)))[0])


def ramp(z, joints, soft):
    """Partition of unity along z over bones at the given heights, low to high."""
    zs = np.array([j[1] for j in joints]); out = np.zeros((len(z), len(joints)))
    out[:, 0] = 1
    for i in range(1, len(joints)):
        t = np.clip((z - zs[i] + soft) / (2 * soft), 0, 1); t = t * t * (3 - 2 * t)
        out[:, i] = t; out[:, :i] *= (1 - t)[:, None]
    return out


ids = np.where(pid == 0)[0]
js = [('Bip01 Spine', 0), ('Bip01 Spine1', T['Bip01 Spine1'][2]), ('Bip01 Spine2', T['Bip01 Spine2'][2])]
r = ramp(co[ids, 2], js, 0.035)
for i, j in enumerate(js): add(j[0], ids, 0); WT[j[0]][ids] += r[:, i]
ids = np.where(pid == 18)[0]
js = [('Bip01 Neck', 0), ('Bip01 Head', T['Bip01 Head'][2])]
r = ramp(co[ids, 2], js, 0.02)
for i, j in enumerate(js): add(j[0], ids, 0); WT[j[0]][ids] += r[:, i]
# boots
for s, p, m in (('R', 12, 1), ('L', 112, -1)):
    ids = np.where(pid == p)[0]
    js = [(f'Bip01 {s} Foot', 0), (f'Bip01 {s} Calf', ank_z + 0.02)]
    r = ramp(co[ids, 2], js, 0.05)
    for i, j in enumerate(js): add(j[0], ids, 0); WT[j[0]][ids] += r[:, i]
# skirt: belt -> thighs, one field of height and side
SK = [14, 16, 25, 30, 32, 33, 38, 41, 42, 47, 49, 50, 56, 57, 58, 60, 61, 65]
ids = np.where(np.isin(pid, SK))[0]
z = co[ids, 2]; x = co[ids, 0] - MID
drop = np.clip((0.02 - z) / 0.42, 0, 1); drop = drop * drop * (3 - 2 * drop)
left = np.clip((x + 0.11) / 0.22, 0, 1); left = left * left * (3 - 2 * left)
wmax = 0.8
add('Bip01 Spine', ids, 0); WT['Bip01 Spine'][ids] += 1 - wmax * drop
add('Bip01 L Thigh', ids, 0); WT['Bip01 L Thigh'][ids] += wmax * drop * left
add('Bip01 R Thigh', ids, 0); WT['Bip01 R Thigh'][ids] += wmax * drop * (1 - left)
# hands
for s, p, mir in (('R', 7, False), ('L', 107, True)):
    ids = np.where(pid == p)[0]
    add(f'Bip01 {s} Hand', ids, 1.0)
    hp = co[ids] * ([-1, 1, 1] if mir else [1, 1, 1]) + ([2 * MID, 0, 0] if mir else [0, 0, 0])
    for name, jp in chains.items():
        vo = set(verts_of[name].tolist()); Rv = co[verts_of[name]]
        jp2 = np.array(jp)
        for v_i, (vid, q) in enumerate(zip(ids, hp)):
            # a finger piece vertex, or a palm vertex within the web of its proximal joint
            d = np.linalg.norm(Rv - q, axis=1).min()
            inpiece = d < 1e-6
            segs = jp2[1:] - jp2[:-1]; L2 = (segs ** 2).sum(1)
            t = np.clip(((q - jp2[:-1]) * segs).sum(1) / L2, 0, 1)
            cl = jp2[:-1] + segs * t[:, None]; ds = np.linalg.norm(q - cl, axis=1)
            k = int(np.argmin(ds))
            if inpiece:
                w = np.zeros(3); w[k] = 1
                # 6 mm blend at the joints
                soft = 0.008
                L = np.sqrt(L2[k]); a = t[k] * L
                if k > 0 and a < soft:
                    f = 0.5 + 0.5 * a / soft; w[k] = f; w[k - 1] = 1 - f
                if k < 2 and L - a < soft:
                    f = 0.5 + 0.5 * (L - a) / soft; w[k] = f; w[k + 1] = 1 - f
            else:
                if ds[0] > 0.014 or t[0] > 0.6: continue
                base_d = t[0] * np.sqrt(L2[0])
                w = np.array([0.5 * (1 - ds[0] / 0.014), 0, 0])
            WT[f'Bip01 {s} Hand'][vid] -= w.sum()
            for i in range(3):
                if w[i] > 0:
                    add(f'Bip01 {s} {name}{i + 1}', [vid], w[i])
tot = sum(WT.values())
assert (tot > 0.99).all() and (tot < 1.01).all(), (tot.min(), tot.max(), np.unique(pid[(tot < .99) | (tot > 1.01)]))
for b, w in WT.items():
    g = body.vertex_groups.new(name=b)
    nz = np.where(w > 1e-3)[0]
    for lvl in np.unique(np.round(w[nz], 3)):
        g.add(nz[np.round(w[nz], 3) == lvl].tolist(), float(lvl), 'REPLACE')
# vertices to the MM9 bind; `fitco` keeps the HD pose for the upload
a_ = me.attributes.new('fitco', 'FLOAT_VECTOR', 'POINT'); a_.data.foreach_set('vector', co.ravel())
new = np.zeros_like(co)
for b, w in WT.items():
    nz = np.where(w > 0)[0]
    new[nz] += w[nz, None] * (JR[b] + (co[nz] - JF[b]) @ CR.get(b, I3).T)
bm_w = np.linalg.inv(np.array(body.matrix_world))
hom = np.c_[new, np.ones(len(new))] @ bm_w.T
me.vertices.foreach_set('co', hom[:, :3].ravel()); me.update()
print('REST bounds', new.min(0), new.max(0), 'height', new[:, 2].max() - new[:, 2].min())
body.parent = rig
m = body.modifiers.get('Armature') or body.modifiers.new('Armature', 'ARMATURE')
m.object = rig
rep['weights_bones'] = sorted(WT)
json.dump(rep, open(REP, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FIT done', len(me.polygons))
