"""Inner lining of the hair shells (see-through gate r1: under the page-boy bob, between the hair and the neck, the view
meets the hair shells' back faces, which the game culls, and shows the background at the neck sides).
The given loose parts (head_split.py numbering: by lowest vertex index) are duplicated whole, flipped, and moved OFFSET
along the inward vertex normal, with the twins' weights (each vertex keeps its own), so the inside follows the outside
in any pose. Every twin loop takes (UVMap and HeadUV) the centre UV of one dark hair face: the face at the DARK_PCT
luminance percentile of the parts' own head-set paint. Face attributes copied (head = 1) and `lined` = 1.
Geometry is added only (existing faces, UVs, weights unchanged).
Args (Blender): <in blend> <out blend> <head base colour png> <parts i,j,...> [offset 0.0015] [dark_pct 15]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, PNG, PARTS = a[0], a[1], a[2], [int(x) for x in a[3].split(',')]
OFFSET = float(a[4]) if len(a) > 4 else 0.0015
DARK = float(a[5]) if len(a) > 5 else 15
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
faces = [f for f in bm.faces if comp[f.verts[0].index] in PARTS]
uvm = bm.loops.layers.uv['UVMap']; huv = bm.loops.layers.uv['HeadUV']
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
print('HAIR_LINING', {'parts': PARTS, 'faces': len(faces), 'twins': new, 'dark_lum': round(float(np.percentile(lv, DARK)), 3)})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
