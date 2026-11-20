"""hkr gate G6-armour: rigid plates against the skinned body (and each other, and the carbine) on every frame of
every listed clip. Per plate (objects Arm_*, closed shells): body vertices inside the plate (signed nearest-face test
against the plate, inside when (p - nearest) . n < -0.5 d), body vertices of the plate's excluded parts (spikes
grown through the plate by design: the plate spec's exclude_bones / exclude_pieces) skipped; plate vertices inside the
body (same test against the body, the closed skin); plate vertices inside another plate; carbine vertices inside a
plate. Candidate body vertices = within PRE (8 cm) of the plate at rest. Reports the deepest value (cm) and its frame
per clip and plate in review/armour_gate_<tag>.json. Pass: everything <= TOL (0.3 cm).
Args: -- <blend> <tag> <spec json> <clip> [...]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
blend, tag, specp, clips = a[0], a[1], a[2], a[3:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE, TOL = float(os.environ.get('PRE', '0.08')), float(os.environ.get('TOL', '0.003'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
SPECJ = json.load(open(specp)); SPEC = {p['name']: p for p in SPECJ['plates']}
FSTEP = int(os.environ.get('FSTEP', '1'))                 # iteration aid: every FSTEP-th frame (the gate itself uses 1)
ONLY = set(os.environ['ONLY'].split(',')) if os.environ.get('ONLY') else None   # iteration aid: only these plates
ATLAS = SPECJ.get('atlas', 1024)
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
plates = sorted([o for o in bpy.data.objects if o.name.startswith(('Arm_','Cuff_'))], key=lambda o: o.name)
gun = bpy.data.objects.get('Rifle')
me = body.data; nv = len(me.vertices)
PIECE = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', PIECE)
GI = {g.index: g.name for g in body.vertex_groups}
DOM = np.array([GI[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices])
BF = [tuple(p.vertices) for p in me.polygons]
# skinned shell (Trooper caste): the skin under a shell piece's interior is deleted in the export (skin_shell.py), so it
# neither pokes through nor holds a plate up: hidden vertices are no candidates, a plate inside the body counts only
# where the nearest skin face is kept
HID = np.zeros(len(me.vertices), np.int32)
if 'shell_hidden' in me.attributes: me.attributes['shell_hidden'].data.foreach_get('value', HID)
HIDF = {k for k, f in enumerate(BF) if all(HID[i] for i in f)}
# hidden loose pieces (the chest ornament under the cuirass) are not in the Trooper mesh at all: out of the body test
# (the main skin's hidden faces stay, they keep the skin closed for the ray parity, and are skipped as nearest faces)
KEEPF = [k for k, f in enumerate(BF) if not (k in HIDF and PIECE[f[0]] != 0)]
BFK = [BF[k] for k in KEEPF]
HIDFK = {j for j, k in enumerate(KEEPF) if k in HIDF}


def ev(ob):
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co)
    faces = [tuple(p.vertices) for p in m.polygons]; e.to_mesh_clear()
    co = co.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)
    return co, faces


# five directions, majority vote: with three, a point in the ring the arms, fist and carbine make in front of the
# chest could read inside (Hit 0.19 s: a cuirass vertex 6 cm from any skin)
DIRS = [Vector(d).normalized() for d in ((0.0123, 0.0217, 1.0), (0.71, -0.33, -0.62), (-0.55, 0.81, 0.2),
                                         (0.12, -0.97, 0.21), (-0.83, -0.18, -0.52))]


def parity(tree, p, maxd=1.0):
    """inside a closed mesh: an odd number of crossings along a ray (majority of three directions)"""
    votes = 0
    for d in DIRS:
        o = Vector(p); n = 0; travelled = 0.0
        while travelled < maxd:
            loc, nrm, fi, dist = tree.ray_cast(o, d, maxd - travelled)
            if loc is None: break
            n += 1; travelled += dist + 1e-5; o = loc + d * 1e-5
        votes += n % 2
    return votes * 2 > len(DIRS)


def inside_closed(tree, pts, maxd=0.5, skipf=()):
    best, arg = 0.0, -1
    for k, p in enumerate(pts):
        loc, n, fi, d = tree.find_nearest(Vector(p), 0.06)
        if loc is None or d <= best or fi in skipf: continue
        # inside = both tests agree: the nearest face's normal points away (signed nearest) and a ray parity
        # (each alone gave false positives: holes and fused spikes break the nearest test, seam splits the parity)
        if (Vector(p) - loc).dot(n) < 0 and parity(tree, p, maxd):
            best, arg = d, k
    return best, arg


def through_depth(tree, pts):
    """skin points beyond a plate's inner surface (inner faces' normals point to the body): nearest point on the
    inner surface, the offset against its normal and within 25 deg of it (the point lies over the plate)"""
    best, arg = 0.0, -1
    for k, p in enumerate(pts):
        loc, n, fi, d = tree.find_nearest(Vector(p), 0.03)   # a poke reaches at most the outer surface + 1.5 cm
        if loc is None or d <= best: continue
        v = Vector(p) - loc
        if v.dot(n) < -0.9 * v.length:
            best, arg = d, k
    return best, arg


def inside_depth(tree, pts, faces=None):
    best, arg = 0.0, -1
    for k, p in enumerate(pts):
        loc, n, fi, d = tree.find_nearest(Vector(p), 0.06)
        if loc is not None and (Vector(p) - loc).dot(n) < -0.5 * d and d > best:
            best, arg = d, (k if faces is None else fi)
    return best, arg


rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
B0, _ = ev(body)
REST_P = {}
cand, pfaces, bfaces, ifaces = {}, {}, {}, {}
PV = {}
for pl in plates:
    P0, F = ev(pl); REST_P[pl.name] = P0
    F = [tuple(p.vertices) for p in pl.data.polygons if p.material_index == 0]; pfaces[pl.name] = F
    uvd = pl.data.uv_layers[0].data; DK = (1 - 12 / ATLAS)   # make_armour's dark strip
    inner = [tuple(p.vertices) for p in pl.data.polygons if p.material_index == 0 and
             all(abs(uvd[li].uv[0] - DK) < 1e-3 for li in p.loop_indices)]
    ifaces[pl.name] = inner
    PV[pl.name] = np.array(sorted({k for f in F for k in f}), int)
    t = BVHTree.FromPolygons(P0.tolist(), F)
    spec = SPEC.get(pl.name[4:], {})
    xb, xp = set(spec.get('exclude_bones', [])), set(spec.get('exclude_pieces', []))
    ok = ~(np.isin(DOM, list(xb)) | np.isin(PIECE, list(xp))) & (HID == 0)
    for b_ in [b for b in xb if b.startswith('Bone_') and b in body.vertex_groups]:   # the spike roots (blended into the shoulder) belong to the spike
        gi_ = body.vertex_groups[b_].index
        ok &= np.array([not any(g.group == gi_ and g.weight > 0.05 for g in v.groups) for v in me.vertices])
    c = [i for i in np.nonzero(ok)[0] if t.find_nearest(Vector(B0[i]), PRE)[0] is not None]
    cand[pl.name] = np.array(c, int)
    bfaces[pl.name] = BF
BONE = {pl.name: pl.get('bone', pl.vertex_groups[0].name) for pl in plates}
# v2: the arms against the cuirass and the leg plates (the torso plates exclude the arm skin from their candidates, so
# an arm crossing the chest went unmeasured): arm, hand and finger skin inside a torso or leg plate per frame
TORSO_BONES = {'B_Spine2', 'B_Spine1', 'B_Spine', 'B_Pelvis', 'B_Groin', 'B_L_Thigh', 'B_R_Thigh', 'B_L_Calf', 'B_R_Calf'}
ARMV = np.nonzero(np.array([any(t in d for t in ('UpperArm', 'Forearm', 'Hand', 'Finger')) for d in DOM]) & (HID == 0))[0]
# rigid together: the cap, tier B's carapace (never worn with the ivory cap) and the spikes on the pauldron's overlay nodes
OVERLAY = [{f'B_{s}_{x}', f'B_{s}_{y}'} for s in 'LR' for x, y in (('Pauldron', 'Carapace'), ('Pauldron', 'Spikes'), ('Carapace', 'Spikes'))]
FULLB = BVHTree.FromPolygons(B0.tolist(), BFK)
BASE_SKIN, BASE_PLATE = {}, {}
for pl in plates:
    P0, _ = ev(pl); t = BVHTree.FromPolygons(P0.tolist(), pfaces[pl.name])
    ti = BVHTree.FromPolygons(P0.tolist(), ifaces[pl.name])
    BASE_SKIN[pl.name] = np.array([i for i in cand[pl.name] if not parity(t, B0[i], 0.5) and through_depth(ti, B0[i:i + 1])[0] == 0], int)
    BASE_PLATE[pl.name] = np.array([k for k in PV[pl.name] if not parity(FULLB, P0[k], 0.8)], int)
    print('BASELINE', pl.name, 'skin verts inside at rest', len(cand[pl.name]) - len(BASE_SKIN[pl.name]),
          'plate verts inside the body at rest', len(PV[pl.name]) - len(BASE_PLATE[pl.name]))
cand = BASE_SKIN
rep = {}
for clip in clips:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    worst = {}
    for f in list(range(f0, f1 + 1, FSTEP)) + ([f1] if (f1 - f0) % FSTEP else []):
        sc.frame_set(f)
        B, _ = ev(body); BL = B.tolist()
        PL = {pl.name: ev(pl)[0] for pl in plates}
        PT = {n: BVHTree.FromPolygons(PL[n].tolist(), pfaces[n]) for n in PL}
        G = ev(gun)[0] if gun is not None else None
        for n in PL:
            if ONLY and n.removeprefix('Arm_') not in ONLY: continue
            ti = BVHTree.FromPolygons(PL[n].tolist(), ifaces[n])
            d1, k1 = through_depth(ti, B[cand[n]]) if len(cand[n]) else (0.0, -1)
            d1b, k1b = inside_closed(PT[n], B[cand[n]]) if len(cand[n]) else (0.0, -1)
            if d1b > d1: d1, k1 = d1b, k1b
            btree = BVHTree.FromPolygons(BL, BFK)
            # the body is large: 0.5 m rays ended inside an arm held in front of the chest (odd count, false 4-6 cm)
            d2, k2 = inside_closed(btree, PL[n][BASE_PLATE[n]], 1.2, HIDFK)
            part = None
            if k2 >= 0:
                fi2 = btree.find_nearest(Vector(PL[n][BASE_PLATE[n]][k2]))[2]; part = DOM[BFK[fi2][0]]
            d3 = 0.0; who = ''; k3 = -1
            for m in PL:
                if m == n or BONE[m] == BONE[n] or {BONE[m], BONE[n]} in OVERLAY: continue
                d, kk = inside_closed(PT[m], PL[n][PV[n]])
                if d > d3: d3, who, k3 = d, m, kk
            d4, k4 = inside_closed(PT[n], G) if G is not None else (0.0, -1)
            d5 = 0.0; who5 = None
            if BONE[n] in TORSO_BONES:
                lo_, hi_ = PL[n].min(0) - 0.01, PL[n].max(0) + 0.01
                near = ARMV[np.all((B[ARMV] > lo_) & (B[ARMV] < hi_), axis=1)]
                if len(near):
                    d5, k5 = inside_closed(PT[n], B[near])
                    who5 = DOM[near[k5]] if k5 >= 0 else None
            r1 = B0[cand[n][k1]] if k1 >= 0 else None
            r2 = REST_P[n][BASE_PLATE[n][k2]] if k2 >= 0 else None
            r3 = REST_P[n][PV[n][k3]] if k3 >= 0 else None
            r5 = B0[near[k5]] if d5 > 0 and k5 >= 0 else None
            for key, val, extra, rp in (('skin_in_plate', d1, DOM[cand[n][k1]] if k1 >= 0 else None, r1),
                                        ('plate_in_skin', d2, part, r2), ('plate_in_plate', d3, who, r3),
                                        ('carbine_in_plate', d4, None, [round(x, 3) for x in gun.data.vertices[k4].co] if k4 >= 0 else None), ('arm_in_plate', d5, who5, r5)):
                w = worst.setdefault(n, {}).setdefault(key, [0.0, None, None, None])
                if val > w[0]: worst[n][key] = [val, f, extra, None if rp is None else [round(float(x), 3) for x in rp]]
    rep[clip] = {n: {k: [round(v[0] * 100, 2), v[1], v[2], v[3]] for k, v in d.items()} for n, d in worst.items()}
    bad = {n: {k: v for k, v in d.items() if v[0] > TOL * 100} for n, d in rep[clip].items()}
    bad = {n: d for n, d in bad.items() if d}
    print('ARMGATE', clip, 'FAIL' if bad else 'PASS', json.dumps(bad)[:1500])
json.dump(rep, open(os.path.join(HERE, 'review', f'armour_gate_{tag}.json'), 'w'), indent=1)
