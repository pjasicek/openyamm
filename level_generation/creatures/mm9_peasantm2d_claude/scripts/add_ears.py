"""PeasantM2d (mm9_peasantm2d_claude) = PeasantM2's approved body + elf ears. Adapted from mm9_peasantm7d_claude/scripts/add_ears.py
for PeasantM2's master (face attributes `mat` 2 = head set, `part` 20 face shell / 21 hair; head mirror-symmetric about x = 0;
UV layers HeadUV, PartUV (head faces = HeadUV), UVMap (body upload: head faces collapsed on one point), MHUV). Ear faces get
mat 2, part 22, hand 0; HeadUV/PartUV islands in the free band at the bottom of the head set (v 0..0.072); UVMap = the head
faces' collapse point. Original M7d notes follow.

PeasantM7d = PeasantM7's body + elf ears (MM9: 4 % of the head vertices move up to 5.3 cm; the ear tips stand out of
the hair, out, back and up). Opens PeasantM7's approved master read-only, adds two procedural elf ears (a cupped leaf
with a rolled rim, as mm9_peasantf8_claude/scripts/assemble_pf.py) to the Body mesh and saves a NEW master for this
project. Nothing else changes: vertices, faces, weights, UVs and attributes of M7's mesh are kept as they are (the ear
faces are appended at the end).

Ears: rigid on `Bip01 Head` (weight 1), face attributes head=1 hand=0 ear=1 (side 1 = +x, 2 = -x), symmetric about the
face's midline (the eye shells' mean x: Meshy's head sits about 1 cm off the head bone). Root inside the skull, tip
placed from MM9's own PeasantM7D ear tip relative to its head (head bone offset applied). HeadUV: one island per ear
side (front cup / back) in the free band above the head islands (v 0.81..0.995, u < 0.79; the hand squares are at
u >= 0.8), at the head's own texel density x DENS. UVMap/MHUV get the HeadUV value (unused for head faces).

Then writes the head upload for the head retextures: every head face (head=1, hand=0), ears included, with UV = HeadUV
exactly (scale 1, unlike M7's texpass upload at HeadUV / 0.8: the ears need the band above), static, no materials.

Args (Blender): <M7 master blend> <out blend> <upload glb> [key=value ...] keys: len, width, root, tip, dens, tilt
"""
import bpy, bmesh, sys, os, json
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, UPLOAD = argv[:3]
opt = dict(a.split('=', 1) for a in argv[3:])
f3 = lambda s: np.array([float(x) for x in s.split(',')])
# ear root and tip in the face-midline frame (x = distance from the midline, +x side; mirrored for -x)
ROOT = f3(opt.get('root', '0.074,0.030,0.776'))
TIP = f3(opt.get('tip', '0.140,0.068,0.858'))
EW = float(opt.get('width', '0.040'))          # widest ear width
DENS = float(opt.get('dens', '1.0'))
PRESS = opt.get('press', '0') == '1'            # v3: Meshy's human ears pressed into the skull (as PeasantF8)
FWD = float(opt.get('fwd', '0.45'))            # how much the cup faces forward (-y) as well as out
NU, NV = 12, 7
PY0, PY1, PZ0, PZ1 = (float(x) for x in opt.get('pressbox', '-0.022,0.055,0.735,0.815').split(','))

bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
nf0, nv0 = len(me.polygons), len(me.vertices)
hd = np.zeros(nf0, np.int32); hn = np.zeros(nf0, np.int32); prt = np.zeros(nf0, np.int32)
me.attributes['mat'].data.foreach_get('value', hd); hd = (hd == 2).astype(np.int32)
me.attributes['part'].data.foreach_get('value', prt)
P = np.array([v.co[:] for v in me.vertices])

MID = float(opt.get('mid', '0.0'))   # PeasantM2's head is mirror-symmetric about x = 0
eyes = []
pressed = 0
if PRESS:
    # v3 (2026-11-02): the face shell carries Meshy's small human ears at d 0.085-0.094 m from the midline, y -0.01..0.03,
    # z 0.76-0.85, just in front of the hair's side edge; with the elf ear behind them each side showed two ears. Each
    # vertex of the face shell (the largest head component) in that box takes at most the distance from the midline of
    # the cheek just in front of the ear (the shell's max at y -0.03..-0.012, same 2 cm height band) + 2 mm, faded over
    # 1 cm at the box edges, so the ear lies flat on the skull under the elf ear's root.
    fv = np.array(sorted({v for p in me.polygons if prt[p.index] == 20 for v in p.vertices}))
    Q = P[fv]; d = np.abs(Q[:, 0] - MID); sg = np.sign(Q[:, 0] - MID)
    newP = P.copy()
    for k, vi in enumerate(fv):
        y, z = Q[k, 1], Q[k, 2]
        if not (PY0 <= y <= PY1 and PZ0 <= z <= PZ1):
            continue
        ref = (sg == sg[k]) & (np.abs(Q[:, 2] - z) < 0.01) & (Q[:, 1] > -0.03) & (Q[:, 1] < -0.012)
        if not ref.any():
            continue
        cap = d[ref].max() + 0.002
        if d[k] <= cap:
            continue
        w = min(1.0, (y - PY0) / 0.01, (PY1 - y) / 0.01, (z - PZ0) / 0.01, (PZ1 - z) / 0.01)
        nd = d[k] + (cap - d[k]) * max(w, 0.0)
        newP[vi, 0] = MID + sg[k] * nd; pressed += 1
    # PeasantM2d: the pressed ear keeps its crumpled folds (helix, concha) as a flat relief that still reads as an ear in
    # profile and from below; SMOOTH iterations of Laplacian smoothing (face-shell edges) on the pressed vertices weighted
    # by their press weight relax it into the surrounding skin.
    NS = int(opt.get('smooth', '0'))
    if NS:
        pw = np.zeros(len(P)); 
        for k, vi in enumerate(fv):
            y, z = Q[k, 1], Q[k, 2]
            if PY0 <= y <= PY1 and PZ0 <= z <= PZ1:
                pw[vi] = max(0.0, min(1.0, (y - PY0) / 0.01, (PY1 - y) / 0.01, (z - PZ0) / 0.01, (PZ1 - z) / 0.01))
        fvs = set(fv.tolist()); nb = {int(v): set() for v in fv}
        for p in me.polygons:
            if prt[p.index] != 20: continue
            vs = list(p.vertices)
            for a_ in vs:
                nb[a_].update(b_ for b_ in vs if b_ != a_)
        act = [v for v in nb if pw[v] > 0]
        for _ in range(NS):
            cur = newP.copy()
            for v in act:
                if nb[v]:
                    avg = cur[list(nb[v])].mean(0); newP[v] = cur[v] + (avg - cur[v]) * 0.5 * pw[v]
    me.vertices.foreach_set('co', newP.ravel()); me.update(); P = newP

# head texel density (HeadUV area per 3D area over the head faces)
huv = me.uv_layers['HeadUV'].data
ua = aa = 0.0
for p in me.polygons:
    if hd[p.index] and prt[p.index] == 20:
        uv = np.array([huv[li].uv[:] for li in p.loop_indices]); co = P[list(p.vertices)]
        for k in range(1, len(uv) - 1):
            e1, e2 = uv[k] - uv[0], uv[k + 1] - uv[0]; ua += abs(e1[0] * e2[1] - e1[1] * e2[0]) / 2
            aa += np.linalg.norm(np.cross(co[k] - co[0], co[k + 1] - co[0])) / 2
S = np.sqrt(ua / aa) * DENS          # UV units per metre

# one ear (+x side) in the midline frame: u along root->tip, v across, cup on the front face
eu = TIP - ROOT; EL = np.linalg.norm(eu); eu /= EL
en = np.array([1.0, -FWD, 0.0]); en -= eu * (en @ eu); en /= np.linalg.norm(en)
ev = np.cross(en, eu); ev /= np.linalg.norm(ev)
uu = np.linspace(0, 1, NU); vv = np.linspace(-1, 1, NV)
V, G = [], []                         # vertices; (side, i, j)
for s, sgn in ((0, 1), (1, -1)):
    for i, u in enumerate(uu):
        wid = EW * (1 - u) ** 0.85 * (0.75 + 0.6 * u * (1 - u) * 4)
        th = 0.0055 * (1 - u) ** 0.7 + 0.0012
        for j, v in enumerate(vv):
            cup = 0.006 * (1 - v * v) * np.sin(np.pi * min(u * 1.1, 1)) if sgn > 0 else 0.0
            rim = 0.002 * np.exp(-((abs(v) - 1) / 0.3) ** 2) * (1 - u) if sgn > 0 else 0.0
            off = sgn * th * np.sqrt(max(1 - v * v, 0.0)) - cup + rim
            V.append(ROOT + eu * (u * EL) + ev * (v * wid * 0.5) + en * off); G.append((s, i, j))
V = np.array(V)
nf = NU * NV
tip = V[(NU - 1) * NV:nf].mean(0); V[(NU - 1) * NV:nf] = tip; V[nf + (NU - 1) * NV:] = tip
# grid UV per (side, i, j): an island EL x (max width) in metres
wmax = max(EW * (1 - u) ** 0.85 * (0.75 + 0.6 * u * (1 - u) * 4) for u in uu)
def guv(s, i, j):
    u = uu[i]; wid = EW * (1 - u) ** 0.85 * (0.75 + 0.6 * u * (1 - u) * 4)
    return np.array([u * EL, (vv[j] * wid * 0.5 + wmax * 0.5)]) * S
T, TU = [], []                        # triangles (vertex ids) and their UV island id
for s in (0, 1):
    for i in range(NU - 1):
        for j in range(NV - 1):
            a = s * nf + i * NV + j; b = a + 1; c = a + NV; d = c + 1
            T += [[a, b, d], [a, d, c]] if s == 0 else [[a, d, b], [a, c, d]]; TU += [s, s]
for i in range(NU - 1):               # side strips (front island UVs, pushed 3 px outward for the back vertices)
    for j in (0, NV - 1):
        a, c = i * NV + j, (i + 1) * NV + j; b, d = nf + a, nf + c
        T += [[a, c, d], [a, d, b]] if j == 0 else [[a, d, c], [a, b, d]]; TU += [2, 2]
T = np.array(T)

# islands: per ear, front and back side by side; ears one after the other along u in the band
pad = 6 / 2048
iw, ih = EL * S, wmax * S
U0, V0 = 0.004, 0.003
assert V0 + ih + 2 * pad < 0.072 and U0 + 4 * (iw + 2 * pad) < 0.99, (iw, ih, S)
def place(ear, s):
    return np.array([U0 + (2 * ear + s) * (iw + 2 * pad) + pad, V0 + pad])

bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.verify()
gi = body.vertex_groups['Bip01 Head'].index
lh, lk, lp = bm.faces.layers.int['mat'], bm.faces.layers.int['hand'], bm.faces.layers.int['part']
le = bm.faces.layers.int.get('ear') or bm.faces.layers.int.new('ear')
uvl = [bm.loops.layers.uv[n] for n in ('HeadUV', 'PartUV', 'MHUV')]
lbu = bm.loops.layers.uv['UVMap']
bm.faces.ensure_lookup_table()
f0 = next(f for f in bm.faces if f[lh] == 2)
COLLAPSE = tuple(f0.loops[0][lbu].uv); MIDX = f0.material_index
new_faces = 0
allnew = []
ear_faces = []
for ear, sx in ((0, 1.0), (1, -1.0)):
    W_ = V.copy(); W_[:, 0] = MID + sx * V[:, 0]
    vs = []
    for p in W_:
        v = bm.verts.new(p.tolist()); v[dl][gi] = 1.0; vs.append(v); allnew.append(v)
    for t, iu in zip(T, TU):
        if len({id(vs[k]) for k in t}) < 3 or len({tuple(np.round(W_[k], 7)) for k in t}) < 3:
            continue                  # collapsed at the tip
        ft = [vs[k] for k in t] if sx > 0 else [vs[k] for k in t[::-1]]
        try:
            f = bm.faces.new(ft)
        except ValueError:
            continue
        f[lh] = 2; f[lk] = 0; f[lp] = 22; f[le] = 1 + ear; f.material_index = MIDX; new_faces += 1; ear_faces.append(f)
        ks = t if sx > 0 else t[::-1]
        for l, k in zip(f.loops, ks):
            s, i, j = G[k]
            if iu == 2:               # strip: front island coordinate, back vertices 3 px out of the island
                q = guv(0, i, j) + (np.array([0, (1 if j else -1) * 3 / 2048]) if s == 1 else 0)
                q = q + place(ear, 0)
            else:
                q = guv(s, i, j) + place(ear, s)
            for ul in uvl:
                l[ul].uv = tuple(q)
            l[lbu].uv = COLLAPSE
bmesh.ops.remove_doubles(bm, verts=allnew, dist=1e-7)
# v4: outward normals (the see-through gate saw the ears' back faces from outside: the hand-built winding was inverted on
# at least one side). Each ear is a closed leaf after the tip merge.
ear_faces = [f for f in ear_faces if f.is_valid]
before = [f.normal.copy() for f in ear_faces]
bmesh.ops.recalc_face_normals(bm, faces=ear_faces)
flipped = sum(1 for f, n in zip(ear_faces, before) if f.normal.dot(n) < 0)
bm.to_mesh(me); bm.free(); me.update()
assert all(me.polygons[i].index == i for i in range(nf0))
rep = dict(ear_faces_flipped=flipped, pressed_ear_vertices=pressed, midline_x=round(MID, 4), ear_len=round(EL, 4), width=EW,
           root=ROOT.tolist(), tip=TIP.tolist(), uv_per_m=round(S, 3), island=[round(iw, 4), round(ih, 4)],
           new_faces=new_faces, faces=len(me.polygons), verts=len(me.vertices), old_faces=nf0, old_verts=nv0)
print('EARS', json.dumps(rep))
bpy.ops.wm.save_as_mainfile(filepath=OUT)

# head upload: head faces incl. ears, UV = HeadUV
n = len(me.polygons)
hd = np.zeros(n, np.int32); me.attributes['mat'].data.foreach_get('value', hd)
head = hd == 2
dup = body.copy(); dup.data = me.copy(); dup.modifiers.clear(); dup.parent = None
dup.matrix_world = body.matrix_world
bpy.context.scene.collection.objects.link(dup)
dm = dup.data
bm = bmesh.new(); bm.from_mesh(dm); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if not head[f.index]], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(dm); bm.free(); dm.update()
dup.vertex_groups.clear()
du, dh = dm.uv_layers['UVMap'].data, dm.uv_layers['HeadUV'].data
for li in range(len(dm.loops)):
    du[li].uv = dh[li].uv
for ln in [l.name for l in dm.uv_layers if l.name != 'UVMap']:
    dm.uv_layers.remove(dm.uv_layers[ln])
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
print('UPLOAD', UPLOAD, int(head.sum()), 'faces')
