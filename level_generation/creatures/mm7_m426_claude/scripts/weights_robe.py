"""Weight rules for the Moon Cleric (after build_rig.py) and the robe chain rig (adapted from the accepted MM8 Cleric,
mm8_m460_claude/scripts/robe_rig.py). Garments from prepare_rig.py.
- Rigid on B_Spine2: crescent (9), back rods/hooks/beads (11), banners (10), chest chain + pendant (7). The frame is
  one welded ornament in the native (it never moves against the back).
- Rigid on B_Head: helmet (pieces 3, 15), eyes (4), cheek plates (5). Hair (piece 11): Head above HAIR_HI, blending
  through B_Neck to B_Spine2 below HAIR_LO (it hangs down the back to the shoulder blades).
- Collar (6): Meshy's weights without arm bones (upper arm/forearm weight moved to the clavicle; playbook: no
  upper-arm weight on chest/neck).
- Hands (pieces 4, 5): 100 % B_*_Hand beyond the wrist plane, the forearm stub inside the sleeve blends from the
  forearm over the last FADE m. The claws never curl in the native: the fingers carry no weight.
- Robe: the skirt (2) and the robe top below the belt that is not sleeve (arm weight < 0.5) take NCH chains x 4 bones
  rooted on B_Pelvis at ZS[0] (ray-cast onto the outer robe surface, as m460); each vertex blends its two sector chains
  and two height bones linearly; above the waist it blends into B_Pelvis over WAIST. Rope ends (8) copy the weights of
  the nearest outer skirt vertex.
Writes work/rig_v2w.blend and scene['cloak_chains'] (read by robe_sim.py). Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; scene = bpy.context.scene
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([v.co[:] for v in me.vertices]); nv = len(co)
gv = np.array([a.value for a in me.attributes['garment'].data]); pv = np.array([a.value for a in me.attributes['piece'].data])
names = [g.name for g in body.vertex_groups]; gid = {n: i for i, n in enumerate(names)}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
J = lambda n: np.array(rig.data.bones[n].head_local)


def only(mask, bone):
    W[mask] = 0; W[mask, gid[bone]] = 1


only(np.isin(gv, (7, 9, 10, 11)), 'B_Spine2')
only(np.isin(gv, (3, 4, 5)), 'B_Head')
HAIR_LO, HAIR_HI = cfg.C.get('hair_z', [1.21, 1.33])
hair = gv == 12
z = co[hair, 2]
t = np.clip((z - HAIR_LO) / (HAIR_HI - HAIR_LO), 0, 1)
W[hair] = 0
W[hair, gid['B_Head']] = np.clip(t * 2 - 1, 0, 1)
W[hair, gid['B_Neck']] = 1 - np.abs(t * 2 - 1)
W[hair, gid['B_Spine2']] = np.clip(1 - t * 2, 0, 1)
for gcol in (6, 13):                                 # collar: no arm weight; mantle: arm share <= MANTLE_ARM
    col = gv == gcol
    keep = 0.0 if gcol == 6 else float(cfg.C.get('mantle_arm', 0.35))
    for s in ('L', 'R'):
        arm = sum(W[col, gid[f'B_{s}_{b}']] for b in ('UpperArm', 'Forearm', 'Hand'))
        over = np.maximum(arm - keep, 0) / np.maximum(arm, 1e-9)
        for b in ('UpperArm', 'Forearm', 'Hand'):
            W[col, gid[f'B_{s}_Clavicle']] += W[col, gid[f'B_{s}_{b}']] * over; W[col, gid[f'B_{s}_{b}']] *= 1 - over
# mantle (13): it hangs from the shoulders, so pelvis and leg weight go to B_Spine; then MANTLE_SMOOTH Jacobi passes
# inside the mantle shell only (no bleeding into the body): Meshy mixed pelvis, clavicle and arm weight along its lower
# edge and the arm swing tore it (4.6x in the sun cleric's attack)
mant = np.where(gv == 13)[0]
if len(mant):
    for n in [n for n in names if n == 'B_Pelvis' or any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe'))]:
        W[mant, gid['B_Spine']] += W[mant, gid[n]]; W[mant, gid[n]] = 0
    mset = set(mant.tolist()); mn = {}
    for e in me.edges:
        i, j = e.vertices
        if i in mset and j in mset:
            mn.setdefault(i, []).append(j); mn.setdefault(j, []).append(i)
    for it in range(int(cfg.C.get('mantle_smooth', 20))):
        Wn = W.copy()
        for i in mant:
            if i in mn:
                Wn[i] = 0.5 * W[i] + 0.5 * W[mn[i]].mean(0)
        W = Wn
    print('WEIGHTS mantle verts', len(mant), 'smoothed')
FADE = 0.025
for s in ('R', 'L'):
    wr, fa = J(f'B_{s}_Hand'), J(f'B_{s}_Forearm')
    m = cfg.hand_mask(co, pv, s, wr, fa, FADE)
    d = (wr - fa) / np.linalg.norm(wr - fa)
    a = np.clip(((co[m] - wr) @ d + FADE) / FADE, 0, 1)                   # 0 above the wrist - FADE, 1 beyond it
    W[m] = 0; W[m, gid[f'B_{s}_Hand']] = a; W[m, gid[f'B_{s}_Forearm']] = 1 - a
for pc, bone in cfg.C.get('rigid_pieces', {}).items():
    only(pv == int(pc), bone)

# torso: in the A-pose the hanging sleeves lie 1 cm from the robe sides below the armpit, so Meshy gave the torso above
# the belt up to 0.5 arm weight and a raised arm tore it (8x edge stretch in the cast). Below SPLIT_Z the robe top falls
# apart into the torso and two sleeves (connectivity); torso vertices lose their arm weight, ramped in from SPLIT_Z
# down over RAMP (the armpit junction keeps a smooth blend); the share goes to the trunk bones already on the vertex.
SPLIT_Z, RAMP = float(cfg.C.get('split_z', 1.065)), 0.05
ARMB0 = [gid[n] for n in names if any(t in n for t in ('UpperArm', 'Forearm', 'Hand'))]
TRUNK = [gid[n] for n in ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2')]
low = (gv == 1) & (co[:, 2] < SPLIT_Z)
adj = {}
for e in me.edges:
    i, j = e.vertices
    if low[i] and low[j]:
        adj.setdefault(i, []).append(j); adj.setdefault(j, []).append(i)
comp = -np.ones(nv, np.int32); ncomp = 0
for v0 in np.where(low)[0]:
    if comp[v0] >= 0:
        continue
    st = [int(v0)]
    while st:
        x = st.pop()
        if comp[x] >= 0:
            continue
        comp[x] = ncomp; st += adj.get(x, [])
    ncomp += 1
torso_c = {int(c) for c in set(comp[low & (np.abs(co[:, 0]) < 0.05)].tolist())} if low.any() else set()
tor = np.where(low & np.isin(comp, list(torso_c)))[0]
for i in tor:
    keep = float(np.clip((co[i, 2] - (SPLIT_Z - RAMP)) / RAMP, 0, 1))
    moved = W[i, ARMB0].sum() * (1 - keep)
    if moved <= 0:
        continue
    W[i, ARMB0] *= keep
    tw_ = W[i, TRUNK]
    if tw_.sum() > 1e-6:
        W[i, TRUNK] += moved * tw_ / tw_.sum()
    else:
        W[i, gid['B_Spine1']] += moved
# armpit smoothing (off by default: tried 12 passes, arm max stretch rose to 10-18x by bleeding arm weight into the
# torso): the torso rule leaves a step between the de-armed torso and the sleeve at the junction (the lying
# death and the casts still stretched those edges 3-6x); SMOOTH_IT Jacobi passes average every robe-top vertex in the
# armpit box with its edge neighbours (half own, half mean), all groups, sums kept
SMOOTH_IT, BOX_Z, BOX_X = int(os.environ.get('ARMPIT_SMOOTH', '0')), (SPLIT_Z - 0.07, 1.20), (0.05, 0.24)
nbr = {}
for e in me.edges:
    i, j = e.vertices
    if gv[i] == 1 and gv[j] == 1:
        nbr.setdefault(i, []).append(j); nbr.setdefault(j, []).append(i)
box = np.where((gv == 1) & (co[:, 2] > BOX_Z[0]) & (co[:, 2] < BOX_Z[1]) & (np.abs(co[:, 0]) > BOX_X[0]) & (np.abs(co[:, 0]) < BOX_X[1]))[0]
for it in range(SMOOTH_IT):
    Wn = W.copy()
    for i in box:
        if i in nbr:
            Wn[i] = 0.5 * W[i] + 0.5 * W[nbr[i]].mean(0)
    W = Wn
print('WEIGHTS armpit smoothing verts', len(box), 'passes', SMOOTH_IT)
# sleeves below the split (components other than the torso): only their own arm's bones. Meshy weighted the mage's
# long bell sleeves, hanging beside the robe, up to 0.48 to the pelvis, and the robe chains then claimed their hems
# (12x stretch at the sleeve hem in the cast)
sleeve = low & ~np.isin(comp, list(torso_c))
for i in np.where(sleeve)[0]:
    sd = 'L' if co[i, 0] > 0 else 'R'
    own = [gid[n] for n in names if n.startswith(f'B_{sd}_') and any(t in n for t in ('UpperArm', 'Forearm', 'Hand'))]
    tot = W[i, own].sum()
    if tot < 1e-6:
        own = [gid[f'B_{sd}_Forearm']]; W[i, own] = 1e-6; tot = 1e-6
    else:
        keep = W[i, own].copy(); armonly = np.zeros_like(W[i]); armonly[own] = keep / tot
        r = float(np.clip((SPLIT_Z - co[i, 2]) / RAMP, 0, 1))         # ramped in below the split (no step at the armpit)
        W[i] = W[i] * (1 - r) + armonly * r
SLEEVE = sleeve
print('WEIGHTS sleeve vertices below the armpit made arm-only', int(sleeve.sum()))
# centre line: no arm weight on the robe top within CENTRE_X of the spine line (Meshy put 0.5 left-upper-arm weight on
# the back centre under the mage's yoke); faded in to CENTRE_X + CENTRE_FADE, the share to the trunk bones
CENTRE_X, CENTRE_FADE = 0.06, 0.08
# off (tried on the mage: the step it leaves at the shoulders raised arm p99 by ~0.3 in every clip)
cen = np.where((gv == 1) & (np.abs(co[:, 0]) < CENTRE_X + CENTRE_FADE))[0] if cfg.C.get('centre_rule') else []
for i in cen:
    keep = float(np.clip((abs(co[i, 0]) - CENTRE_X) / CENTRE_FADE, 0, 1))
    moved = W[i, ARMB0].sum() * (1 - keep)
    if moved <= 1e-6:
        continue
    W[i, ARMB0] *= keep
    tw_ = W[i, TRUNK]
    if tw_.sum() > 1e-6:
        W[i, TRUNK] += moved * tw_ / tw_.sum()
    else:
        W[i, gid['B_Spine2']] += moved
# a cape fused to the body behind the arms (warlock): robe-top vertices behind the arm plane (y > CB_Y, faded over
# CB_F) lose their arm weight to the trunk (the cape behind the shoulder stretched 5x when the arm swung)
if 'cape_back_y' in cfg.C:
    CB_Y, CB_F = cfg.C['cape_back_y']
    cb = np.where((gv == 1) & (co[:, 1] > CB_Y - CB_F) & ~cfg.hand_mask(co, pv, 'L', J('B_L_Hand'), J('B_L_Forearm'), 0.05)
                  & ~cfg.hand_mask(co, pv, 'R', J('B_R_Hand'), J('B_R_Forearm'), 0.05))[0]
    def segd(p, a, b):
        ab = b - a; t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(p - (a + np.outer(t, ab)), axis=1)
    near_arm = np.zeros(len(cb), bool)
    for sd in 'LR':                                  # the arm's own skin (within ARM_R of its bones) is not cape
        sh, el, wr_ = J(f'B_{sd}_UpperArm'), J(f'B_{sd}_Forearm'), J(f'B_{sd}_Hand')
        near_arm |= (segd(co[cb], sh, el) < 0.065) | (segd(co[cb], el, wr_) < 0.055)
    cb = cb[~near_arm]
    for i in cb:
        r = float(np.clip((co[i, 1] - (CB_Y - CB_F)) / CB_F, 0, 1))
        moved = W[i, ARMB0].sum() * r
        if moved <= 1e-6:
            continue
        W[i, ARMB0] *= 1 - r
        tw_ = W[i, TRUNK]
        if tw_.sum() > 1e-6:
            W[i, TRUNK] += moved * tw_ / tw_.sum()
        else:
            W[i, gid['B_Spine2']] += moved
    print('WEIGHTS cape behind the arms', len(cb))
print('WEIGHTS torso below the armpit', len(tor), 'of', int(low.sum()), 'robe-top verts below', SPLIT_Z, 'components', ncomp)

# ---------------------------------------------------------------- robe chains
ARMB = [gid[n] for n in names if any(t in n for t in ('UpperArm', 'Forearm', 'Hand'))]
_wz = float(cfg.C.get('waist_z', 0.90))
ZS = [_wz] + [round(_wz - (_wz - 0.02) * k / 4, 4) for k in (1, 2, 3, 4)]
WAIST = (_wz - 0.04, _wz + 0.03)       # chains below WAIST[0], B_Pelvis above WAIST[1]
NCH = int(cfg.C.get('nch', os.environ.get('NCH', '14')))    # 14 x 4 robe bones + 2 x 2 x 3 banner bones keep the skin within 128 joints
HANDV = cfg.hand_mask(co, pv, 'L', J('B_L_Hand'), J('B_L_Forearm'), 0.03) | cfg.hand_mask(co, pv, 'R', J('B_R_Hand'), J('B_R_Forearm'), 0.03)
# legs modelled inside a fused gown (warlock): a skirt-region vertex whose outward (radial) ray hits the shell again is
# inside the gown -> a real leg: Meshy's leg weights are kept (they move the bare feet) and it is not a robe vertex
INNER_LEG = np.zeros(nv, bool)
if cfg.C.get('inner_legs'):
    allf = [tuple(f.vertices) for f in me.polygons]
    tr = BVHTree.FromPolygons(co.tolist(), allf)
    pel_ = J('B_Pelvis')
    for i in np.where(gv == 2)[0]:
        d = Vector((co[i, 0] - pel_[0], co[i, 1] - pel_[1], 0.0))
        if d.length < 1e-6:
            INNER_LEG[i] = True; continue
        d.normalize()
        hit = tr.ray_cast(Vector(co[i]) + d * 0.004, d, 0.5)
        INNER_LEG[i] = hit[0] is not None
    # ... and near a leg bone: the gown's back surface also hits the cape behind it (Warlock: 592 such vertices took
    # calf weights and the cape hem went 24 cm under the floor in Dead; user review 2026-10-20)
    def _segd(p, a_, b_):
        ab = b_ - a_; t = np.clip(((p - a_) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(p - (a_ + np.outer(t, ab)), axis=1)
    near = np.full(nv, 9.0)
    for sd in 'LR':
        th_, ca_, ft_ = (np.array(rig.data.bones[f'B_{sd}_{b}'].head_local) for b in ('Thigh', 'Calf', 'Foot'))
        near = np.minimum(near, np.minimum(_segd(co, th_, ca_), _segd(co, ca_, ft_)))
    INNER_LEG &= near < float(cfg.C.get('inner_leg_r', 0.12))
    print('WEIGHTS inner legs (inside the gown)', int(INNER_LEG.sum()), 'of', int((gv == 2).sum()))
robe = (((gv == 2) & (W[:, ARMB].sum(1) < 0.5) & ~INNER_LEG) | ((gv == 1) & (co[:, 2] < WAIST[1] + 0.02) & (W[:, ARMB].sum(1) < 0.5) & ~SLEEVE)) & ~HANDV
ids = np.where(robe)[0]
faces = [tuple(f.vertices) for f in me.polygons if all(gv[i] == 2 for i in f.vertices)]
tree = BVHTree.FromPolygons(co.tolist(), faces)
pel = J('B_Pelvis'); axis = Vector((float(pel[0]), float(pel[1]), 0.0))
chains = []
for c in range(NCH):
    deg = -180 + c * 360.0 / NCH; a = math.radians(deg); d = Vector((math.sin(a), math.cos(a), 0))
    pts = []
    for zz in ZS:
        start = Vector((axis.x, axis.y, zz)); hits = []; dist = 0
        while dist < 0.6:
            loc, n, idx, dl = tree.ray_cast(start + d * (dist + 1e-5), d, 0.6 - dist)
            if loc is None:
                break
            hits.append(loc); dist += dl + 1e-5
        if hits:
            pt = hits[-1]
        else:
            aa = np.arctan2(co[ids, 0] - axis.x, co[ids, 1] - axis.y); da = np.abs((aa - a + math.pi) % (2 * math.pi) - math.pi)
            cand = ids[(da < .25) & (np.abs(co[ids, 2] - zz) < .07)]
            if not len(cand):                        # the hem rises here (the feet show): nearest robe height in this sector
                sec = ids[da < .25]
                cand = sec[np.abs(co[sec, 2] - zz) < np.abs(co[sec, 2] - zz).min() + 0.03]
            pt = Vector(co[cand].mean(0)); pt.z = zz
        pts.append(list(pt))
    chains.append({'deg': deg, 'pts': pts, 'bones': [f'Robe_{c:02}_{k}' for k in range(4)]})
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
for c in chains:
    parent = rig.data.edit_bones['B_Pelvis']
    for k, n in enumerate(c['bones']):
        b = rig.data.edit_bones.get(n) or rig.data.edit_bones.new(n)
        b.head = c['pts'][k]; b.tail = c['pts'][k + 1]; b.parent = parent; b.use_connect = k > 0; parent = b
bpy.ops.object.mode_set(mode='OBJECT')
for c in chains:
    for n in c['bones']:
        if n not in gid:
            body.vertex_groups.new(name=n); names.append(n); gid[n] = len(names) - 1
W = np.hstack([W, np.zeros((nv, len(names) - W.shape[1]))])
step = 360.0 / NCH
for i in ids:
    x, y, zz = co[i]
    a = (math.degrees(math.atan2(x - axis.x, y - axis.y)) + 180) / step; lo = int(a) % NCH; hi = (lo + 1) % NCH; t = a - math.floor(a)
    w = np.zeros(len(names))
    u = float(np.interp(zz, list(reversed(ZS[:-1])), list(reversed(range(4)))))
    k = min(3, int(u)); j = min(3, k + 1); v = u - k
    for ci, mix in ((lo, 1 - t), (hi, t)):
        w[gid[chains[ci]['bones'][k]]] += mix * (1 - v); w[gid[chains[ci]['bones'][j]]] += mix * v
    waist = float(np.clip((zz - WAIST[0]) / (WAIST[1] - WAIST[0]), 0, 1))
    W[i] = W[i] * waist + w * (1 - waist) if zz > WAIST[0] else w
    if zz > WAIST[0]:                                  # above: Meshy's trunk weights, legs folded into the pelvis
        for s in ('L', 'R'):
            for b in ('Thigh', 'Calf', 'Foot', 'Toe0'):
                W[i, gid['B_Pelvis']] += W[i, gid[f'B_{s}_{b}']]; W[i, gid[f'B_{s}_{b}']] = 0
# interior robe vertices near the body axis (between the legs inside a fused gown): the sector angle is unstable there
# (29x stretch in the warlock's walk); they copy the weights of the nearest outer robe vertex (radius >= R_OUT)
R_IN, R_OUT = 0.085, 0.12
rad = np.hypot(co[:, 0] - axis.x, co[:, 1] - axis.y)
inner = ids[rad[ids] < R_IN]; outer_ids = ids[rad[ids] >= R_OUT]
if len(inner) and len(outer_ids):
    kdo = KDTree(len(outer_ids))
    for j, i in enumerate(outer_ids):
        kdo.insert(co[i], j)
    kdo.balance()
    for i in inner:
        W[i] = W[outer_ids[kdo.find(co[i])[1]]]
    print('WEIGHTS inner robe vertices copied from the outer surface', len(inner))
# rope ends: per-vertex copies of the nearest skirt vertex mixed different chains along one cord (5x stretch in the
# walk); each rope piece takes ONE sector mix (its mean angle) with the height blend per vertex, like a skirt strip
rope = np.where(gv == 8)[0]


def chain_weights(ang_deg, zz):
    a = (ang_deg + 180) / step; lo = int(a) % NCH; hi = (lo + 1) % NCH; t = a - math.floor(a)
    w = np.zeros(len(names))
    u = float(np.interp(zz, list(reversed(ZS[:-1])), list(reversed(range(4)))))
    k = min(3, int(u)); j = min(3, k + 1); v = u - k
    for ci, mix in ((lo, 1 - t), (hi, t)):
        w[gid[chains[ci]['bones'][k]]] += mix * (1 - v); w[gid[chains[ci]['bones'][j]]] += mix * v
    return w


for piece in sorted(set(pv[rope].tolist())):
    m = rope[pv[rope] == piece]; c = co[m].mean(0)
    ang = math.degrees(math.atan2(c[0] - axis.x, c[1] - axis.y))
    for i in m:
        W[i] = chain_weights(ang, min(co[i, 2], WAIST[0]))
# no leg weight anywhere (no legs under the robe); normalise, keep the 4 largest
legs = [gid[n] for n in names if any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe0'))]
nolegs = (gv != 15) & ~INNER_LEG                     # shoes/feet (15) and legs inside a gown keep theirs
W[nolegs, gid['B_Pelvis']] += W[np.ix_(nolegs, legs)].sum(1); W[np.ix_(nolegs, legs)] = 0
for i in range(nv):
    w = W[i]; top = np.argsort(-w)[:4]; s = w[top].sum()
    for g in body.vertex_groups:
        pass
    keep = np.zeros_like(w); keep[top] = w[top] / s if s > 0 else 0
    W[i] = keep
for g in body.vertex_groups:
    g.remove(list(range(nv)))
for gi in range(len(names)):
    nz = np.where(W[:, gi] > 1e-5)[0]
    for i in nz:
        body.vertex_groups[names[gi]].add([int(i)], float(W[i, gi]), 'REPLACE')
scene['cloak_chains'] = json.dumps(chains)
assert len(rig.data.bones) <= 128
print('WEIGHTS robe verts', len(ids), 'rope', len(rope), 'chains', NCH, 'bones', len(rig.data.bones),
      'unweighted', int((W.sum(1) < 0.99).sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
