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
SPLIT_Z, RAMP = float(cfg.C.get('split_z', 1.065)), float(cfg.C.get('split_ramp', 0.05))
ARMB0 = [gid[n] for n in names if any(t in n for t in ('UpperArm', 'Forearm', 'Hand'))]
TRUNK = [gid[n] for n in ('B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2')]
CHEST = [gid[n] for n in ('B_Spine1', 'B_Spine2')]
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
    # m422: the arm share goes to the CHEST bones (Meshy's trunk mix there is mostly B_Spine: the side panel was pulled
    # between the hip bone and the raised arm, 5-7 cm openings)
    tw_ = W[i, CHEST] if cfg.C.get('split_to_chest') else W[i, TRUNK]
    tg_ = CHEST if cfg.C.get('split_to_chest') else TRUNK
    if tw_.sum() > 1e-6:
        W[i, tg_] += moved * tw_ / tw_.sum()
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
print('WEIGHTS torso below the armpit', len(tor), 'of', int(low.sum()), 'robe-top verts below', SPLIT_Z, 'components', ncomp)

# m422 user review 1 (arm raised overhead in the attack): Meshy left upper-arm weight on the chest beside the strip
# and on the side panel under the arm, which dragged the chest toward the arm and pulled the armpit into a flat fan.
# Playbook: upper-arm weight fades out medially. On the coat top (not the sleeves) between ARMPIT_Z and the shoulder
# joint, the arm share (upper arm, forearm, hand) is scaled by smoothstep((|x| - X0) / (X1 - X0)) - none on the chest
# medial of X0, Meshy's at the shoulder seam beyond X1 - and the rest goes to the trunk bones already on the vertex;
# then ARMPIT_SMOOTH Jacobi passes over that band (coat top only, all groups) remove the step.
AP = cfg.C.get('armpit_fade')
if AP:
    X0, X1, ZLO = AP['x0'], AP['x1'], AP['z_lo']
    band = np.where((gv == 1) & ~SLEEVE & (co[:, 2] > ZLO) & (co[:, 2] < float(J('B_R_UpperArm')[2]) + 0.06))[0]
    BX0, BX1 = AP.get('back_x0', X0), AP.get('back_x1', X1)
    for i in band:
        back = co[i, 1] > float(J("B_Pelvis")[1]) + 0.05   # the back panel: the fade reaches further out (shoulder blade)
        x0_, x1_ = (BX0, BX1) if back else (X0, X1)
        f = float(np.clip((abs(co[i, 0]) - x0_) / (x1_ - x0_), 0, 1)); f = f * f * (3 - 2 * f)
        moved = W[i, ARMB0].sum() * (1 - f)
        if moved <= 1e-6:
            continue
        W[i, ARMB0] *= f
        tgt = CHEST + [gid['B_L_Clavicle'], gid['B_R_Clavicle']]
        tw_ = W[i, tgt]
        if tw_.sum() > 1e-6:
            W[i, tgt] += moved * tw_ / tw_.sum()
        else:
            W[i, gid['B_Spine2']] += moved
    # the trunk share of the band by HEIGHT (Meshy put up to 0.5 B_Pelvis on the back at chest height, so the back
    # panel was pulled between the hip and the shoulder): a linear ladder between the trunk joints' heights
    if AP.get('trunk_ladder'):
        TB = ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2']; TZ = [float(J(n)[2]) for n in TB]; TI = [gid[n] for n in TB]
        for i in band:
            tot = W[i, TI].sum()
            if tot <= 1e-6:
                continue
            u = float(np.interp(co[i, 2], TZ, range(4))); k = min(2, int(u)); t = u - k
            W[i, TI] = 0; W[i, TI[k]] += tot * (1 - t); W[i, TI[k + 1]] += tot * t
    bset = set(band.tolist()); nb_ = {}
    for e in me.edges:
        i, j = e.vertices
        if i in bset and gv[j] == 1:
            nb_.setdefault(i, []).append(j)
        if j in bset and gv[i] == 1:
            nb_.setdefault(j, []).append(i)
    for it in range(int(AP.get('smooth', 6))):
        Wn = W.copy()
        for i in band:
            if i in nb_:
                Wn[i] = 0.5 * W[i] + 0.5 * W[nb_[i]].mean(0)
        W = Wn
    print('WEIGHTS armpit medial fade verts', len(band), 'x0/x1', X0, X1)
# ---------------------------------------------------------------- robe chains
ARMB = [gid[n] for n in names if any(t in n for t in ('UpperArm', 'Forearm', 'Hand'))]
_wz = float(cfg.C.get('waist_z', 0.90))
_hem = float(cfg.C.get('hem_z', 0.02))          # m422: the coat ends at mid-shin, the chains end at its hem
ZS = [_wz] + [round(_wz - (_wz - _hem) * k / 4, 4) for k in (1, 2, 3, 4)]
WAIST = (_wz - 0.04, _wz + 0.03)       # chains below WAIST[0], B_Pelvis above WAIST[1]
NCH = int(cfg.C.get('nch', os.environ.get('NCH', '14')))    # 14 x 4 robe bones + 2 x 2 x 3 banner bones keep the skin within 128 joints
robe = (gv == 2) | ((gv == 1) & (co[:, 2] < WAIST[1] + 0.02) & (W[:, ARMB].sum(1) < 0.5) & ~SLEEVE)
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
            assert len(cand), (deg, zz)
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
# m422 user review 1: the skirt beside the raised front button strip is a vertical groove that Meshy never saw (painted
# flat); with each side blending its own neighbour chain the groove opened in the walk and showed as flat light
# patches beside the strip. Within FRONT_SEAM deg of the front centre the skirt takes the centre chain only (as the
# clasps do), blending back to the sector rule over FRONT_BLEND deg, so the strip and its grooves move as one panel.
FRONT_SEAM, FRONT_BLEND = (float(x) for x in cfg.C.get('front_seam_deg', [0, 0]))
for i in ids:
    x, y, zz = co[i]
    deg_ = math.degrees(math.atan2(x - axis.x, y - axis.y))
    a = (deg_ + 180) / step
    if FRONT_SEAM + FRONT_BLEND > 0:
        df = 180 - abs(deg_)
        f = 1.0 if df < FRONT_SEAM else max(0.0, 1 - (df - FRONT_SEAM) / max(FRONT_BLEND, 1e-6))
        a = a + ((0.0 if a < NCH / 2 else float(NCH)) - a) * f
    lo = int(a) % NCH; hi = (lo + 1) % NCH; t = a - math.floor(a)
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


for piece in sorted(set(pv[rope].tolist()) - set(int(x) for x in cfg.C.get('accessory_pieces', []))):
    m = rope[pv[rope] == piece]; c = co[m].mean(0)
    ang = math.degrees(math.atan2(c[0] - axis.x, c[1] - axis.y))
    for i in m:
        W[i] = chain_weights(ang, min(co[i, 2], WAIST[0]))
# m422 user review 1: the coat is a closed shell 0.5-2 cm thick, and its inner layer (never seen, painted flat by
# Meshy) took its own sector/height mix: the bending chains moved it differently from the outer surface and it came
# through as flat light patches beside the button strip in the walk. Each inner-layer vertex (its outward radial ray
# meets the coat again within INNER_REACH) now copies the weights of the nearest vertex of the outer face it hits, so
# both layers share one blended transform.
INNER_REACH = float(cfg.C.get('inner_layer_reach', 0.0))
if INNER_REACH > 0:
    # inner layer = vertices whose every coat face turns its normal toward the body axis (a radial ray from the vertex
    # missed the outer face at the strip's grooves); each takes the weights of the nearest outer-layer vertex within
    # INNER_REACH
    COAT = (1, 2)
    inner_f = np.zeros(len(me.polygons), bool); coatf = np.zeros(len(me.polygons), bool)
    for f in me.polygons:
        if all(gv[v] in COAT for v in f.vertices) and f.center.z < WAIST[1]:
            coatf[f.index] = True
            r = Vector((f.center.x - axis.x, f.center.y - axis.y, 0.0))
            inner_f[f.index] = r.length > 1e-4 and f.normal.dot(r.normalized()) < -0.2
    vin = np.zeros(nv, bool); vout = np.zeros(nv, bool)
    for f in me.polygons:
        if coatf[f.index]:
            for v in f.vertices:
                (vin if inner_f[f.index] else vout)[v] = True
    vin &= ~vout & ~SLEEVE
    kd = KDTree(int(vout.sum()))
    for k, i in enumerate(np.where(vout)[0]):
        kd.insert(Vector(co[i]), int(i))
    kd.balance()
    ninner = 0
    for i in np.where(vin)[0]:
        _, j, dd = kd.find(Vector(co[i]))
        if j is not None and dd < INNER_REACH:
            W[i] = W[j]; ninner += 1
    print('WEIGHTS inner coat layer vertices copied from the outer surface', ninner, 'of', int(vin.sum()))
# m422 user review 1: the clasps (rigid on spine bones or a per-cord chain mix) and the buckle (rigid on B_Spine) slid
# off their painted seats on the placket. Playbook: accessories copy the skin under them. Each listed piece takes ONE
# weight set, that of the coat vertex nearest its centroid (the placket under it, chain bones below the belt), so it
# stays rigid and moves exactly with the surface it sits on.
ACC = [int(x) for x in cfg.C.get('accessory_pieces', [])]
if ACC:
    COATG = (1, 2)
    cids = np.where(np.isin(gv, COATG))[0]
    kd2 = KDTree(len(cids))
    for k, i in enumerate(cids):
        kd2.insert(Vector(co[i]), int(i))
    kd2.balance()
    for pc_ in ACC:
        m = np.where(pv == pc_)[0]
        if not len(m):
            continue
        # the coat point under the piece: the nearest coat vertex to the piece's rear-most (body-side) points' centre
        c = co[m].mean(0)
        _, j, dd = kd2.find(Vector(c))
        W[m] = W[j]
    print('WEIGHTS accessories copy the skin under them', len(ACC), 'pieces')
# no leg weight anywhere (no legs under the robe); normalise, keep the 4 largest
legs = [gid[n] for n in names if any(t in n for t in ('Thigh', 'Calf', 'Foot', 'Toe0'))]
nolegs = gv != 15                                    # shoes (garment 15, the mage's feet under the hem) keep theirs
W[nolegs, gid['B_Pelvis']] += W[np.ix_(nolegs, legs)].sum(1); W[np.ix_(nolegs, legs)] = 0
# m422 (mid-shin coat over real legs): the skirt follows the thighs by a share that grows from 0 at the waist to
# SKIRT_LEG at the hem (smoothstep), one smooth left/right mix by the side of the pelvis line (front and back centre
# 50/50 over +-MIXW): the pure chain skirt let the striding and kicking legs through its closed front and back in the
# walk and the death (the chains only cleared the legs at their joints). The chain share keeps the swing.
SKIRT_LEG = float(cfg.C.get('skirt_leg_share', 0.0))
if SKIRT_LEG > 0:
    MIXW = 0.06
    tL, tR = gid['B_L_Thigh'], gid['B_R_Thigh']
    for i in ids:
        x, y, zz = co[i]
        if zz >= WAIST[0]:
            continue
        u = float(np.clip((WAIST[0] - zz) / (WAIST[0] - ZS[-1]), 0, 1)); sh = SKIRT_LEG * u * u * (3 - 2 * u)
        mL = float(np.clip(0.5 + (x - axis.x) / (2 * MIXW), 0, 1))
        W[i] *= 1 - sh; W[i, tL] += sh * mL; W[i, tR] += sh * (1 - mL)
    for i in rope:                                     # the skirt buttons ride the skirt the same way
        x, y, zz = co[i]
        if zz >= WAIST[0]:
            continue
        u = float(np.clip((WAIST[0] - zz) / (WAIST[0] - ZS[-1]), 0, 1)); sh = SKIRT_LEG * u * u * (3 - 2 * u)
        mL = float(np.clip(0.5 + (x - axis.x) / (2 * MIXW), 0, 1))
        W[i] *= 1 - sh; W[i, tL] += sh * mL; W[i, tR] += sh * (1 - mL)
    print('WEIGHTS skirt leg share', SKIRT_LEG)
for i in range(nv):
    w = W[i]; top = np.argsort(-w)[:int(cfg.C.get("max_influences", 4))]; s = w[top].sum()
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
