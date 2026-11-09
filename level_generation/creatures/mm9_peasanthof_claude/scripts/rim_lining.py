"""Lining behind open garment rims (2026-11-02, user on PeasantDM2: "holes in sleeves + some in knees (e.g. running
anim 12)"). Meshy's cloth and leather are single-sided: through an open rim (a boot top) the view meets the garment's
back faces, which the game culls, and shows the background.

For each open boundary loop of body faces (no `head`/`hand` attribute) whose vertices are mostly weighted to one of
`bones` (keywords, e.g. Calf) and whose centre lies within `zmin`..`zmax` (Blender rest, optional): the band of body
faces reachable from the loop through faces whose vertices all lie within `depth` (m) of the loop's vertices and are
mostly weighted to `band_bones` is duplicated `offset` behind itself along the area-weighted vertex normal, flipped, with
the twins' weights (the deform layer is duplicated), so the inside follows the outside under any pose (sleeve_lining.py's
technique, there for the forearm bones only). The loop's edges are joined to their twins by a rim strip facing out of the
garment. Lining and rim take one dark texel of the band's own paint: the roughest face among the darkest `dark_pct` %
of band faces whose region mask label is `region` (R tunic, G trousers, B boots, A belt; region_variants.py then
recolours it with that region's tier ramp). The bands of the selected loops of one side are united and lined once
(a boot's turned-down cuff has two rims 1-2 cm apart), and every selected rim is joined to that lining.
With skip_inner=1, band faces that face their dominant bone's axis (normal against the direction from the bone segment,
< -0.2: Meshy's own inner layer) are not lined: in the sleeves their twin sat outside the cloth as dark patches. Elsewhere
(collar, belt, boots) skipping them reopened see-through slots, so there they are lined with the vertices of inner-layer
faces moved only inner_offset (0.5 mm in linings.sh; back to back at 0 confused the arm and hand gate's inside test): at 3 mm their
twins poked through the outer layer of a fold as dark specks. Those twins keep the face's own UVs:
where a posed fold pokes the inner layer through the outer one, the twin shows cloth paint, not a dark blotch.
Every lining vertex is also kept behind any cloth its offset direction meets within 2 cm (at most 40 % of that distance). Band, lining and rim faces get the face attribute `lined` = 1; later runs leave them out (no doubled linings).
Geometry is added only: existing faces, UVs, weights and attributes are unchanged, so the paid paints stay valid.
Args (Blender): <in blend> <out blend> <report json> <region mask png> <body base colour png> <orm png>
                [key=value: bones Calf, band_bones Calf,Foot,Thigh, depth 0.07, offset 0.003, region B, dark_pct 25,
                 zmin -9, zmax 9, min_edges 3, mid_ok 0, band_regions (all), skip_inner 0, inner_offset = offset]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP, MASK, BODYPNG, ORMPNG = argv[:6]
opt = dict(x.split('=', 1) for x in argv[6:])
BONES = opt.get('bones', 'Calf').split(',')
BAND_BONES = opt.get('band_bones', 'Calf,Foot,Thigh').split(',')
DEPTH = float(opt.get('depth', 0.07))
OFFSET = float(opt.get('offset', 0.003))
REGION = opt.get('region', 'B')
DARK_PCT = float(opt.get('dark_pct', 25))
ZMIN, ZMAX = float(opt.get('zmin', -9)), float(opt.get('zmax', 9))
MIN_EDGES = int(opt.get('min_edges', 3))
BAND_REGIONS = opt.get('band_regions', '')   # e.g. BG: band faces must carry one of these region labels (or none)
MID_OK = opt.get('mid_ok', '0') == '1'
SKIP_INNER = opt.get('skip_inner', '0') == '1'
INNER_OFFSET = float(opt.get('inner_offset', OFFSET))   # offset of vertices on inner-layer faces (folds)   # leave Meshy's inner-layer faces unlined (see below)      # a sided band may take midline-weighted faces (a sleeve reaching the torso)     # smaller loops are left open (a belt knot's own opening)

bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
M, Mi = body.matrix_world, body.matrix_world.inverted()
names = [g.name for g in body.vertex_groups]


def pixels(path):
    img = bpy.data.images.load(path, check_existing=True)
    px = np.empty(img.size[0] * img.size[1] * 4, np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(img.size[1], img.size[0], 4)


MK, BODY_PX, ORM_PX = pixels(MASK), pixels(BODYPNG)[..., :3], pixels(ORMPNG)[..., :3]
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
dl = bm.verts.layers.deform.active
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
uvb = bm.loops.layers.uv['UVMap']
uvh = bm.loops.layers.uv.get('HeadUV')
# faces an earlier run already lined (and the lining faces themselves) are left out, so bands never double up
ll = bm.faces.layers.int.get('lined') or bm.faces.layers.int.new('lined')


def dominant(v):
    w = v[dl]
    return names[max(w.items(), key=lambda kv: kv[1])[0]] if len(w) else ''


def centre_uv(f):
    return sum((Vector(tuple(l[uvb].uv)) for l in f.loops), Vector((0, 0))) / len(f.loops)


def texel(px, uv):
    H, W = px.shape[:2]
    return px[min(H - 1, max(0, int(uv.y * H))), min(W - 1, max(0, int(uv.x * W)))]


def label(f):
    m = texel(MK, centre_uv(f))
    return 'RGBA'[int(np.argmax(m))] if m.max() > 0.3 else 'none'


def is_body(f):
    return not f[lh] and not f[lk] and not f[ll]


# boundary loops of body faces
seen, loops = set(), []
for e in bm.edges:
    if not e.is_boundary or e in seen or not is_body(e.link_faces[0]):
        continue
    lp, st = [], [e]; seen.add(e)
    while st:
        x = st.pop(); lp.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y.is_boundary and y not in seen and is_body(y.link_faces[0]):
                    seen.add(y); st.append(y)
    loops.append(lp)

report = {'loops': [], 'sides': {}}
groups = {}                  # side -> (selected loops, band faces): one lining per side, every selected rim joined to it
for lp in loops:
    vs = list({v for x in lp for v in x.verts})
    doms = [dominant(v) for v in vs]
    hits = [d for d in doms if any(k in d for k in BONES)]
    c = sum((M @ v.co for v in vs), Vector()) / len(vs)
    if len(hits) < 0.6 * len(vs) or not (ZMIN <= c.z <= ZMAX) or len(lp) < MIN_EDGES:
        continue
    nl, nr = sum(' L ' in d for d in hits), sum(' R ' in d for d in hits)
    side = ' L ' if nl > len(hits) / 2 else ' R ' if nr > len(hits) / 2 else ''     # '' : a midline rim (belt, collar)
    kd = KDTree(len(vs))
    for i, v in enumerate(vs):
        kd.insert(M @ v.co, i)
    kd.balance()

    def side_ok(d):
        return side in d or (MID_OK and ' L ' not in d and ' R ' not in d)

    def ok(f):
        if BAND_REGIONS and label(f) not in BAND_REGIONS + 'none':
            return False
        return is_body(f) and all(kd.find(M @ v.co)[2] < DEPTH and side_ok(dominant(v))
                                  and any(k in dominant(v) for k in BAND_BONES) for v in f.verts)
    band, st = set(), [x.link_faces[0] for x in lp]
    while st:
        f = st.pop()
        if f in band or not ok(f):
            continue
        band.add(f)
        for e in f.edges:
            st += [g for g in e.link_faces if g not in band]
    g = groups.setdefault(side, ([], set()))
    g[0].append(lp); g[1].update(band)
    report['loops'].append({'edges': len(lp), 'centre': [round(x, 3) for x in c], 'side': side.strip(),
                            'band_faces': len(band)})
# faces of Meshy's own inner layer (facing the limb or body axis: the inside of a turned cuff, a fold) are not lined: their
# twin would sit outside the cloth, facing out (dark patches on the outer surface)
segs = {b.name: (rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local) for b in rig.data.bones}


def faces_axis(f):
    cnt = {}
    for v in f.verts:
        d = dominant(v)
        cnt[d] = cnt.get(d, 0) + 1
    b = max(cnt, key=cnt.get)
    if b not in segs:
        return False
    a0, a1 = segs[b]
    c = M @ f.calc_center_median()
    d = a1 - a0
    t = max(0.0, min(1.0, (c - a0).dot(d) / max(d.dot(d), 1e-12)))
    out = c - (a0 + d * t)
    return (M.to_3x3() @ f.normal).normalized().dot(out.normalized()) < -0.2


for side, (lps, band) in groups.items():
    inner = [f for f in band if SKIP_INNER and faces_axis(f)]
    band = [f for f in band if not (SKIP_INNER and faces_axis(f))]
    report.setdefault('inner_faces_skipped', {})[side.strip() or 'mid'] = len(inner)
    cand = [f for f in band if label(f) == REGION] or band
    lum = np.array([texel(BODY_PX, centre_uv(f)) @ np.array([0.299, 0.587, 0.114]) for f in cand])
    order = np.argsort(lum)[:max(1, int(len(lum) * DARK_PCT / 100))]
    dark = cand[int(max(order, key=lambda i: texel(ORM_PX, centre_uv(cand[i]))[1]))]
    dark_uv = tuple(centre_uv(dark))
    normal = {}
    for f in band:
        for v in f.verts:
            normal[v] = normal.get(v, Vector()) + f.normal * f.calc_area()
    bset = set(band)
    near_inner = {v for f in band if faces_axis(f) for v in f.verts}
    # collision-aware: a vertex whose offset direction meets other cloth within reach (the outer layer of a fold, 0.3-2 mm
    # away) moves at most 40 % of that distance, so its twin stays behind that layer (rest pose, before the twins exist)
    bvh = BVHTree.FromBMesh(bm)
    capped, target = 0, {}
    for v, n in normal.items():
        dirw = -(M.to_3x3() @ n).normalized()
        want = INNER_OFFSET if v in near_inner else OFFSET
        pw = M @ v.co
        hit = bvh.ray_cast(Mi @ (pw + dirw * 1e-4), (Mi.to_3x3() @ dirw).normalized(), 0.02)
        if hit[0] is not None:
            dist = ((M @ hit[0]) - pw).length
            if 0.4 * dist < want:
                want = 0.4 * dist; capped += 1
        target[v] = Mi @ (pw + dirw * want)
    out = bmesh.ops.duplicate(bm, geom=band)
    vmap = out['vert_map']
    for v, co in target.items():
        vmap[v].co = co
    report.setdefault('offset_capped_vertices', {})[side.strip() or 'mid'] = capped
    lining = [x for x in out['geom'] if isinstance(x, bmesh.types.BMFace)]
    bmesh.ops.reverse_faces(bm, faces=lining)
    for f in band + lining:
        f[ll] = 1
    fmap = out['face_map']
    own = {fmap[f] for f in band if f in fmap and faces_axis(f)}
    for f in lining:
        if f in own:          # back to back with an inner-layer face: keeps that face's own paint (seen only where the
            continue          # fold pokes through its outer layer in a pose, where a dark texel showed as a blotch)
        for l in f.loops:
            l[uvb].uv = dark_uv
            if uvh:
                l[uvh].uv = dark_uv
    report.setdefault('own_paint_twins', {})[side.strip() or 'mid'] = len(own)
    rim = []
    for lp in lps:
        for e in lp:
            f0 = e.link_faces[0]
            if f0 not in bset:
                continue
            a, b = e.verts
            a2, b2 = vmap[a], vmap[b]
            for tri in ((a, b, b2), (a, b2, a2)):
                f = bm.faces.new(tri)
                f[lh] = 0; f[lk] = 0; f[ll] = 1; f.material_index = f0.material_index; f.smooth = f0.smooth
                f.normal_update()
                if f.normal.dot(f.calc_center_median() - f0.calc_center_median()) < 0:
                    f.normal_flip()
                for l in f.loops:
                    l[uvb].uv = dark_uv
                    if uvh:
                        l[uvh].uv = dark_uv
                rim.append(f)
    report['sides'][side.strip() or 'mid'] = {'loops': len(lps), 'band_faces': len(band), 'lining_faces': len(lining),
                                     'rim_faces': len(rim),
                                     'band_regions': {k: sum(label(f) == k for f in band) for k in 'RGBA'},
                                     'dark_rgb': [round(float(x), 3) for x in texel(BODY_PX, Vector(dark_uv))]}
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('RIM_LINING', json.dumps(report))
json.dump(report, open(REP, 'w'), indent=1)
