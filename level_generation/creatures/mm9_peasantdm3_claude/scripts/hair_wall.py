"""Close the see-through gap between the lengthened hair curtain and the jaw/neck (review/t4_magenta.png: background
between cheek and hair from the front). Per side and height, a forward-facing sheet BACK (1.2 cm) behind the curtain's
front-most vertex at that height (lat > 8.5 cm) from the head shell / body surface (ray from the head axis outward, minus 5 mm) to the
hair curtain's inner surface (+ 4 mm into the hair), for heights where the curtain exists. Faces carry head = 1, one
dark hair texel of the head set in HeadUV (PCT percentile luminance, default 3rd: reads as the shadow under the hair of the hair part's face-centre texels), weights
copied from the nearest hair vertex. Existing geometry, UVs and weights are unchanged.
Args: -- <in blend> <out blend> <head basecolor png> [BACK 0.012] [PCT 0.03] [swatch]"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, HEADPNG = argv[:3]
BACK = float(argv[3]) if len(argv) > 3 else 0.012
PCT = float(argv[4]) if len(argv) > 4 else 0.03
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
co = L.rest_coords(body); lab = L.loose_parts(me)
hair = lab[np.argmax(co[:, 2])]
cand = np.where((co[:, 2] > 0.40) & (co[:, 2] < 0.47))[0]
shell = lab[cand[np.argmin(co[cand, 1])]]
torso = int(np.bincount(lab).argmax())
S = np.where(lab == shell)[0]
xc = (co[S, 0].min() + co[S, 0].max()) / 2
vs = co.tolist()
def tree(parts):
    fs = [list(f.vertices) for f in me.polygons if lab[f.vertices[0]] in parts]
    return BVHTree.FromPolygons(vs, fs)
th, tb = tree({hair}), tree({shell, torso})
# dark hair texel
img = bpy.data.images.load(HEADPNG); W, H = img.size
px = np.array(img.pixels[:]).reshape(H, W, 4)[..., :3]
huv = me.uv_layers['HeadUV'].data
cands = []
for f in me.polygons:
    if lab[f.vertices[0]] != hair: continue
    uv = np.mean([tuple(huv[li].uv) for li in f.loop_indices], 0)
    x, y = int(uv[0] * W), int(uv[1] * H)          # Blender image pixels: row 0 = bottom = v 0
    if 0 <= x < W and 0 <= y < H:
        c = px[y, x]; cands.append((float(c @ [0.2126, 0.7152, 0.0722]), tuple(uv), tuple(c)))
cands.sort(); pick = cands[int(len(cands) * PCT)]
UVD = pick[1]
if len(argv) > 5 and argv[5] == 'swatch':
    UVD = (0.95, 0.05)          # swatch_paint.py's very dark brown block (free head-set UV)
kd = KDTree(int((lab == hair).sum()))
for i in np.where(lab == hair)[0]: kd.insert(Vector(co[i]), int(i))
kd.balance()
bm = bmesh.new(); bm.from_mesh(me)
deform = bm.verts.layers.deform.verify()
orig_verts = list(bm.verts)
head_l = bm.faces.layers.int.get('head'); hand_l = bm.faces.layers.int.get('hand')
uvl = {u.name: bm.loops.layers.uv[u.name] for u in me.uv_layers}
rep = {'texel_rgb': [round(x, 3) for x in pick[2]], 'rows': {}}
zs = np.arange(0.325, 0.485, 0.012)
nf = 0
HV = np.where(lab == hair)[0]
TS = (0, 0.25, 0.5, 0.75, 1)
for side in (-1, 1):
    rows = []
    for z in zs:
        # the curtain's front edge at this height: front-most hair vertex hanging beside the head (lat > 0.085)
        near = HV[(np.abs(co[HV, 2] - z) < 0.012) & (np.sign(co[HV, 0] - xc) == side) & (np.abs(co[HV, 0] - xc) > 0.085)]
        if len(near) < 2: rows.append(None); continue
        yw = co[near, 1].min() + BACK
        o = Vector((xc, yw, z)); d = Vector((side, 0, 0))
        hb, _, _, db = tb.ray_cast(o, d)
        lat_in = (db - 0.005) if hb is not None else 0.03
        hh, _, _, dh = th.ray_cast(o + d * max(lat_in - 0.01, 0), d)
        if hh is None: rows.append(None); continue
        lat_out = max(lat_in - 0.01, 0) + dh + 0.002
        if lat_out - lat_in < 0.004 or lat_out > 0.15: rows.append(None); continue
        rows.append((z, lat_in, lat_out, yw))
    rep['rows'][side] = [None if r is None else [round(x, 3) for x in r] for r in rows]
    prev = None
    for r in rows:
        if r is None: prev = None; continue
        z, li, lo, yw = r
        cur = []
        for t in TS:
            x = xc + side * (li + (lo - li) * t)
            # stay behind the hair wherever the hair covers this point seen from the front (ray from -y)
            # (the first FRONT-facing hair face: the curtain's inner layer faces away and is culled in the game)
            org = Vector((x, -0.5, z)); y = yw
            for _ in range(6):
                hit, nor, _, dist = th.ray_cast(org, Vector((0, 1, 0)))
                if hit is None: break
                if nor.y < 0:
                    y = max(yw, hit.y + 0.003); break
                org = hit + Vector((0, 1e-4, 0))
            cur.append(bm.verts.new((x, y, z)))
        for v in cur:
            idx = kd.find(v.co)[1]
            src = orig_verts[idx][deform]
            for g, w in src.items(): v[deform][g] = w
        if prev is not None:
            for k in range(len(TS) - 1):
                quad = [prev[k], prev[k + 1], cur[k + 1], cur[k]]
                f = bm.faces.new(quad)
                f.normal_update()
                if f.normal.y > 0: f.normal_flip()          # face the front (-y)
                if head_l: f[head_l] = 1
                if hand_l: f[hand_l] = 0
                f.material_index = 0
                for l in f.loops:
                    for name, lay in uvl.items(): l[lay].uv = UVD
                nf += 1
        prev = cur
bm.to_mesh(me); bm.free(); me.update()
rep['faces'] = nf
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HAIRWALL', json.dumps(rep))
