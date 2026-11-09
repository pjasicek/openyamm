"""hkr skinned armour shell (Trooper caste, 2026-10-22): the plates whose spec entry has `shell` (armour_spec_v3.py)
are skinned instead of riding one bone. Per piece (object Arm_<name>, built by make_armour.py as an NV x NU grid:
outer surface vertices first, then the inner surface, then glow strips and studs):
- each inner grid node takes the body's weights at its nearest point on the skin under the piece (barycentric over the
  nearest face; the same skin selection as the projection: exclude/include bones and pieces); the outer node takes
  its inner node's weights (the thickness never changes), glow strips and studs their nearest outer node's;
- only deforming B_* joints count (no tail, jaw, chest-ornament or spike bones; `shell.bones` narrows a piece further);
  the weights are smoothed over the grid (SMOOTH Jacobi passes) and blended toward the piece's mean by `rigid`, so a
  piece moves like armour and the bending happens in the gaps between pieces; at most 4 influences, normalised;
- the skin under each piece's interior is flagged: a body vertex (main skin, piece 0, in the piece's skin selection)
  whose outward normal ray meets the piece's inner surface within REACH at least MARGIN (1.5 cm) inside its border
  (the rims keep covering skin); `shell.hide_pieces` hides whole loose mesh pieces lying under the piece. Body vertex attribute `shell_hidden` = 1 + the piece's index (0 = kept);
  export_hkr.py MODE=trooper deletes the faces whose vertices are all hidden (the bare base keeps the full skin).
Run after make_armour.py and again after twist_bones.py (the twist bones then carry the forearm and upper-arm plates).
Args: -- <in blend> <spec json> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
src, specp, out = a[0], a[1], a[2]
SMOOTH, REACH, PRUNE = int(os.environ.get('SMOOTH', '12')), float(os.environ.get('REACH', '0.09')), 0.03
MARGIN = float(os.environ.get('MARGIN', '0.015'))      # hidden skin stays this far inside the piece's border
SPEC = json.load(open(specp))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
nv = len(me.vertices)
CO = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
NRM = np.array([tuple((body.matrix_world.to_3x3() @ v.normal).normalized()) for v in me.vertices])
names = [g.name for g in body.vertex_groups]; W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
DOM = [names[int(np.argmax(W[i]))] if W[i].any() else '' for i in range(nv)]
PIECE = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', PIECE)
FACES = [tuple(p.vertices) for p in me.polygons]
hidden = np.zeros(nv, np.int32)
report = {}
shells = [p for p in SPEC['plates'] if p.get('shell')]
for si, pl in enumerate(shells):
    ob = bpy.data.objects['Arm_' + pl['name']]; pm = ob.data
    NU, NV = pl.get('nu', 9), pl.get('nv', 8); G = NU * NV
    xb = set(pl.get('exclude_bones', [])) | set(SPEC.get('exclude_bones_all', [])); xp = set(pl.get('exclude_pieces', []))
    keep = np.array([not (DOM[i] in xb or PIECE[i] in xp) for i in range(nv)])
    if pl.get('include_bones'):
        ib = set(pl['include_bones']); keep &= np.array([DOM[i] in ib for i in range(nv)])
    kf = [f for f in FACES if all(keep[k] for k in f)]
    tree = BVHTree.FromPolygons([tuple(c) for c in CO], kf)
    P = np.array([tuple(ob.matrix_world @ v.co) for v in pm.vertices])
    inner = P[G:2 * G]
    Wg = np.zeros((G, len(names)))
    for k, p in enumerate(inner):
        loc, n, fi, d = tree.find_nearest(Vector(p))
        f = kf[fi]; tri = CO[list(f)]
        # barycentric weights of the nearest point over the face's first triangle fan (quads/ngons: nearest corner fan)
        best = None
        for t in range(1, len(f) - 1):
            A, B, C = tri[0], tri[t], tri[t + 1]
            v0, v1, v2 = B - A, C - A, np.array(loc) - A
            d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
            den = d00 * d11 - d01 * d01
            if abs(den) < 1e-14: continue
            bv = (d11 * d20 - d01 * d21) / den; bw = (d00 * d21 - d01 * d20) / den; bu = 1 - bv - bw
            err = -min(bu, bv, bw, 0.0)
            if best is None or err < best[0]: best = (err, (0, t, t + 1), np.clip([bu, bv, bw], 0, 1))
        idx, bary = best[1], best[2] / best[2].sum()
        Wg[k] = sum(b * W[f[i]] for b, i in zip(bary, idx))
    # only the deforming B_* joints (no tail, jaw, chest-ornament or spike bones), optionally a per-piece whitelist
    allow = np.array([n.startswith('B_') and (not pl['shell'].get('bones') or n in pl['shell']['bones']) for n in names])
    Wg[:, ~allow] = 0.0
    nb = list(names).index(pl['bone']) if pl['bone'] in names else None
    zero = Wg.sum(1) <= 1e-9
    if zero.any() and nb is not None: Wg[zero, nb] = 1.0
    Wg /= Wg.sum(1, keepdims=True)
    Wg = Wg.reshape(NV, NU, -1)
    for it in range(SMOOTH):
        Q = Wg.copy()
        Q[1:-1] = 0.5 * Wg[1:-1] + 0.25 * (Wg[:-2] + Wg[2:])
        Q2 = Q.copy(); Q2[:, 1:-1] = 0.5 * Q[:, 1:-1] + 0.25 * (Q[:, :-2] + Q[:, 2:])
        Wg = Q2
    R = float(pl['shell'].get('rigid', 0.6))
    Wg = (1 - R) * Wg + R * Wg.reshape(G, -1).mean(0)
    Wg = Wg.reshape(G, -1)
    if pl['name'] == 'back_low':
        Wg *= .6
        Wg[:, names.index('B_Spine')] += .4
    Wg[Wg < PRUNE] = 0.0
    for k in range(G):
        o = np.argsort(-Wg[k]); Wg[k, o[4:]] = 0.0
    Wg /= Wg.sum(1, keepdims=True)
    Wv = np.zeros((len(P), len(names)))
    Wv[:G] = Wg; Wv[G:2 * G] = Wg
    if len(P) > 2 * G:
        outer = P[:G]
        for k in range(2 * G, len(P)):
            Wv[k] = Wg[int(np.argmin(np.linalg.norm(outer - P[k], axis=1)))]
    for g in list(ob.vertex_groups): ob.vertex_groups.remove(g)
    used = np.nonzero(Wv.sum(0) > 0)[0]
    for gi in used:
        vg = ob.vertex_groups.new(name=names[gi])
        for k in np.nonzero(Wv[:, gi] > 0)[0]:
            vg.add([int(k)], float(Wv[k, gi]), 'REPLACE')
    ob['shell'] = 1
    # hidden skin: rays along the skin normal onto the interior cells of the inner surface
    # the inner surface's border loop (grid order), for the MARGIN test of each ray hit
    loop = [(0, j) for j in range(NU - 1)] + [(i, NU - 1) for i in range(NV - 1)] + \
           [(NV - 1, j) for j in range(NU - 1, 0, -1)] + [(i, 0) for i in range(NV - 1, 0, -1)]
    BA = np.array([inner[i * NU + j] for i, j in loop]); BB = np.roll(BA, -1, axis=0)

    def to_border(q):
        d = BB - BA; t = np.clip(((q - BA) * d).sum(1) / np.maximum((d * d).sum(1), 1e-12), 0, 1)
        return float(np.min(np.linalg.norm(BA + d * t[:, None] - q, axis=1)))
    inf_ = [tuple(p.vertices) for p in pm.polygons if all(G <= x < 2 * G for x in p.vertices)]
    intf = inf_
    n_h = 0
    it_ = BVHTree.FromPolygons([tuple(c) for c in P], inf_)
    for i in np.nonzero(keep & (PIECE == 0))[0]:
        loc, n, fi, d = it_.ray_cast(Vector(CO[i]) - Vector(NRM[i]) * 0.002, Vector(NRM[i]), REACH)
        if loc is not None and hidden[i] == 0 and to_border(np.array(loc)) >= MARGIN:
            hidden[i] = si + 1; n_h += 1
    for pc in pl['shell'].get('hide_pieces', []):           # whole loose pieces under the piece (chest ornament)
        sel = (PIECE == pc) & (hidden == 0); hidden[sel] = si + 1; n_h += int(sel.sum())
    top = sorted(((float(Wg[:, gi].mean()), names[gi]) for gi in used), reverse=True)[:4]
    report[pl['name']] = {'bones': [(b, round(w, 2)) for w, b in top], 'hidden_skin_verts': n_h, 'interior_faces': len(intf)}
    print('SHELL', pl['name'], json.dumps(report[pl['name']]))
att = me.attributes.get('shell_hidden') or me.attributes.new('shell_hidden', 'INT', 'POINT')
att.data.foreach_set('value', hidden.tolist())
hf = sum(1 for f in FACES if all(hidden[k] for k in f))
print('SHELLHIDE verts', int((hidden > 0).sum()), 'faces fully hidden', hf, 'of', len(FACES))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
