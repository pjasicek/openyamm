"""Inner lining of the sleeves (see-through gate r2: in bent elbows (AttackMelee, Fidget, Running) the view into the
elbow-length sleeve met the sleeve wall's culled back faces and showed the background; the sleeve has no open rim loop
for rim_lining.py: Meshy joined its turned-in edge to the forearm). Body faces (no head/hand/lined attribute) whose
vertices are mostly weighted to the BONES keywords and lie beyond |x| > XMIN (Blender rest) are duplicated, flipped, and moved OFFSET
along the inward vertex normal, with the twins' weights (each vertex keeps its own), so the inside follows the outside
in any pose. Every twin loop takes (UVMap and HeadUV) the centre UV of one dark hair face: the face at the DARK_PCT
luminance percentile of the parts' own head-set paint. Face attributes copied (head = 1) and `lined` = 1.
Geometry is added only (existing faces, UVs, weights unchanged).
Args (Blender): <in blend> <out blend> <body base colour png> <bones kw,...> <xmin> [offset 0.0015] [dark_pct 15]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, PNG, BONES, XMIN = a[0], a[1], a[2], a[3].split(','), float(a[4])
OFFSET = float(a[5]) if len(a) > 5 else 0.0015
DARK = float(a[6]) if len(a) > 6 else 15
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; me = ob.data
img = bpy.data.images.load(PNG)
W, H = img.size
pix = np.array(img.pixels[:], np.float32).reshape(H, W, 4)
bm = bmesh.new(); bm.from_mesh(me)
lined = bm.faces.layers.int.get('lined') or bm.faces.layers.int.new('lined')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int64); cid = 0
for v in bm.verts:                                   # numbered by lowest vertex index, as head_split.py
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
hl = bm.faces.layers.int['head']; hn = bm.faces.layers.int['hand']
dl0 = bm.verts.layers.deform.active
gidx = {i for i, g in enumerate(ob.vertex_groups) if any(k in g.name for k in BONES)}
def armv(v):
    d = v[dl0]; tot = sum(d.values()) or 1
    return sum(w for gi, w in d.items() if gi in gidx) / tot > 0.5
faces = [f for f in bm.faces if not f[hl] and not f[hn] and not f[lined] and all(abs(v.co.x) > XMIN for v in f.verts)
         and sum(armv(v) for v in f.verts) >= 2]
PARTS = BONES
uvm = bm.loops.layers.uv['UVMap']; huv = bm.loops.layers.uv['UVMap']
lums = []
for f in faces:
    c = sum((l[huv].uv for l in f.loops), Vector((0, 0))) / len(f.loops)
    x, y = int(np.clip(c.x * W, 0, W - 1)), int(np.clip(c.y * H, 0, H - 1))
    p = pix[y, x]
    lums.append((0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2], f))
lv = np.array([l for l, _ in lums])
pick = lums[int(np.argmin(np.abs(lv - np.percentile(lv, DARK))))][1]
uv_h = sum((l[huv].uv for l in pick.loops), Vector((0, 0))) / len(pick.loops)
uv_m = sum((l[uvm].uv for l in pick.loops), Vector((0, 0))) / len(pick.loops)
dl = bm.verts.layers.deform.active
ilayers = [bm.faces.layers.int[k] for k in bm.faces.layers.int.keys()]
vmap = {}
vs = {v for f in faces for v in f.verts}
for v in vs:
    n = v.normal
    nv = bm.verts.new(v.co - n * OFFSET)
    for gi, gw in v[dl].items():
        nv[dl][gi] = gw
    vmap[v] = nv
new = 0
for f in faces:
    try:
        nf = bm.faces.new([vmap[v] for v in reversed(f.verts)])
    except ValueError:
        continue
    for L in ilayers:
        nf[L] = f[L]
    nf[lined] = 1
    nf.material_index = f.material_index
    nf.smooth = f.smooth
    for l in nf.loops:
        l[huv].uv = uv_h; l[uvm].uv = uv_m
    new += 1
f_l = None
bm.to_mesh(me); bm.free(); me.update()
print('SLEEVE_LINING', {'parts': PARTS, 'faces': len(faces), 'twins': new, 'dark_lum': round(float(np.percentile(lv, DARK)), 3)})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
