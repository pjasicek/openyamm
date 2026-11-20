"""Line the inside of the linen undersleeve cuffs (see-through gate r2: crescents of background inside the cuff opening in
every clip, review/holes/sheet1.png). DM1's Meshy undersleeve is a flared cuff folded back into the forearm, so there is no
open rim for rim_lining.py: through the cuff opening the view meets the cuff wall's back faces, culled in the game.
Body faces mostly weighted to a Forearm (or Hand) bone whose normal points away from the forearm axis (cos > 0.3) and that lie
farther than R_MIN from that axis (the cuff wall, not the forearm skin) are duplicated OFFSET behind themselves (toward the
axis), flipped, with their weights, on one dark texel of their own paint (the 10th percentile luminance of those faces);
face attribute `lined` = 1. Positions/faces only (paints and UVs stay valid).
Args (Blender): <in blend> <out blend> [R_MIN 0.040] [OFFSET 0.003] [body base colour png] [force] [COS 0.3]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
R_MIN = float(a[2]) if len(a) > 2 else 0.040
OFFSET = float(a[3]) if len(a) > 3 else 0.003
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; M = body.matrix_world; Mi = M.inverted()
names = [g.name for g in body.vertex_groups]
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.active
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
ll = bm.faces.layers.int.get('lined') or bm.faces.layers.int.new('lined')
uvb = bm.loops.layers.uv['UVMap']
BASE = bpy.data.images.load(a[4]) if len(a) > 4 else None
FORCE = len(a) > 5 and a[5] == 'force'
COS = float(a[6]) if len(a) > 6 else 0.3      # also faces rim_lining.py's band flagged (its vertex-normal twin can land outside at the fold)
rep = {}
for side in ('L', 'R'):
    fa = rig.data.bones[f'Bip01 {side} Forearm']; ha = rig.data.bones[f'Bip01 {side} Hand']
    p0 = rig.matrix_world @ fa.head_local; p1 = rig.matrix_world @ ha.head_local
    ax = (p1 - p0); L = ax.length; ax.normalize()
    sel = []
    for f in bm.faces:
        if f[lh] or f[lk] or (f[ll] and not FORCE):
            continue
        doms = []
        for v in f.verts:
            w = v[dl]
            doms.append(names[max(w.items(), key=lambda kv: kv[1])[0]] if len(w) else '')
        if sum((f'{side} Forearm' in d) or (f'{side} Hand' in d) for d in doms) < len(doms) * 0.67:
            continue
        c = M @ f.calc_center_median()
        t = (c - p0).dot(ax)
        if t < -0.05 or t > L + 0.04:
            continue
        rad = (c - p0) - ax * t
        if rad.length < R_MIN:
            continue
        n = (M.to_3x3() @ f.normal).normalized()
        if n.dot(rad.normalized()) < COS:
            continue
        sel.append(f)
    # dark texel: 10th percentile luminance of the selected faces' centre texels
    if BASE is not None and sel:
        W, H = BASE.size; px = np.array(BASE.pixels[:]).reshape(H, W, 4)
        def lum(f):
            uv = sum((Vector(tuple(l[uvb].uv)) for l in f.loops), Vector((0, 0))) / len(f.loops)
            c = px[min(H - 1, int(uv.y * H)), min(W - 1, int(uv.x * W))]
            return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2], tuple(uv)
        ls = sorted(lum(f) for f in sel)
        dark_uv = ls[int(len(ls) * 0.1)][1]
    else:
        dark_uv = None
    vmap = {}
    normal = {}
    for f in sel:
        for v in f.verts:
            normal[v] = normal.get(v, Vector()) + f.normal * f.calc_area()
    for v, n in normal.items():
        nv = bm.verts.new(v.co - n.normalized() * OFFSET * (Mi.to_3x3() @ Vector((1, 0, 0))).length)
        for g, w in v[dl].items():
            nv[dl][g] = w
        vmap[v] = nv
    nf = 0
    for f in sel:
        g = bm.faces.new([vmap[v] for v in reversed(f.verts)])
        g.material_index = f.material_index; g[lh] = 0; g[lk] = 0; g[ll] = 1; f[ll] = 1
        for l in g.loops:
            l[uvb].uv = dark_uv if dark_uv else (0, 0)
        for name in [u.name for u in me.uv_layers if u.name != 'UVMap']:
            lay = bm.loops.layers.uv[name]
            for l in g.loops: l[lay].uv = (0.0, 0.0)
        nf += 1
    rep[side] = {'faces': nf, 'dark_uv': dark_uv}
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CUFF_LINING', json.dumps(rep))
