"""Extract a boss's armour shell from a Meshy figure built from its painted masters, fitted onto the winged body.

1. Align: import the Meshy figure, try four yaws, normalise height, trimmed similarity ICP onto the body (wings
   excluded); then a damped per-bone rigid correction blended by the body's skin weights (the figure's limbs land on
   ours).
2. Classify each Meshy face: signed distance to the body surface and the painted masters' colour projected through
   the exact guide cameras (registration.json): gold/ivory/glow = armour, violet = skin.
3. Shell = armour faces outside the excluded regions (hands, feet, head unless allowed, wing roots), cleaned by a
   majority filter and island size; pushed to a minimum clearance; saved with a diagnostic colour attribute.

Usage (Blender): fit_shell.py <boss> <meshy.glb> [--allow-head] [--min-dist M] [--far M]
Writes work/<boss>/shell_fit.blend, work/<boss>/shell_fit.json."""
import bpy, bmesh, sys, json, math, argparse
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser()
ap.add_argument('boss'); ap.add_argument('meshy')
ap.add_argument('--allow-head', action='store_true')
ap.add_argument('--min-dist', type=float, default=-0.02)
ap.add_argument('--smooth', type=int, default=6)
ap.add_argument('--hole', type=int, default=80)
ap.add_argument('--far', type=float, default=0.022)
ap.add_argument('--clearance', type=float, default=0.005)
ap.add_argument('--rigid', action='append', default=[],
                help='NAME:BONE:xmin,xmax,ymin,ymax,zmin,zmax:min_sd  figure faces in the box farther than min_sd '
                     'from the body become a rigid add-on object Rigid_NAME (removed from the shell)')
ap.add_argument('--drop', action='append', default=[],
                help='xmin,xmax,ymin,ymax,zmin,zmax:min_sd  figure faces in the box farther than min_sd are dropped')
a = ap.parse_args(argv)
P = Path(__file__).resolve().parents[1]
W = P / 'work' / a.boss; W.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/base.blend'))
sc = bpy.context.scene
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()

# ---------------------------------------------------------------- body data (rest pose, world space)
bm_ = body.data
BV = np.array([tuple(body.matrix_world @ v.co) for v in bm_.vertices])
BN = np.array([tuple((body.matrix_world.to_3x3() @ v.normal).normalized()) for v in bm_.vertices])
gname = {g.index: g.name for g in body.vertex_groups}
nb = len(gname)
BW = np.zeros((len(BV), nb), np.float32)
for v in bm_.vertices:
    for g in v.groups:
        BW[v.index, g.group] = g.weight
BW /= np.maximum(BW.sum(1, keepdims=True), 1e-9)
wing = np.array([gname[i].startswith('B_Wing_') for i in range(nb)])
wv = BW[:, wing].sum(1)
# islands mostly on wing bones and spurs above the shoulders are not body
parent = np.arange(len(BV))
def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for e in bm_.edges:
    x, y = find(e.vertices[0]), find(e.vertices[1])
    if x != y:
        parent[x] = y
roots = np.array([find(i) for i in range(len(BV))])
headw = BW[:, [i for i in range(nb) if gname[i] in ('B_Head', 'B_Neck')]].sum(1)
notbody = wv > 0.25
for r in np.unique(roots):
    s = roots == r
    if wv[s].mean() > 0.3 or (BV[s, 2].mean() > 1.38 and headw[s].mean() < 0.2 and s.sum() < 400):
        notbody[s] = True
core_faces = [p.index for p in bm_.polygons if not any(notbody[i] for i in p.vertices)]
bmc = bmesh.new()
bmc.from_mesh(bm_)
bmc.transform(body.matrix_world)
bmc.faces.ensure_lookup_table()
keep = set(core_faces)
bmesh.ops.delete(bmc, geom=[f for f in bmc.faces if f.index not in keep], context='FACES')
body_bvh = BVHTree.FromBMesh(bmc)
core_v = np.flatnonzero(~notbody)
kd_body = KDTree(len(core_v))
for k, i in enumerate(core_v):
    kd_body.insert(BV[i], k)
kd_body.balance()
lo_b, hi_b = BV[core_v].min(0), BV[core_v].max(0)

# ---------------------------------------------------------------- Meshy figure
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(Path(a.meshy).resolve()))
new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
for o in bpy.data.objects:
    if o not in before and o.type != 'MESH':
        pass
bpy.ops.object.select_all(action='DESELECT')
for o in new:
    o.select_set(True)
bpy.context.view_layer.objects.active = new[0]
if len(new) > 1:
    bpy.ops.object.join()
fig = bpy.context.view_layer.objects.active
fig.name = 'Figure'
fig.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in [o for o in bpy.data.objects if o not in before and o != fig]:
    bpy.data.objects.remove(o, do_unlink=True)
wb = bmesh.new(); wb.from_mesh(fig.data)
bmesh.ops.remove_doubles(wb, verts=wb.verts, dist=1e-5)
wb.to_mesh(fig.data); wb.free(); fig.data.update()
FV0 = np.array([tuple(v.co) for v in fig.data.vertices])
print('FIGURE', len(FV0), 'verts', len(fig.data.polygons), 'faces')


def nearest_body(pts):
    out = np.zeros_like(pts); dist = np.zeros(len(pts)); nrm = np.zeros_like(pts); idx = np.zeros(len(pts), int)
    for i, p in enumerate(pts):
        loc, n, fi, d = body_bvh.find_nearest(Vector(p))
        out[i] = loc; dist[i] = d; nrm[i] = n; idx[i] = fi
    return out, dist, nrm, idx


def umeyama(src, dst, with_scale=True):
    ms, md = src.mean(0), dst.mean(0)
    s_, d_ = src - ms, dst - md
    U, S, Vt = np.linalg.svd(d_.T @ s_ / len(src))
    D = np.eye(3)
    if np.linalg.det(U @ Vt) < 0:
        D[2, 2] = -1
    Rm = U @ D @ Vt
    c = (S * np.diag(D)).sum() / (s_ ** 2).sum(1).mean() if with_scale else 1.0
    t = md - c * Rm @ ms
    return c, Rm, t


rng = np.random.default_rng(1)
best = None
for yaw in (0, 90, 180, 270):
    th = math.radians(yaw)
    Rz = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    V = FV0 @ Rz.T
    lo, hi = V.min(0), V.max(0)
    s = (hi_b[2] - lo_b[2]) / (hi[2] - lo[2])
    V = (V - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * s
    V += np.array([(lo_b[0] + hi_b[0]) / 2, (lo_b[1] + hi_b[1]) / 2, lo_b[2]])
    def rigid_icp(V, iters):
        for it in range(iters):
            sel = rng.choice(len(V), min(4000, len(V)), replace=False)
            q, d, _, _ = nearest_body(V[sel])
            k = d <= np.quantile(d, 0.5)
            c, Rm, t = umeyama(V[sel][k], q[k], with_scale=False)
            V = V @ Rm.T + t
        return V
    V = rigid_icp(V, 15)
    feet = np.array([V[:, 0].mean(), V[:, 1].mean(), V[:, 2].min()])
    best_s = None
    for sc_ in list(np.arange(0.88, 1.13, 0.03)):
        Vs = rigid_icp((V - feet) * sc_ + feet, 8)
        q, d, _, _ = nearest_body(Vs[rng.choice(len(Vs), 3000, replace=False)])
        sco = float(np.quantile(d, 0.35))
        if best_s is None or sco < best_s[0]:
            best_s = (sco, sc_)
    for sc_ in best_s[1] + np.array([-0.015, -0.0075, 0, 0.0075, 0.015]):
        Vs = rigid_icp((V - feet) * sc_ + feet, 8)
        q, d, _, _ = nearest_body(Vs[rng.choice(len(Vs), 3000, replace=False)])
        sco = float(np.quantile(d, 0.35))
        if sco <= best_s[0]:
            best_s = (sco, sc_)
    V = rigid_icp((V - feet) * best_s[1] + feet, 15)
    print('SCALE', yaw, round(float(best_s[1]), 4))
    q, d, _, _ = nearest_body(V[rng.choice(len(V), 4000, replace=False)])
    score = float(np.quantile(d, 0.5))
    print('YAW', yaw, 'median dist', round(score * 100, 2), 'cm')
    if best is None or score < best[0]:
        best = (score, yaw, V.copy())
score, yaw, FV = best

# ---------------------------------------------------------------- per-bone damped correction (twice)
def body_weights_at(pts):
    W_ = np.zeros((len(pts), nb), np.float32)
    for i, p in enumerate(pts):
        res = kd_body.find_n(Vector(p), 4)
        ws = 0
        for co, k, dd in res:
            w = 1.0 / max(dd, 1e-4)
            W_[i] += w * BW[core_v[k]]; ws += w
        W_[i] /= ws
    return W_


for rnd in range(2):
    FW = body_weights_at(FV)
    q, d, _, _ = nearest_body(FV)
    Ts = np.tile(np.eye(4), (nb, 1, 1))
    for b in range(nb):
        if wing[b]:
            continue
        sel = (FW[:, b] > 0.5) & (d < 0.03)
        if sel.sum() < 30:
            continue
        c, Rm, t = umeyama(FV[sel], q[sel], with_scale=False)
        ang = math.degrees(math.acos(max(-1, min(1, (np.trace(Rm) - 1) / 2))))
        lim = min(1.0, 12.0 / max(ang, 1e-6))
        # damp: slerp toward identity, clamp translation
        from mathutils import Matrix as M3
        qr = M3(Rm.tolist()).to_quaternion()
        qr = M3.Identity(3).to_quaternion().slerp(qr, 0.7 * lim)
        Rd = np.array(qr.to_matrix())
        cen = FV[sel].mean(0)
        tt = (q[sel].mean(0) - cen) * 0.7
        n_ = np.linalg.norm(tt)
        if n_ > 0.04:
            tt *= 0.04 / n_
        T = np.eye(4); T[:3, :3] = Rd; T[:3, 3] = cen + tt - Rd @ cen
        Ts[b] = T
    H = np.concatenate([FV, np.ones((len(FV), 1))], 1)
    out = np.zeros_like(FV)
    for b in range(nb):
        w = FW[:, b]
        if w.max() == 0:
            continue
        out += w[:, None] * (H @ Ts[b].T)[:, :3]
    FV = out
    q, d, _, _ = nearest_body(FV[rng.choice(len(FV), 4000, replace=False)])
    print('ROUND', rnd, 'median dist', round(float(np.median(d)) * 100, 2), 'cm')

np.savez(W / 'figure_map.npz', original=FV0, aligned=FV)
fig.data.vertices.foreach_set('co', FV.ravel())
fig.data.update()

# ---------------------------------------------------------------- signed distance and colour per vertex
q, dist, fn, _ = nearest_body(FV)
FWv = body_weights_at(FV)
sgn = np.sign(((FV - q) * fn).sum(1))
sd = dist * np.where(sgn == 0, 1, sgn)
cams = json.loads((P / 'references_hd/guides/cameras.json').read_text())['cameras']
reg = json.loads((P / 'references_hd' / a.boss / 'registration.json').read_text())


def load_rgba(path):
    im = bpy.data.images.load(str(path))
    w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    bpy.data.images.remove(im)
    return px.reshape(h, w, 4)[::-1].copy()  # top row first, as PIL


fig_bm = bmesh.new(); fig_bm.from_mesh(fig.data)
fig_bvh = BVHTree.FromBMesh(fig_bm)
fig.data.calc_normals_split() if hasattr(fig.data, 'calc_normals_split') else None
FN = np.array([tuple(v.normal) for v in fig.data.vertices])
armour_vote = np.zeros(len(FV)); skin_vote = np.zeros(len(FV)); wsum = np.zeros(len(FV))
col_acc = np.zeros((len(FV), 3))


def classify(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1); mn = rgb.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-6)
    hue = np.zeros_like(mx)
    dm = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / dm) % 6, np.where(mx == g, (b - r) / dm + 2, (r - g) / dm + 4)) * 60
    gold = (hue >= 18) & (hue <= 65) & (sat > 0.22) & (mx > 0.3)
    ivory = (sat < 0.28) & (mx > 0.62)
    hot = (mx > 0.85) & (sat > 0.4) & (hue < 45)
    violet_glow = (mx > 0.75) & (hue > 250) & (hue < 300) & (sat < 0.6)
    skin = ((hue >= 285) | (hue <= 12)) & (sat > 0.2) & (mx < 0.8) & ~violet_glow
    return (gold | ivory | hot | violet_glow).astype(float), skin.astype(float)


for view in ('01_front', '02_back', '03_left', '04_right'):
    cam = cams[view]; r = reg[view]
    img = load_rgba(P / 'references_hd' / a.boss / f'{view}.png')
    Hh, Ww = img.shape[:2]
    Mw = np.array(cam['matrix_world']); Mi = np.linalg.inv(Mw)
    pc = (np.concatenate([FV, np.ones((len(FV), 1))], 1) @ Mi.T)[:, :3]
    scale = cam['ortho_scale']
    px = Ww / 2 + pc[:, 0] / scale * Hh
    py = Hh / 2 - pc[:, 1] / scale * Hh
    piv = np.array(r['pivot_px'])
    mx_ = (px - piv[0]) * r['scale'] + piv[0] + r['dx_px']
    my_ = (py - piv[1]) * r['scale'] + piv[1] + r['dy_px']
    fwd = -Mw[:3, 2]  # camera looks along -Z
    facing = np.clip(-(FN @ fwd), 0, 1)
    ok = (facing > 0.15) & (mx_ >= 0) & (mx_ < Ww) & (my_ >= 0) & (my_ < Hh)
    for i in np.flatnonzero(ok):
        o = Vector(FV[i] - fwd * 0.012)
        hit = fig_bvh.ray_cast(o, Vector(-fwd), 5.0)
        if hit[0] is not None and hit[3] > 0.01:
            ok[i] = False
    ix = np.clip(mx_.astype(int), 0, Ww - 1); iy = np.clip(my_.astype(int), 0, Hh - 1)
    rgba = img[iy, ix]
    arm, sk = classify(rgba[:, :3])
    w = facing * ok * (rgba[:, 3] > 0.5)
    armour_vote += w * arm; skin_vote += w * sk; wsum += w
    col_acc += w[:, None] * rgba[:, :3]
# diffuse the votes over the mesh edges into unpainted vertices
E = np.array([tuple(e.vertices) for e in fig.data.edges])
for _ in range(25):
    for arr in (armour_vote, skin_vote, wsum):
        acc = np.zeros_like(arr); cnt = np.zeros_like(arr)
        np.add.at(acc, E[:, 0], arr[E[:, 1]]); np.add.at(acc, E[:, 1], arr[E[:, 0]])
        np.add.at(cnt, E[:, 0], 1); np.add.at(cnt, E[:, 1], 1)
        fill = wsum < 0.05
        arr[fill] = 0.5 * arr[fill] + 0.5 * acc[fill] / np.maximum(cnt[fill], 1)
armour_p = np.where(wsum > 1e-4, armour_vote / np.maximum(wsum, 1e-6), 0.5)
skin_p = np.where(wsum > 1e-4, skin_vote / np.maximum(wsum, 1e-6), 0.5)

print('DBG armour_p', np.percentile(armour_p,[10,25,50,75,90]).round(2), 'skin_p', np.percentile(skin_p,[10,25,50,75,90]).round(2))
print('DBG sd cm', (np.percentile(sd,[5,10,25,50,75,90,95])*100).round(2), 'wsum0', float((wsum==0).mean()))
_rgb = col_acc / np.maximum(wsum, 1e-6)[:, None]
print('DBG rgb sample', _rgb[np.random.default_rng(0).choice(len(_rgb), 8)].round(2).tolist())
# ---------------------------------------------------------------- face decision
def group_weight(names):
    idx = [i for i in range(nb) if any(gname[i].startswith(n) for n in names)]
    return FWv[:, idx].sum(1) if idx else np.zeros(len(FV))

hands = group_weight(['B_L_Hand', 'B_R_Hand', 'B_L_Finger', 'B_R_Finger'])
feet = group_weight(['B_L_Foot', 'B_R_Foot', 'B_L_Toe', 'B_R_Toe'])
head = group_weight(['B_Head'])
excluded = (hands > 0.5) | (feet > 0.5)
if not a.allow_head:
    excluded |= head > 0.5
else:
    excluded |= (head > 0.5) & (sd < 0.015)
# wing roots
for side in 'LR':
    for bn in (f'B_Wing_{side}_Root', f'B_Wing_{side}_Arm'):
        h = np.array(rig.matrix_world @ rig.data.bones[bn].head_local)
        excluded |= np.linalg.norm(FV - h, axis=1) < 0.06
margin = armour_p - skin_p
for _ in range(a.smooth):
    acc = np.zeros_like(margin); cnt = np.zeros_like(margin)
    np.add.at(acc, E[:, 0], margin[E[:, 1]]); np.add.at(acc, E[:, 1], margin[E[:, 0]])
    np.add.at(cnt, E[:, 0], 1); np.add.at(cnt, E[:, 1], 1)
    margin = 0.5 * margin + 0.5 * acc / np.maximum(cnt, 1)
vert_armour = ((margin > 0.0) & (sd > a.min_dist)) | (sd > a.far)
vert_armour &= ~excluded
faces = np.array([tuple(p.vertices) for p in fig.data.polygons], dtype=object)
F = np.array([list(p.vertices)[:3] for p in fig.data.polygons])
face_arm = vert_armour[F].mean(1) >= 0.5
print('DBG vert_armour', vert_armour.mean().round(3), 'excluded', excluded.mean().round(3), 'face_arm0', face_arm.mean().round(3))
# majority filter over face adjacency
fig_bm.faces.ensure_lookup_table()
adj = [[l.face.index for e in f.edges for l in e.link_loops if l.face.index != f.index] for f in fig_bm.faces]
adj = [[x for x in s if x != i] for i, s in enumerate(adj)]
for _ in range(6):
    nxt = face_arm.copy()
    for i, s in enumerate(adj):
        if s:
            m = np.mean(face_arm[s])
            if m > 0.66:
                nxt[i] = True
            elif m < 0.34:
                nxt[i] = False
    face_arm = nxt
print('DBG after majority', face_arm.mean().round(3))
# drop small islands
lab = -np.ones(len(face_arm), int); nl = 0
for i in np.flatnonzero(face_arm):
    if lab[i] >= 0:
        continue
    stack = [i]; lab[i] = nl
    while stack:
        j = stack.pop()
        for k in adj[j]:
            if face_arm[k] and lab[k] < 0:
                lab[k] = nl; stack.append(k)
    nl += 1
sizes = np.bincount(lab[lab >= 0], minlength=nl)
small = np.isin(lab, np.flatnonzero(sizes < 40))
face_arm &= ~small
# fill small skin holes enclosed by armour (not in excluded regions)
fex = excluded[F].mean(1) > 0.5
hl = -np.ones(len(face_arm), int); nh = 0
for i in np.flatnonzero(~face_arm & ~fex):
    if hl[i] >= 0:
        continue
    stack = [i]; hl[i] = nh; members = [i]; touches_ex = False
    while stack:
        j = stack.pop()
        for k in adj[j]:
            if fex[k]:
                touches_ex = True
            elif not face_arm[k] and hl[k] < 0:
                hl[k] = nh; stack.append(k); members.append(k)
    if len(members) < a.hole and not touches_ex:
        face_arm[members] = True
    nh += 1
def box_faces(spec):
    b, md = spec.split(':')
    x0, x1, y0, y1, z0, z1 = [float(v) for v in b.split(',')]
    inb = ((FV[:, 0] >= x0) & (FV[:, 0] <= x1) & (FV[:, 1] >= y0) & (FV[:, 1] <= y1) & (FV[:, 2] >= z0)
           & (FV[:, 2] <= z1) & (sd > float(md)))
    return inb[F].all(1)


rigid_faces = {}
for spec in a.rigid:
    name, bone, rest_ = spec.split(':', 2)
    sel = box_faces(rest_)
    # grow to whole connected pieces mostly inside the selection
    rigid_faces[(name, bone)] = sel
    face_arm &= ~sel
for spec in a.drop:
    face_arm &= ~box_faces(spec)
print('ARMOUR faces', int(face_arm.sum()), 'of', len(face_arm), 'islands', int((sizes >= 40).sum()))

# diagnostic colours on the figure (armour red, skin green, excluded blue)
ca = fig.data.color_attributes.new('diag', 'BYTE_COLOR', 'CORNER')
loop_v = np.zeros(len(fig.data.loops), int); fig.data.loops.foreach_get('vertex_index', loop_v)
loop_f = np.zeros(len(fig.data.loops), int)
for p in fig.data.polygons:
    loop_f[p.loop_start:p.loop_start + p.loop_total] = p.index
cols = np.where(face_arm[loop_f][:, None], [0.85, 0.15, 0.1, 1], [0.2, 0.7, 0.25, 1]).astype(float)
cols[excluded[loop_v]] = [0.2, 0.3, 0.9, 1]
ca.data.foreach_set('color', cols.ravel())
vp = fig.data.color_attributes.new('votes', 'FLOAT_COLOR', 'POINT')
vp.data.foreach_set('color', np.stack([armour_p, skin_p, np.clip(sd * 20 + 0.5, 0, 1), np.ones(len(FV))], 1).ravel())
pc_ = fig.data.color_attributes.new('paint', 'BYTE_COLOR', 'POINT')
pcol = np.concatenate([np.where(wsum[:, None] > 0, col_acc / np.maximum(wsum, 1e-6)[:, None], 0.5),
                       np.ones((len(FV), 1))], 1)
pc_.data.foreach_set('color', pcol.ravel())

# ---------------------------------------------------------------- shell object
shell_bm = bmesh.new(); shell_bm.from_mesh(fig.data); shell_bm.faces.ensure_lookup_table()
bmesh.ops.delete(shell_bm, geom=[f for f in shell_bm.faces if not face_arm[f.index]], context='FACES')
shell_me = bpy.data.meshes.new('Shell'); shell_bm.to_mesh(shell_me)
shell = bpy.data.objects.new('Shell', shell_me); sc.collection.objects.link(shell)
SV = np.array([tuple(v.co) for v in shell_me.vertices])
q2, d2, n2, _ = nearest_body(SV)
s2 = np.sign(((SV - q2) * n2).sum(1)); sd2 = d2 * np.where(s2 == 0, 1, s2)
push = sd2 < a.clearance
SV[push] = q2[push] + n2[push] * a.clearance
shell_me.vertices.foreach_set('co', SV.ravel()); shell_me.update()
for (name, bone), sel in rigid_faces.items():
    rb = bmesh.new(); rb.from_mesh(fig.data); rb.faces.ensure_lookup_table()
    bmesh.ops.delete(rb, geom=[f for f in rb.faces if not sel[f.index]], context='FACES')
    rme = bpy.data.meshes.new('Rigid_' + name); rb.to_mesh(rme); rb.free()
    for c in list(rme.color_attributes):
        rme.color_attributes.remove(c)
    ro = bpy.data.objects.new('Rigid_' + name, rme); sc.collection.objects.link(ro)
    ro['bone'] = bone
    print('RIGID', name, bone, len(rme.polygons), 'faces')
stats = {'boss': a.boss, 'yaw': yaw, 'median_fit_cm': round(score * 100, 2), 'figure_faces': len(F),
         'shell_faces': int(face_arm.sum()), 'pushed_vertices': int(push.sum()),
         'armour_islands': int((sizes >= 40).sum())}
(W / 'shell_fit.json').write_text(json.dumps(stats, indent=1))
print('STATS', stats)
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'shell_fit.blend'))
