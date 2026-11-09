"""Forad v3 rig fixes on the MM9 skeleton (2026-10-30, user review of v2: back to the MM9 skeleton and clips, as Annud
and Yrsa). Input work/head_v1.blend (the shared graft_hands.py + head_split.py result on the v1 MM9 fit), output
work/head_v3.blend for build_runtime_v2.sh (BLEND=v2/work/head_v3.blend). Writes work/v3_rig.json.

1. Finger bones: Forad's graft ran without `add_bones` (v2 rigged the fingers on its own playbook rig), so the MPFB
   finger weights had no bones on MM9_Rig. The 15 bones per side are added exactly as graft_hands.py does for Annud
   and Yrsa (`add_bones` of v3_rig.json): head at the MPFB joint (work/hands_v1.json), rest frame copied from the MM9
   mitten bone (Finger0/01, Finger1/11), length to the next joint. clips_mm9.py drives them through `finger_alias`.
2. Knees: the v1 fit put the MM9 knees 10-12 cm low against the HD body (Meshy's auto-rig and the leg shape agree).
   Each Calf joint moves to the leg slice centre at the Meshy knee height (work/joints_final.json, sides swapped,
   minus the Scene Root height); rest rotation, length and the Foot joint are unchanged. Thigh/Calf weights are then
   re-split along the hip -> ankle axis by a smoothstep of +/- `knee_band` around the new knee (the old split sat at the
   old knee, so the shin bent above the boot); other bones' weights are kept.
3. Chin: the MM9 skin blended Head into Neck across the jaw and chin (purple in the weight map), so the chin stretched
   when the head turned (v1 "cut-looking chin"). Head + Neck weight is re-split by a plane through the bottom of the chin
   and the nape at the skull base (x axis in the plane), moved down by `chin_drop`: above it all Head, fading over
   `chin_band` below it; a vertex only ever gains Head weight (the MM9 neck blend below the jaw stays). Vertices
   weighted to the ponytail are left alone.
4. Jewellery: small loose parts (<= `max_verts`) with their centre inside `jewellery.box_lo/hi` and within `max_dist`
   of the skin take the weights of the nearest skin vertex, so necklace beads ride on the chest.
Args: -- <config json>"""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
CFG = json.load(open(sys.argv[sys.argv.index('--') + 1]))
V2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda p: p if os.path.isabs(p) else os.path.join(V2, p)
bpy.ops.wm.open_mainfile(filepath=P(CFG['blend_in']))
rig = bpy.data.objects[CFG.get('rig', 'MM9_Rig')]; body = bpy.data.objects[CFG.get('body', 'Body')]
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
CO = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
rep = {}


def groups(names):
    return {body.vertex_groups[n].index for n in names if n in body.vertex_groups}


def wmat(names):
    """Per vertex weight of each named group (n x k)."""
    idx = {body.vertex_groups[n].index: k for k, n in enumerate(names) if n in body.vertex_groups}
    W = np.zeros((len(me.vertices), len(names)))
    for v in me.vertices:
        for g in v.groups:
            if g.group in idx:
                W[v.index, idx[g.group]] = g.weight
    return W


def set_w(vi, name, w):
    g = body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
    if w > 1e-4:
        g.add([int(vi)], float(w), 'REPLACE')
    else:
        g.remove([int(vi)])


smooth = lambda e0, e1, x: np.clip((x - e0) / (e1 - e0), 0, 1) ** 2 * (3 - 2 * np.clip((x - e0) / (e1 - e0), 0, 1))
J = json.load(open(P(CFG['hands_json'])))['joints']
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
# ---------------------------------------------------------------- 1. finger bones
err = 0.0
for key in ('L', 'R'):
    jj = J[key]
    for mp, spec in CFG['add_bones'].items():
        name = spec['name'].replace('{S}', key)
        tmpl = eb[spec['template'].replace('{S}', key)]
        b = eb.get(name) or eb.new(name)
        Rt = tmpl.matrix.to_3x3()
        hp = Vector(jj[mp]); f, j = mp[6], int(mp[8])
        nxt = jj[f'finger{f}-{j + 1}'] if j < 3 else jj[f'finger{f}-3_tip']
        ln = max((Vector(nxt) - hp).length, 0.01)
        b.head = hp; b.tail = hp + Rt.col[1] * ln; b.align_roll(Rt.col[2])
        b.parent = eb[spec['parent'].replace('{S}', key)]; b.use_connect = False; b.use_deform = True
        err = max(err, math.degrees(b.matrix.to_3x3().to_quaternion().rotation_difference(Rt.to_quaternion()).angle))
rep['finger_bones'] = 2 * len(CFG['add_bones']); rep['finger_frame_err_deg'] = round(err, 4)
# ---------------------------------------------------------------- 2. knees
JF = json.load(open(P(CFG['knees']['joints_json'])))['joints']
root_z = CFG['knees']['root_z']
knee = {}
for side, src in CFG['knees']['sides'].items():          # MM9 side -> joints_final key (sides swapped)
    calf, thigh, foot = (eb[f'Bip01 {side} {n}'] for n in ('Calf', 'Thigh', 'Foot'))
    tz = JF[src][2] - root_z
    W = wmat([thigh.name, calf.name])
    leg = (W.sum(1) > 0.5) & (np.abs(CO[:, 2] - tz) < 0.012) & (np.sign(CO[:, 0]) == np.sign(calf.head.x))
    c = CO[leg].mean(0)
    target = Vector((float(c[0]), float(c[1]), tz))
    old = calf.head.copy(); foot_head = foot.head.copy()
    foot.use_connect = False
    for ch in calf.children:
        ch.use_connect = False
    m = calf.matrix.copy(); m.translation = target; calf.matrix = m
    assert (foot.head - foot_head).length < 1e-6
    knee[side] = dict(old=list(old), new=list(target), hip=list(thigh.head), ankle=list(foot.head),
                      thigh=thigh.name, calf=calf.name, slice_verts=int(leg.sum()))
    rep.setdefault('knees', {})[side] = {'moved_cm': [round(100 * x, 1) for x in (target - old)],
                                         'new': [round(x, 4) for x in target]}
bpy.ops.object.mode_set(mode='OBJECT')
B = CFG['knees'].get('knee_band', 0.04)
for side, k in knee.items():
    W = wmat([k['thigh'], k['calf']]); s = W.sum(1)
    hip, kn, ank = (np.array(k[x]) for x in ('hip', 'new', 'ankle'))
    ax = ank - hip; ax /= np.linalg.norm(ax)
    d = (CO - kn) @ ax                                  # signed distance past the new knee toward the ankle
    cf = smooth(-B, B, d)
    changed = 0
    for vi in np.where(s > 1e-4)[0]:
        wt, wc = s[vi] * (1 - cf[vi]), s[vi] * cf[vi]
        if abs(wc - W[vi, 1]) > 1e-3:
            changed += 1
        set_w(vi, k['thigh'], wt); set_w(vi, k['calf'], wc)
    rep['knees'][side]['reweighted_verts'] = changed
# ---------------------------------------------------------------- 3. chin
ch = CFG['chin']
hb = rig.data.bones['Bip01 Head']; H0 = rig.matrix_world @ hb.head_local
names = ['Bip01 Head', 'Bip01 Neck'] + ch.get('keep_bones', [])
W = wmat(names); s = W[:, 0] + W[:, 1]; keep = W[:, 2:].sum(1) if W.shape[1] > 2 else np.zeros(len(W))
mid = np.abs(CO[:, 0] - H0.x) < 0.015
front = mid & (CO[:, 1] < H0.y - 0.04) & (W[:, 0] > 0.3)
chin = CO[front][np.argmin(CO[front][:, 2])]
back = mid & (CO[:, 1] > H0.y + 0.02) & (s > 0.5) & (keep < 0.1)
nape = CO[back][np.argmin(np.abs(CO[back][:, 2] - H0.z))]
t = np.array([0, nape[1] - chin[1], nape[2] - chin[2]]); t /= np.linalg.norm(t)
n = np.array([0, -t[2], t[1]])                          # up normal of the jaw plane (x axis lies in it)
if n[2] < 0:
    n = -n
d = (CO - chin) @ n + ch.get('chin_drop', 0.01)
h = smooth(-ch.get('chin_band', 0.03), 0.0, d)
changed = 0
for vi in np.where((s > 1e-4) & (keep < 0.1))[0]:
    hv = max(h[vi], W[vi, 0] / s[vi])                 # only ever more Head: the MM9 neck blend below stays
    if abs(hv - W[vi, 0] / s[vi]) > 1e-3:
        changed += 1
        set_w(vi, 'Bip01 Head', s[vi] * hv); set_w(vi, 'Bip01 Neck', s[vi] * (1 - hv))
rep['chin'] = {'chin': [round(float(x), 4) for x in chin], 'nape': [round(float(x), 4) for x in nape],
               'reweighted_verts': changed}
# ---------------------------------------------------------------- 4. jewellery follows the skin
# small loose parts on the chest (necklace beads and teeth) carry the weights of the skin under them, so they ride on
# it (detached-parts audit 2026-10-30: one 6-triangle bead, weighted to Spine3 over Neck-weighted skin, lifted 6 mm)
jw = CFG.get('jewellery')
if jw:
    import bmesh
    from mathutils.kdtree import KDTree
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    comp = -np.ones(len(bm.verts), np.int32); cid = 0
    for v in bm.verts:
        if comp[v.index] >= 0:
            continue
        st = [v]; comp[v.index] = cid
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if comp[y.index] < 0:
                    comp[y.index] = cid; st.append(y)
        cid += 1
    bm.free()
    sizes = np.bincount(comp); shell = int(np.argmax(sizes))
    kd = KDTree(int((comp == shell).sum()))
    for i in np.where(comp == shell)[0]:
        kd.insert(Vector(CO[i]), int(i))
    kd.balance()
    lo, hi = np.array(jw['box_lo']), np.array(jw['box_hi'])
    moved = 0
    for k in range(cid):
        vs = np.where(comp == k)[0]
        if k == shell or len(vs) > jw.get('max_verts', 40):
            continue
        c = CO[vs].mean(0)
        if not ((c >= lo).all() and (c <= hi).all()):
            continue
        _, src, dist = kd.find(Vector(c))
        if dist > jw.get('max_dist', 0.03):
            continue
        sw = [(body.vertex_groups[g.group].name, g.weight) for g in me.vertices[src].groups if g.weight > 1e-4]
        for vi in vs:
            for g in list(me.vertices[vi].groups):
                body.vertex_groups[g.group].remove([int(vi)])
            for nm, wt in sw:
                body.vertex_groups[nm].add([int(vi)], wt, 'REPLACE')
        moved += 1
    rep['jewellery_parts_rebound'] = moved
bpy.ops.wm.save_as_mainfile(filepath=P(CFG['blend_out']))
json.dump(rep, open(P(CFG['report']), 'w'), indent=1)
print('V3RIG', json.dumps(rep))
