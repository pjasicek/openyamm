"""Five-finger hands for a rigged, textured Meshy body: posed MPFB (MakeHuman, CC0) hands grafted at the cuff.

User review 2026-10-30 (MM9 Isle of Ashes villagers): the Meshy hands had four fused/warped fingers and a spiked thumb.
Route after mm6_cle_claude (hands_mpfb.py / fit_hands.py), but grafted into the body mesh before the finger rig so
every finger is its own chain:
1. MPFB human (macro from the config), `default` rig, a relaxed rest curl (config `curl`, degrees per finger MCP;
   PIP x1.1, DIP x0.8) and fingers drawn together (`spread`). The hand (hand-bone weight > 0.02) plus a forearm stub is
   cut from the posed, helper-free mesh and decimated to `hand_tris` triangles.
2. Our old hand: skin-class faces (textures/<prefix>_material_classes.png = 1) past the cuff (the farthest non-skin
   arm face along the forearm axis: bracer, sleeve end) minus `cut_margin` are deleted. Its frame: finger direction
   = first PCA axis of the old hand vertices, palm normal = the smallest axis, thumb side signed by the rig's thumb
   joint. MPFB frame: wrist -> middle knuckle, palm normal from PCA, signed toward its index. Uniform scale by hand
   length (wrist -> farthest vertex along the finger direction).
3. Conform: MPFB vertices before the cuff edge are pulled inside the cut opening (0.97 x its radius per angle about
   the forearm axis); over `blend` metres past the edge the radius eases from the opening's to MPFB's own.
4. The hands join 'Body'. Face attribute `hand` (1 = new hand face); UV layers: `MHUV` (MakeHuman layout, for the
   skin bake) and `HeadUV` (the hand's square in the head texture set, config `squares`). Vertex groups
   `MP_<mpfb bone>` hold MPFB's own hand weights; vertex attribute `graft_s` (0 stub .. 1 hand) and `graft_side`.
5. Weights (config `bone_map`, MPFB bone -> our bone): graft_s * mapped MPFB weights + (1 - graft_s) * the weights of
   the nearest kept old vertex. With `add_bones`, the finger bones are first created at the MPFB joints with the rest
   frame of the named template bone (MM9 mitten chains: every finger MCP takes Finger1's frame, so the MM9 clips'
   mitten curl can be copied onto each finger; see clips_mm9.py `finger_alias`).
Writes <out blend> and <out json> (frames, scale, joints in our space). Args: -- <config json>"""
import bpy, bmesh, json, math, os, sys
import addon_utils
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

CFG = json.load(open(sys.argv[sys.argv.index('--') + 1]))
PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda p: p if os.path.isabs(p) else os.path.join(PROJ, p)
FING = {f: [f'finger{f}-{j}' for j in (1, 2, 3)] for f in range(1, 6)}
HANDB = ['wrist'] + [f'metacarpal{i}' for i in range(1, 5)]

# ------------------------------------------------------------------ MPFB hands
addon_utils.enable("bl_ext.blender_org.mpfb", default_set=True)
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.blender_org.mpfb", default_set=True)
macro = {"gender": 1.0, "age": 0.5, "muscle": 0.5, "weight": 0.5, "proportions": 0.5, "height": 0.5, "cupsize": 0.5,
         "firmness": 0.5, "race": {"asian": 0.33, "caucasian": 0.34, "african": 0.33}}
macro.update(CFG.get('macro', {}))
h = HumanService.create_human(macro_detail_dict=macro)
mrig = HumanService.add_builtin_rig(h, "default")
mask = next(m for m in h.modifiers if m.type == 'MASK')
MASK_GROUP, MASK_INV = mask.vertex_group, mask.invert_vertex_group
mask.show_viewport = False; mask.show_render = False
dg = lambda: bpy.context.evaluated_depsgraph_get()
nvm = len(h.data.vertices)
names = {g.index: g.name for g in h.vertex_groups}
WM = {}
for v in h.data.vertices:
    for g in v.groups:
        WM.setdefault(names[g.group], np.zeros(nvm))[v.index] = g.weight
bodymask = WM.get(MASK_GROUP, np.zeros(nvm)) > .5
if MASK_INV:
    bodymask = ~bodymask


def MJ(name, tail=False):
    pb = mrig.pose.bones[name]
    return mrig.matrix_world @ (pb.tail if tail else pb.head)


def flex_sign(bone, n):
    pb = mrig.pose.bones[bone]; pb.rotation_mode = 'XYZ'
    t0 = MJ(bone, True); pb.rotation_euler = (0.3, 0, 0); bpy.context.view_layer.update()
    t1 = MJ(bone, True); pb.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
    return 1.0 if (t1 - t0).dot(n) > 0 else -1.0


def mframe(sfx):
    w = MJ('wrist' + sfx); m3 = MJ('finger3-1' + sfx); i2 = MJ('finger2-1' + sfx); p5 = MJ('finger5-1' + sfx)
    hd = (m3 - w).normalized(); t = (i2 - p5); t = (t - hd * t.dot(hd)).normalized()
    n = t.cross(hd) if sfx == '.R' else hd.cross(t)
    return w, hd, t, n.normalized()


curl = CFG.get('curl', [6, 8, 11, 14])            # index, middle, ring, pinky MCP degrees (relaxed rest)
spread = CFG.get('spread', [6, 1, -4, -9])         # fingers drawn together (local Z degrees)
thumb = CFG.get('thumb', [0, 4, 6])                # thumb: CMC swing toward the palm, MCP, IP flex
for sfx in ('.L', '.R'):
    w, hd, t, n = mframe(sfx)
    for f, deg, sp in zip((2, 3, 4, 5), curl, spread):
        for b, k in zip(FING[f], (1.0, 1.1, 0.8)):
            s = flex_sign(b + sfx, n)
            pb = mrig.pose.bones[b + sfx]; pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (s * math.radians(deg * k), 0, math.radians(sp) if b.endswith('-1') else 0)
    for b, a in zip(FING[1], thumb):
        s = flex_sign(b + sfx, n)
        pb = mrig.pose.bones[b + sfx]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (s * math.radians(a), 0, 0)
bpy.context.view_layer.update()
ev = h.evaluated_get(dg()); me_ev = ev.to_mesh()
PM = np.array([(h.matrix_world @ v.co)[:] for v in me_ev.vertices]); ev.to_mesh_clear()
MPFB = {}
for sfx in ('.L', '.R'):
    w, hd, t, n = mframe(sfx)
    hw = sum(WM.get(b + sfx, 0) for b in HANDB + sum(FING.values(), []))
    hv = np.where((hw > 0.5) & bodymask)[0]
    rel = PM[hv] - np.array(w[:])
    L = float((rel @ np.array(hd[:])).max())
    c = PM[hv].mean(0); U = np.linalg.svd(PM[hv] - c)[2]
    nn = Vector(U[2].tolist()); nn = (nn - hd * nn.dot(hd)).normalized()
    if nn.dot(n) < 0:
        nn = -nn
    tt = nn.cross(hd).normalized()
    if tt.dot(t) < 0:
        tt = -tt
    joints = {b: MJ(b + sfx) for b in HANDB + sum(FING.values(), [])}
    for f in range(1, 6):
        joints[f'finger{f}-3_tip'] = MJ(f'finger{f}-3' + sfx, True)
    MPFB[sfx] = dict(w=w, h=hd, t=tt, n=nn, L=L, hw=hw, joints=joints, x=float(w.x))
# cut each hand (+ forearm stub) out of the posed helper-free mesh
STUB_F = CFG.get('stub_frac', 0.25)              # forearm stub, fraction of the hand length
cut = {}
for sfx in ('.L', '.R'):
    F = MPFB[sfx]
    me = bpy.data.meshes.new_from_object(h.evaluated_get(dg()), preserve_all_data_layers=True, depsgraph=dg())
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    keep = set()
    for v in bm.verts:
        if v.index >= nvm or not bodymask[v.index]:
            continue
        p = h.matrix_world @ v.co
        armw = F['hw'][v.index] + WM.get('lowerarm02' + sfx, np.zeros(nvm))[v.index] + WM.get('lowerarm01' + sfx, np.zeros(nvm))[v.index]
        if F['hw'][v.index] > 0.5 or ((p - F['w']).dot(F['h']) > -STUB_F * F['L'] and armw > 0.3):
            keep.add(v.index)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(v.index in keep for v in f.verts)], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    # largest connected piece
    bm.faces.ensure_lookup_table()
    comp = {}; cid = 0
    for f in bm.faces:
        if f.index in comp:
            continue
        st = [f]; comp[f.index] = cid
        while st:
            x = st.pop()
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in comp:
                        comp[y.index] = cid; st.append(y)
        cid += 1
    big = max(range(cid), key=lambda c: sum(1 for v in comp.values() if v == c))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if comp[f.index] != big], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.transform(h.matrix_world)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('Hand' + sfx, me); bpy.context.scene.collection.objects.link(o)
    cut[sfx] = o
# keep each hand with only its own MPFB groups (as named vertex groups, carried by the decimation)
for sfx, o in cut.items():
    keepg = [b + sfx for b in HANDB + sum(FING.values(), [])] + ['lowerarm02' + sfx, 'lowerarm01' + sfx]
    for g in list(o.vertex_groups):
        if g.name not in keepg:
            o.vertex_groups.remove(g)
for o in list(bpy.data.objects):
    if o not in cut.values():
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=P('work/mpfb_hands_tmp.blend'))
mp_data = {sfx: {k: (list(v) if isinstance(v, Vector) else v) for k, v in F.items() if k not in ('hw', 'joints')}
           for sfx, F in MPFB.items()}
mp_joints = {sfx: {k: list(v) for k, v in F['joints'].items()} for sfx, F in MPFB.items()}

# ------------------------------------------------------------------ our body
bpy.ops.wm.open_mainfile(filepath=P(CFG['blend_in']))
rig = bpy.data.objects[CFG['rig']]; body = bpy.data.objects[CFG['body']]
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
with bpy.data.libraries.load(P('work/mpfb_hands_tmp.blend')) as (src, dst):
    dst.objects = ['Hand.L', 'Hand.R']
for o in dst.objects:
    bpy.context.scene.collection.objects.link(o)
HANDS = {o.name[-2:]: o for o in dst.objects}
me = body.data
mw = body.matrix_world
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
# face classes from the material class map (1 skin)
img = bpy.data.images.load(P(CFG['classes_png']))
IW, IH = img.size
cls = np.array(img.pixels[:], np.float32).reshape(IH, IW, img.channels)[..., 0] * 255
uvl = me.uv_layers[CFG.get('uv', 'UVMap')].data
FC = np.zeros(len(me.polygons), np.int32)
FCEN = np.zeros((len(me.polygons), 3))
for p in me.polygons:
    u = np.mean([uvl[l].uv[0] for l in p.loop_indices]); v = np.mean([uvl[l].uv[1] for l in p.loop_indices])
    FC[p.index] = int(round(cls[min(IH - 1, max(0, int(v * IH))), min(IW - 1, max(0, int(u * IW)))]))
    FCEN[p.index] = CO[list(p.vertices)].mean(0)
bones = rig.data.bones
RJ = lambda n: rig.matrix_world @ bones[n].head_local
report = {'sides': {}}
del_faces = set()
OUR = {}
for key, sd in CFG['sides'].items():
    W = RJ(sd['hand']); E = RJ(sd['forearm']); T0 = RJ(sd['thumb'])
    d = (W - E).normalized()
    Wn, dn = np.array(W[:]), np.array(d[:])
    rel = FCEN - Wn
    along = rel @ dn
    radial = np.linalg.norm(rel - np.outer(along, dn), axis=1)
    arm = (radial < sd.get('arm_radius', 0.12)) & (along > -0.25) & (along < 0.3) & (np.sign(FCEN[:, 0]) == np.sign(Wn[0]))
    cuff = float(np.percentile(along[arm & np.isin(FC, CFG.get('cuff_classes', [8, 9])) & (along < sd.get('cuff_max', 0.08))],
                               sd.get('cuff_percentile', 100)))     # < 100: ignore a few mislabelled skin-coloured faces
    a_cut = cuff - CFG.get('cut_margin', 0.008)
    # inside a sleeve (before the cuff) only the wrist skin goes, never the sleeve lining (Meshy paints parts of it skin)
    inner = (along >= cuff) | (radial < sd.get('inner_radius', 0.045))
    dels = np.where(arm & (FC == 1) & (along > a_cut) & inner)[0]
    # centroid rule (an all-vertices rule left old skin shards poking out of a sleeve end); with `poke` also every
    # skin face that reaches past the cuff edge by that much (shards at a tight bracer's rim)
    vrel = CO - Wn; valong = vrel @ dn
    dels = set(dels.tolist())
    if sd.get('poke') is not None:
        for i in np.where(arm)[0]:                       # any class: bracer-rim slivers past the cuff go too
            if valong[list(me.polygons[i].vertices)].max() > cuff + sd['poke'] and along[i] > cuff - 0.006:
                dels.add(int(i))
    if sd.get('rim_clean'):
        # a tight bracer's rim: faces near the cuff edge far inside or outside the bracer's own radius are old wrist
        # skin slivers (some carry metal labels) poking out under the rim
        band = arm & np.isin(FC, CFG.get('cuff_classes', [8, 9])) & (along > cuff - 0.025) & (along <= cuff)
        r_med = float(np.median(radial[band]))
        for i in np.where(arm & (along > cuff - 0.012))[0]:
            if abs(radial[i] - r_med) > 0.35 * r_med:
                dels.add(int(i))
        report.setdefault('rim', {})[key] = round(r_med, 4)
    dels = sorted(dels)
    del_faces.update(dels)
    hv = np.unique(np.concatenate([list(me.polygons[i].vertices) for i in dels]))
    hv = hv[valong[hv] > cuff]                      # the hand proper (PCA, length): not the wrist inside a sleeve
    c = CO[hv].mean(0); U = np.linalg.svd(CO[hv] - c)[2]
    hd = Vector(U[0].tolist())
    if hd.dot(Vector(c.tolist()) - W) < 0:
        hd = -hd
    nn = Vector(U[2].tolist()); nn = (nn - hd * nn.dot(hd)).normalized()
    if nn.dot(Vector(sd.get('palm', [0, 0, -1]))) < 0:
        nn = -nn
    tt = nn.cross(hd).normalized()
    if tt.dot(T0 - Vector(c.tolist())) < 0:
        tt = -tt
    L = float(((CO[hv] - Wn) @ np.array(hd[:])).max())
    OUR[key] = dict(W=W, d=d, h=hd, t=tt, n=nn, L=L, cuff=cuff, a_cut=a_cut, hv=hv)
    report['sides'][key] = {'cuff_along_m': round(cuff, 4), 'deleted_faces': len(dels), 'old_hand_verts': int(len(hv)),
                            'hand_len_m': round(L, 4), 'h': [round(x, 3) for x in hd], 'n': [round(x, 3) for x in nn]}
# conform target: the ORIGINAL skin surface of this arm (all its skin faces, before the cut), ray cast from the forearm
# axis (a ring of cut vertices was unreliable: in wide sleeves it ran along the sleeve rim)
from mathutils.bvhtree import BVHTree
kept_v = set(v for p in me.polygons if p.index not in del_faces for v in p.vertices)
for key, O in OUR.items():
    sd = CFG['sides'][key]
    Wn, dn = np.array(O['W'][:]), np.array(O['d'][:])
    rel = FCEN - Wn; al = rel @ dn; rad = np.linalg.norm(rel - np.outer(al, dn), axis=1)
    sel = np.where((FC == 1) & (rad < sd.get('arm_radius', 0.12)) & (al > O['a_cut'] - 0.06) & (al < 0.3) &
                   (np.sign(FCEN[:, 0]) == np.sign(Wn[0])))[0]
    vidx = sorted(set(v for i in sel for v in me.polygons[i].vertices)); remap = {v: k for k, v in enumerate(vidx)}
    O['bvh'] = BVHTree.FromPolygons([Vector(CO[v].tolist()) for v in vidx],
                                    [[remap[v] for v in me.polygons[i].vertices] for i in sel])
    # every kept arm surface (sleeve, bracer, skin): the stub must stay inside it
    sel2 = np.where((rad < sd.get('arm_radius', 0.12)) & (al > O['a_cut'] - 0.15) & (al < 0.3) &
                    (np.sign(FCEN[:, 0]) == np.sign(Wn[0])))[0]
    sel2 = np.array([i for i in sel2 if i not in del_faces])
    vidx = sorted(set(v for i in sel2 for v in me.polygons[i].vertices)); remap = {v: k for k, v in enumerate(vidx)}
    O['bvh_all'] = BVHTree.FromPolygons([Vector(CO[v].tolist()) for v in vidx],
                                        [[remap[v] for v in me.polygons[i].vertices] for i in sel2])
    O['edge_along'] = O['a_cut']
# old weights (kept vertices only) for the stub
gname = {g.index: g.name for g in body.vertex_groups}
kv = np.array(sorted(kept_v))
kd = KDTree(len(kv))
for k, i in enumerate(kv):
    kd.insert(CO[i], k)
kd.balance()


def frame(xa, ya):
    x = xa.normalized(); y = (ya - x * ya.dot(x)).normalized()
    return Matrix((x, y, x.cross(y))).transposed()


# ------------------------------------------------------------------ optional finger bones
BMAP = dict(CFG['bone_map'])                       # '<mpfb bone>' -> '<our bone>' with {S} = side token
joints_out = {}
for key, O in OUR.items():
    sd = CFG['sides'][key]
    sfx = '.L' if (MPFB['.L']['x'] > 0) == (O['W'].x > 0) else '.R'
    F = MPFB[sfx]
    S = CFG.get('hand_scale') or O['L'] / F['L']     # hand_scale: one size for both hands (a noisy old hand reads 7 % apart)
    # frames from (finger direction, palm normal): both are well defined; the thumb side follows from the same-side
    # MPFB hand (a cross-product thumb axis flipped the palm up on one side)
    Rm = frame(O['h'], O['n']) @ frame(Vector(F['h']), Vector(F['n'])).inverted()
    T = Matrix.Translation(O['W']) @ (Rm.to_4x4() @ Matrix.Scale(S, 4)) @ Matrix.Translation(-Vector(F['w']))
    O.update(sfx=sfx, S=S, T=T)
    joints_out[key] = {k: list(T @ Vector(v)) for k, v in mp_joints[sfx].items()}
    th = T @ Vector(mp_joints[sfx]['finger1-2']); ix = T @ Vector(mp_joints[sfx]['finger5-1'])
    T0 = RJ(CFG['sides'][key]['thumb'])
    report['sides'][key].update(mpfb_side=sfx, scale=round(S, 4),
                                thumb_side_ok=bool((th - ix).dot(T0 - O['W']) > (ix - th).dot(T0 - O['W'])))
if CFG.get('add_bones'):
    bpy.context.view_layer.objects.active = rig
    for o in bpy.data.objects:
        o.select_set(o == rig)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = rig.data.edit_bones
    for key, O in OUR.items():
        sd = CFG['sides'][key]
        J = joints_out[key]
        for mp, spec in CFG['add_bones'].items():      # mp: 'finger2-1' -> {"name": "...{S}...", "template": "...", "parent": "..."}
            name = spec['name'].replace('{S}', sd['token'])
            tmpl = eb[spec['template'].replace('{S}', sd['token'])]
            par = spec['parent'].replace('{S}', sd['token'])
            b = eb.get(name) or eb.new(name)
            Rt = tmpl.matrix.to_3x3()
            hp = Vector(J[mp]); f, j = mp[6], int(mp[8])
            nxt = J[f'finger{f}-{j + 1}'] if j < 3 else J[f'finger{f}-3_tip']
            ln = max((Vector(nxt) - hp).length, 0.01)
            b.head = hp; b.tail = hp + Rt.col[1] * ln; b.align_roll(Rt.col[2])
            b.parent = eb[par]; b.use_connect = False; b.use_deform = True
            err = math.degrees(b.matrix.to_3x3().to_quaternion().rotation_difference(Rt.to_quaternion()).angle)
            report.setdefault('bone_frame_err_deg', 0.0)
            report['bone_frame_err_deg'] = max(report['bone_frame_err_deg'], round(err, 4))
    bpy.ops.object.mode_set(mode='OBJECT')
# ------------------------------------------------------------------ place, conform, UV, weights, join
for key, O in OUR.items():
    o = HANDS[O['sfx']]
    o.data.transform(O['T']); o.matrix_world = Matrix.Identity(4)
    # decimate to the triangle budget (collapse keeps groups and UVs)
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.context.view_layer.objects.active = o
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    dm = o.modifiers.new('Dec', 'DECIMATE'); dm.ratio = min(1.0, CFG.get('hand_tris', 700) / tris)
    dm.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=dm.name)
    Wn, dn = np.array(O['W'][:]), np.array(O['d'][:])
    edge = O['edge_along']; blend = CFG.get('blend', 0.02); bvh = O['bvh']
    sv = np.zeros(len(o.data.vertices)); pulled = 0
    for v in o.data.vertices:
        p = np.array(v.co[:]); a = (p - Wn) @ dn
        ax = Wn + a * dn; qr = p - ax; r = np.linalg.norm(qr)
        s = 0.0 if a < edge else (1.0 if a >= edge + blend else (a - edge) / blend)
        s = s * s * (3 - 2 * s)
        sv[v.index] = s
        if r < 1e-6:
            continue
        if a < edge + blend:
            hit = O['bvh_all'].ray_cast(Vector(ax.tolist()), Vector((qr / r).tolist()), 0.2)
            if hit[0] is not None:
                r_in = (np.array(hit[0][:]) - ax) @ (qr / r)
                if 0 < r_in and r > CFG.get('inside', 0.92) * r_in:
                    r = CFG.get('inside', 0.92) * r_in; p = ax + qr / np.linalg.norm(qr) * r; qr = p - ax; pulled += 1
                    v.co = Vector(p.tolist())
        if s >= 1.0:
            continue
        hit = bvh.ray_cast(Vector(ax.tolist()), Vector((qr / r).tolist()), 0.2)
        if hit[0] is None:
            continue
        r_old = (np.array(hit[0][:]) - ax) @ (qr / r)
        r_old = min(r_old, 1.35 * r)                    # never flare the stub out (sleeve rims)
        r_new = min(r, 0.95 * r_old) if a < edge else r_old * (1 - s) + r * s
        v.co = Vector((ax + qr / r * r_new).tolist()); pulled += 1
    report['sides'][key]['conformed_verts'] = pulled
    o['graft_s'] = sv.tolist()
    # UV: MakeHuman layout kept as MHUV; HeadUV = Smart UV packed into this hand's square
    o.data.uv_layers[0].name = 'MHUV'
    uv = o.data.uv_layers.new(name='HeadUV'); o.data.uv_layers.active = uv
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    u0, v0, side = CFG['squares'][key]
    for l in o.data.uv_layers['HeadUV'].data:
        l.uv = (u0 + l.uv[0] * side, v0 + l.uv[1] * side)
    # weights
    mpw = {g.name: np.zeros(len(o.data.vertices)) for g in o.vertex_groups}
    gi = {g.index: g.name for g in o.vertex_groups}
    for v in o.data.vertices:
        for g in v.groups:
            mpw[gi[g.group]][v.index] = g.weight
    o.vertex_groups.clear()
    sd = CFG['sides'][key]
    tok = sd['token']
    out_w = [dict() for _ in o.data.vertices]
    for mpname, arr in mpw.items():
        base = mpname[:-2]
        tgt = BMAP.get(base, BMAP.get('*'))
        tgt = tgt.replace('{S}', tok).replace('{HAND}', sd['hand']).replace('{FOREARM}', sd['forearm'])
        for i in np.where(arr > 1e-4)[0]:
            out_w[i][tgt] = out_w[i].get(tgt, 0) + arr[i]
        g = o.vertex_groups.new(name='MP_' + base)
        for i in np.where(arr > 1e-4)[0]:
            g.add([int(i)], float(arr[i]), 'REPLACE')
    for v in o.data.vertices:
        s = sv[v.index]
        tot = sum(out_w[v.index].values()) or 1.0
        wv = {k: x / tot * s for k, x in out_w[v.index].items()}
        if s < 1.0:
            _, k, _ = kd.find(v.co)
            src = me.vertices[int(kv[k])]
            ow = {gname[g.group]: g.weight for g in src.groups if g.weight > 1e-4}
            tot = sum(ow.values()) or 1.0
            for nme, x in ow.items():
                wv[nme] = wv.get(nme, 0) + x / tot * (1 - s)
        for nme, x in wv.items():
            if x > 1e-4:
                (o.vertex_groups.get(nme) or o.vertex_groups.new(name=nme)).add([v.index], x, 'REPLACE')
    a = o.data.attributes.new('graft_s', 'FLOAT', 'POINT'); a.data.foreach_set('value', sv.tolist())
    a = o.data.attributes.new('graft_side', 'INT', 'POINT'); a.data.foreach_set('value', [int(key == list(OUR)[1])] * len(sv))
    a = o.data.attributes.new('hand', 'INT', 'FACE'); a.data.foreach_set('value', [1] * len(o.data.polygons))
    for p in o.data.polygons:
        p.use_smooth = True
    report['sides'][key]['new_tris'] = sum(len(p.vertices) - 2 for p in o.data.polygons)
    report['sides'][key]['stub_verts'] = int((sv < 1).sum())
# delete the old hand faces
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in sorted(del_faces)], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# small leftover pieces of the cut (old skin shards inside a sleeve) go too
bm.verts.ensure_lookup_table()
seen = set(); frag = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; part = [v]; seen.add(v.index)
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); st.append(y); part.append(y)
    if len(part) < CFG.get('fragment_verts', 40):
        pc = np.array([tuple(mw @ q.co) for q in part]).mean(0)
        if any(np.linalg.norm(pc - np.array(O['W'][:])) < 0.2 for O in OUR.values()):
            frag += part
bmesh.ops.delete(bm, geom=frag, context='VERTS')
report['fragments_removed_verts'] = len(frag)
bm.to_mesh(me); bm.free()
for ln in ('MHUV', 'HeadUV'):
    if ln not in me.uv_layers:
        me.uv_layers.new(name=ln)
if 'hand' not in me.attributes:
    me.attributes.new('hand', 'INT', 'FACE')
# join (body keeps its object, modifiers and parent); hands are in world space, body has its own matrix
inv = body.matrix_world.inverted()
for o in HANDS.values():
    o.data.transform(inv)
    for ln in [l.name for l in me.uv_layers]:
        if ln not in o.data.uv_layers:
            o.data.uv_layers.new(name=ln)
for o in bpy.data.objects:
    o.select_set(o in list(HANDS.values()) + [body])
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
me = body.data
me.uv_layers.active = me.uv_layers[CFG.get('uv', 'UVMap')]
for ln in [l.name for l in me.uv_layers]:
    me.uv_layers[ln].active_render = (ln == CFG.get('uv', 'UVMap'))
# keep the body material on the new faces
for p in me.polygons:
    p.material_index = 0
report['tris_after'] = sum(len(p.vertices) - 2 for p in me.polygons)
report['joints'] = joints_out
report['frames'] = {k: {'S': O['S'], 'sfx': O['sfx'], 'W': list(O['W']), 'h': list(O['h']), 't': list(O['t']),
                        'n': list(O['n']), 'edge_along': O['edge_along'], 'd': list(O['d'])} for k, O in OUR.items()}
os.makedirs(os.path.dirname(P(CFG['json_out'])), exist_ok=True)
json.dump(report, open(P(CFG['json_out']), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=P(CFG['blend_out']))
print('GRAFT', json.dumps({k: v for k, v in report.items() if k not in ('joints', 'frames')}))
