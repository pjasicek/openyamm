"""Medusa rig on work/step1_raw.blend -> work/rig_v1.blend (Rig + Body) and work/rig.json.
Forward -Y, up +Z, character left +X. Joints: work/joints.json (joints_m282.py), work/hands.json (fit_hands.py).

Skeleton
- Serpent (quadruped playbook, "Snakes"): Root = the segment at the bend; Tail_01..Tail_NN run back along the floor to
  the rattle, Col_01..Col_NN rise from the bend to the hips. Bones are disconnected so clips can fit them to a curve.
- Human upper body (humanoid playbook): Pelvis - Spine1 - Spine2 - Neck - Head; per side Clavicle - UpperArm -
  ForeArm (+ ForeArmTwist at mid forearm, 60 % of the hand roll) - Hand - five 3-bone fingers fitted by connectivity.
  Spine/arm rolls: local Z forward, so +X rotation flexes forward; finger X = the hand's flexion axis, sign chosen so
  +X curls toward the palm.
Weights
- serpent skin: arc position along the axial centreline (cobra rule: nearest point, smoothed over the mesh, linear
  between segment midpoints);
- upper skin: Blender heat weights on a voxel proxy of the skin above the hips (upper bones only), then the arm rules:
  no UpperArm/ForeArm weight medial of the armpit or on chest/back/neck, forearm twist ramp 15-85 %; blended into the
  serpent weights between z 0.80 and 0.95;
- hands (separate pieces): palm on Hand, fingers along their own chains, the wrist ring copies the skin under it;
- hair snakes: Head above the chin, fading to Neck and Spine2 toward their hanging ends;
- quiver, arrows, breast studs rigid on Spine2; eyes rigid on Head; collar and arm rings copy the skin under them."""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ = lambda *p: os.path.join(HERE, 'work', *p)
bpy.ops.wm.open_mainfile(filepath=W_('step1_raw.blend'))
body = bpy.data.objects['Body']; me = body.data
# the Smart Topology import is flat-shaded (sharp_face on every face): the export then split every vertex per face and
# the model rendered as light/dark triangle facets (user review). Smooth shading everywhere; the normal maps add detail.
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
if 'sharp_face' in me.attributes:
    me.attributes.remove(me.attributes['sharp_face'])
me.update()
JS = json.load(open(W_('joints.json'))); HS = json.load(open(W_('hands.json')))
J = np.array(JS['axial']); RAD = np.array(JS['radius']); K = JS['root']; H = {k: np.array(v) for k, v in JS['human'].items()}
NSEG = len(J) - 1
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
EDGES = np.array([tuple(e.vertices) for e in me.edges])
# --------------------------------------------------------------------------------- piece classes (step1 piece ids)
QUIVER = {20}; STUDS = {17, 18}; EYES = {28, 30}; COLLAR = {19}; RINGS = {21, 22}; HANDS = {5: 'L', 6: 'R'}
cent = {p: co[pv == p].mean(0) for p in range(pv.max() + 1)}
ARROWS = {p for p in cent if p not in QUIVER and cent[p][1] > 0.38 and (pv == p).sum() < 40}
RIGID_SPINE2 = QUIVER | STUDS | ARROWS
HAIR = {p for p in cent if p != 0 and p not in RIGID_SPINE2 | EYES | COLLAR | RINGS | set(HANDS)}
print('PIECES hair', sorted(HAIR), 'arrows', sorted(ARROWS))


def axname(i):
    if i == K:
        return 'Root'
    return f'Tail_{K - i:02d}' if i < K else f'Col_{i - K:02d}'


FINGERS = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = ad.edit_bones
V = lambda a: Vector(tuple(float(x) for x in a))
FWD = Vector((0, -1, 0)); UP = Vector((0, 0, 1))


def new(name, head, tail, parent=None, roll_to=FWD, connect=False):
    b = eb.new(name); b.head = V(head); b.tail = V(tail)
    d = (b.tail - b.head).normalized()
    ref = roll_to if abs(d.dot(roll_to.normalized())) < 0.95 else (UP if abs(d.dot(UP)) < 0.95 else Vector((1, 0, 0)))
    b.align_roll(ref)
    if parent is not None:
        b.parent = eb[parent]; b.use_connect = connect
    return b


for i in range(NSEG):                                   # axial: tail bones point away from the root
    a, c = J[i], J[i + 1]
    h, t = (c, a) if i < K else (a, c)
    new(axname(i), h, t, roll_to=UP if i < K else FWD)
for i in range(NSEG):
    if i < K:
        eb[axname(i)].parent = eb[axname(i + 1)]
    elif i > K:
        eb[axname(i)].parent = eb[axname(i - 1)]
top = axname(NSEG - 1)
new('Pelvis', H['Pelvis'], H['Spine1'], top)
new('Spine1', H['Spine1'], H['Spine2'], 'Pelvis', connect=True)
new('Spine2', H['Spine2'], H['Neck'], 'Spine1', connect=True)
new('Neck', H['Neck'], H['Head'], 'Spine2', connect=True)
new('Head', H['Head'], H['HeadTop'], 'Neck', connect=True)
for s in 'LR':
    hs = HS[s]; X = np.array(hs['frame']['X']); Zp = np.array(hs['frame']['Z_palm'])
    new(f'Clavicle_{s}', H[f'Clavicle_{s}'], H[f'UpperArm_{s}'], 'Spine2')
    new(f'UpperArm_{s}', H[f'UpperArm_{s}'], H[f'ForeArm_{s}'], f'Clavicle_{s}', connect=True)
    new(f'ForeArm_{s}', H[f'ForeArm_{s}'], H[f'Hand_{s}'], f'UpperArm_{s}', connect=True)
    mid = (H[f'ForeArm_{s}'] + H[f'Hand_{s}']) / 2
    new(f'ForeArmTwist_{s}', mid, H[f'Hand_{s}'], f'ForeArm_{s}')
    hb = new(f'Hand_{s}', H[f'Hand_{s}'], hs['hand_end'], f'ForeArm_{s}', connect=True)
    hb.align_roll(V(Zp))                                  # hand local Z = palm normal, X = flexion axis
    for f in FINGERS:
        jt = hs['fingers'][f]['joints']
        for k in range(3):
            b = new(f'{f}{k + 1}_{s}', jt[k], jt[k + 1], f'Hand_{s}' if k == 0 else f'{f}{k}_{s}', connect=k > 0)
            d = (b.tail - b.head).normalized()
            fx = V(X) - d * d.dot(V(X))                    # flexion axis = the hand's X, orthogonalised
            if f == 'Thumb':
                fx = d.cross(V(Zp)).normalized()
                fx = fx if fx.dot(V(X)) >= 0 else -fx
            fz = fx.normalized().cross(d)                  # +X rotation turns Y toward Z
            # make +X rotation curl toward the palm: Z must point to the palm side
            if fz.dot(V(Zp)) < 0:
                fz = -fz
            b.align_roll(fz)
bpy.ops.object.mode_set(mode='OBJECT')
names = [b.name for b in ad.bones]
gi = {n: k for k, n in enumerate(names)}
NB = len(names)
Wt = np.zeros((nv, NB))
skin = np.where(pv == 0)[0]

# --------------------------------------------------------------------------------- serpent weights (arc position)
segA, segB = J[:-1], J[1:]
seglen = np.linalg.norm(segB - segA, axis=1); cum = np.r_[0, np.cumsum(seglen)]
best_s = np.zeros(nv); best_d = np.full(nv, 1e9)
for i in range(NSEG):
    dv = segB[i] - segA[i]
    t = np.clip(((co - segA[i]) @ dv) / (dv @ dv), 0, 1)
    dist = np.linalg.norm(co - (segA[i] + t[:, None] * dv), axis=1)
    m = dist < best_d; best_d[m] = dist[m]; best_s[m] = cum[i] + t[m] * seglen[i]
adj = [[] for _ in range(nv)]
for a, b in EDGES:
    adj[a].append(b); adj[b].append(a)
s_ = best_s.copy()
for _ in range(10):                                       # smoothed arc position: no weight step across the S-bend
    s_ = np.array([0.5 * s_[v] + 0.5 * np.mean(s_[adj[v]]) if adj[v] else s_[v] for v in range(nv)])
mid = (cum[:-1] + cum[1:]) / 2
SER = np.zeros((nv, NB))
for v in range(nv):
    x = s_[v]
    if x <= mid[0]:
        SER[v, gi[axname(0)]] = 1; continue
    if x >= mid[-1]:
        SER[v, gi[axname(NSEG - 1)]] = 1; continue
    i = int(np.searchsorted(mid, x) - 1); f = (x - mid[i]) / (mid[i + 1] - mid[i])
    SER[v, gi[axname(i)]] += 1 - f; SER[v, gi[axname(i + 1)]] += f

# --------------------------------------------------------------------------------- upper body: heat weights on a proxy
UPPER = ['Col_%02d' % (NSEG - 1 - K), 'Pelvis', 'Spine1', 'Spine2', 'Neck', 'Head'] + \
        [f'{n}_{s}' for s in 'LR' for n in ('Clavicle', 'UpperArm', 'ForeArm', 'ForeArmTwist', 'Hand')]
pm = me.copy(); proxy = bpy.data.objects.new('Proxy', pm); bpy.context.scene.collection.objects.link(proxy)
bm = bmesh.new(); bm.from_mesh(pm); lay = bm.verts.layers.int.get('piece')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] != 0], context='VERTS')
bmesh.ops.holes_fill(bm, edges=bm.edges, sides=0)
bm.to_mesh(pm); bm.free()
r = proxy.modifiers.new('Remesh', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = float(os.environ.get('VOXEL', '0.014'))
deps = bpy.context.evaluated_depsgraph_get()
rm = bpy.data.meshes.new_from_object(proxy.evaluated_get(deps)); proxy.modifiers.clear(); proxy.data = rm
for b in ad.bones:
    b.use_deform = b.name in UPPER
for o in bpy.data.objects:
    o.select_set(o in (proxy, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
pw = np.array([sum(g.weight for g in v.groups) for v in rm.vertices])
print('RIG proxy verts', len(rm.vertices), 'unweighted', int((pw < 1e-6).sum()))
for b in ad.bones:
    b.use_deform = True
body.vertex_groups.clear()
for n in names:
    body.vertex_groups.new(name=n)
dt = body.modifiers.new('DT', 'DATA_TRANSFER'); dt.object = proxy
dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.modifier_apply(modifier='DT')
HEAT = np.zeros((nv, NB))
for v in me.vertices:
    for e in v.groups:
        HEAT[v.index, e.group] = e.weight
bpy.data.objects.remove(proxy, do_unlink=True)


def seg_param(p, a, b):
    d = b - a; t = np.clip(((p - a) @ d) / (d @ d), 0, 1)
    return t, np.linalg.norm(p - (a + t[:, None] * d), axis=1)


# arm rules on the skin
for s, sg in (('L', 1), ('R', -1)):
    S, E, Wr = H[f'UpperArm_{s}'], H[f'ForeArm_{s}'], H[f'Hand_{s}']
    tu, du = seg_param(co, S, E); tf, df = seg_param(co, E, Wr)
    armr = np.minimum(du, df)
    lateral = sg * co[:, 0]
    # medial of the armpit / chest / back / neck / hips: no upper-arm or forearm weight. Arm skin lies within 6.5 cm
    # of the shoulder-elbow-wrist line (the deltoid cap within 9 cm, lateral of the armpit)
    deltoid = (tu < 0.25) & (du < 0.09) & (lateral > 0.12)
    torso = ~(((armr < 0.065) & ((tu > 0.1) | (df < du))) | deltoid) | (co[:, 2] > 1.43) | \
        ((lateral < 0.15) & (co[:, 2] < 1.33))                 # the ribs under the armpit
    for n in ('UpperArm', 'ForeArm', 'ForeArmTwist', 'Hand'):
        HEAT[torso, gi[f'{n}_{s}']] = 0
    # forearm twist ramp 15-85 % along the forearm
    fa = (df < du) & (tf > 0) & (pv == 0) & ~torso
    tw = np.clip((tf - 0.15) / 0.7, 0, 1); tw = tw * tw * (3 - 2 * tw)
    tot = HEAT[:, gi[f'ForeArm_{s}']] + HEAT[:, gi[f'ForeArmTwist_{s}']]
    HEAT[fa, gi[f'ForeArmTwist_{s}']] = tot[fa] * tw[fa]
    HEAT[fa, gi[f'ForeArm_{s}']] = tot[fa] * (1 - tw[fa])
# armpit webs: Smart Topology fused the inner upper arm to the ribs from the armpit down to z ~1.19, so a hard arm/torso
# weight edge there tore (18x edge stretch with the arm raised). Diffuse the weights over that zone (Laplacian passes on
# the skin graph, both sides) so the fused skin stretches gradually like an armpit.
pit = (pv == 0) & (np.abs(co[:, 0]) > 0.08) & (np.abs(co[:, 0]) < 0.30) & (co[:, 2] > 1.10) & (co[:, 2] < 1.38) & (co[:, 1] > 0.10)
nbr = [[] for _ in range(nv)]
for a_, b_ in EDGES:
    nbr[a_].append(b_); nbr[b_].append(a_)
pit_ids = np.where(pit)[0]
for _ in range(int(os.environ.get('PIT_PASSES', '25'))):
    new_rows = {i: 0.5 * HEAT[i] + 0.5 * HEAT[nbr[i]].mean(0) for i in pit_ids if nbr[i]}
    for i, r in new_rows.items():
        HEAT[i] = r
print('RIG armpit diffusion vertices', len(pit_ids))
# blend serpent (below) and heat (above) weights over z 0.80 .. 0.95
b = np.clip((co[:, 2] - 0.80) / 0.15, 0, 1); b = b * b * (3 - 2 * b)
hs = HEAT.sum(1, keepdims=True)
HN = np.where(hs > 1e-6, HEAT / np.maximum(hs, 1e-9), SER)
ARMB = [gi[f'{n}_{s}'] for s in 'LR' for n in ('UpperArm', 'ForeArm', 'ForeArmTwist', 'Hand')]
armshare = HN[:, ARMB].sum(1)
b = np.where(armshare > 0.05, 1.0, b)                     # arms never take serpent weights (wrists hang at hip level)
Wt[skin] = (SER * (1 - b[:, None]) + HN * b[:, None])[skin]

# --------------------------------------------------------------------------------- pieces
kd = KDTree(len(skin))
for k, sv in enumerate(skin):
    kd.insert(co[sv], k)
kd.balance()


def copy_skin(idx, rigid=True, n=6):
    for i in idx:
        hits = kd.find_n(co[i], n); w = np.array([1.0 / max(h[2], 1e-4) for h in hits])
        Wt[i] = (w[:, None] * Wt[[skin[h[1]] for h in hits]]).sum(0) / w.sum()
    if rigid:
        Wt[idx] = Wt[idx].mean(0)


for p in range(1, pv.max() + 1):
    idx = np.where(pv == p)[0]
    if p in RIGID_SPINE2:
        Wt[idx] = 0; Wt[idx, gi['Spine2']] = 1
    elif p in EYES:
        Wt[idx] = 0; Wt[idx, gi['Head']] = 1
    elif p in COLLAR or p in RINGS:
        copy_skin(idx, rigid=True)
    elif p in HAIR:
        z = co[idx, 2]
        h = np.clip((z - 1.30) / 0.22, 0, 1); h = h * h * (3 - 2 * h)          # 1 above the chin, 0 at z 1.30
        lo = np.clip((z - 1.12) / 0.18, 0, 1)                                   # Neck between, Spine2 at the ends
        Wt[idx] = 0
        Wt[idx, gi['Head']] = h
        Wt[idx, gi['Neck']] = (1 - h) * lo
        Wt[idx, gi['Spine2']] = (1 - h) * (1 - lo)
    elif p in HANDS:
        s = HANDS[p]; hs_ = HS[s]; geo = {int(k): v for k, v in hs_['geo'].items()}
        Wt[idx] = 0
        ring = np.array([i for i in idx if geo[int(i)] < 0.045])
        palm = set(hs_['palm_verts'])
        for i in idx:
            if geo[int(i)] < 0.045:
                continue
            Wt[i, gi[f'Hand_{s}']] = 1.0
        for f in FINGERS:
            jt = np.array(hs_['fingers'][f]['joints']); fv = np.array(hs_['fingers'][f]['verts'])
            L = np.linalg.norm(np.diff(jt, axis=0), axis=1); cl = np.r_[0, np.cumsum(L)]
            bs = np.zeros(len(fv)); bd = np.full(len(fv), 9.0)
            for k in range(3):
                t, dd = seg_param(co[fv], jt[k], jt[k + 1])
                m = dd < bd; bd[m] = dd[m]; bs[m] = cl[k] + t[m] * L[k]
            mids = (cl[:-1] + cl[1:]) / 2
            for v, x in zip(fv, bs):
                Wt[v] = 0
                bn = [f'{f}{k + 1}_{s}' for k in range(3)]
                if x < mids[0]:                                  # base: blend from the palm
                    a_ = np.clip(x / max(mids[0], 1e-4), 0, 1)
                    Wt[v, gi[bn[0]]] = 0.5 + 0.5 * a_; Wt[v, gi[f'Hand_{s}']] = 0.5 - 0.5 * a_
                elif x >= mids[-1]:
                    Wt[v, gi[bn[2]]] = 1
                else:
                    k = int(np.searchsorted(mids, x) - 1); f_ = (x - mids[k]) / (mids[k + 1] - mids[k])
                    Wt[v, gi[bn[k]]] = 1 - f_; Wt[v, gi[bn[k + 1]]] = f_
        # the wrist ring follows the skin under it (bracelet)
        if len(ring):
            copy_skin(ring, rigid=False)
            Wt[ring] = 0.5 * Wt[ring] + 0.5 * Wt[ring].mean(0)
        # palm vertices near the wrist get a little forearm-twist share for a smooth wrist
        for i in idx:
            g = geo[int(i)]
            if 0.045 <= g < 0.07 and Wt[i, gi[f'Hand_{s}']] > 0.99:
                f_ = (0.07 - g) / 0.025 * 0.35
                Wt[i, gi[f'Hand_{s}']] = 1 - f_; Wt[i, gi[f'ForeArmTwist_{s}']] = f_
good = np.where(Wt.sum(1) > 0.5)[0]; lost = np.where(Wt.sum(1) <= 0.5)[0]
if len(lost):
    kg = KDTree(len(good))
    for k, g in enumerate(good):
        kg.insert(co[g], k)
    kg.balance()
    for i in lost:
        Wt[i] = Wt[good[kg.find(co[i])[1]]]
top4 = np.argsort(-Wt, 1)[:, :4]; W2 = np.zeros_like(Wt); rows = np.arange(nv)[:, None]
W2[rows, top4] = Wt[rows, top4]; W2[W2 < 0.01] = 0; W2 /= np.maximum(W2.sum(1, keepdims=True), 1e-9)
for g in body.vertex_groups:
    g.remove(list(range(nv)))
for j, n in enumerate(names):
    nz = np.nonzero(W2[:, j] > 1e-4)[0]
    grp = body.vertex_groups[n]
    for i in nz:
        grp.add([int(i)], float(W2[i, j]), 'REPLACE')
body.parent = rig
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
print('RIG bones', NB, 'filled', len(lost), 'unweighted', int((W2.sum(1) < 0.99).sum()))
json.dump({'axial': J.tolist(), 'radius': RAD.tolist(), 'root': K, 'names': [axname(i) for i in range(NSEG)],
           'human': {k: v.tolist() for k, v in H.items()}},
          open(W_('rig.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=W_('rig_v1.blend'))
print('SAVED rig_v1')
