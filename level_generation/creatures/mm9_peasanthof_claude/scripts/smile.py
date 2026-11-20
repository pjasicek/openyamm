"""A gentle closed smile and rounder cheeks on the shared head (coordinator review r4, 2026-11-02: the faces read stern;
MM9's dwarf women smile warmly with round cheeks). Positions only (UVs, paint, weights unchanged): the painted lips move
with the mesh, so the paint follows the new shape.
- Lips: head-shell faces in front of the face (Blender y < -0.06, z 0.36..0.40, |x| < 0.032) whose HeadUV centroid texel in the design-1
  head paint is lip red (r > 1.45 g, saturation > 0.33); corners = the lip vertices at the extreme x within 8 mm of the mouth height.
- Corner lift: shell vertices within R_CORNER of a corner rise LIFT (smoothstep falloff) and sink BACK into the face.
- Cheeks: shell vertices within R_CHEEK of a point above and outside each corner (the apple of the cheek) come forward
  CHEEK and up CHEEK / 2.
Args (Blender): <in blend> <out blend> <head basecolor png> [lift 0.0025] [cheek 0.0016]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, PNG = a[:3]
LIFT = float(a[3]) if len(a) > 3 else 0.0025
CHEEK = float(a[4]) if len(a) > 4 else 0.0016
BACK = 0.0008; R_CORNER = 0.014; R_CHEEK = 0.022
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; M = body.matrix_world; Mi = M.inverted()
img = bpy.data.images.load(PNG); W_, H_ = img.size
px = np.empty(W_ * H_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H_, W_, 4)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
lk = bm.faces.layers.int['head']; lh = bm.faces.layers.int['hand']; lt = bm.faces.layers.int.get('twin')
uvh = bm.loops.layers.uv['HeadUV']
lipv = set()
for f in bm.faces:
    if not f[lk] or f[lh] or (lt and f[lt]): continue
    c = M @ f.calc_center_median()
    if not (c.y < -0.06 and 0.36 < c.z < 0.40 and abs(c.x) < 0.032): continue
    u = sum((l[uvh].uv for l in f.loops), Vector((0, 0))) / len(f.loops)
    r, g, b = px[min(H_ - 1, int(u.y * H_)), min(W_ - 1, int(u.x * W_)), :3]
    mx, mn = max(r, g, b), min(r, g, b)
    if r > 1.45 * g and (mx - mn) / max(mx, 1e-6) > 0.33:
        lipv.update(f.verts)
P = {v: M @ v.co for v in lipv}
xs = np.array([p.x for p in P.values()])
mouthz = float(np.median([p.z for p in P.values()]))
band = [p for p in P.values() if abs(p.z - mouthz) < 0.008]
ymin = min(p.y for p in band); band = [p for p in band if p.y < ymin + 0.018]   # the outer lips, not the inner slit
cx = float(np.median([p.x for p in band])); hw = min(float(np.percentile([abs(p.x - cx) for p in band], 85)), 0.025)
cl = min(band, key=lambda p: abs(p.x - (cx - hw))); cr = min(band, key=lambda p: abs(p.x - (cx + hw)))   # red cheeks widen the raw extremes
shell = {v for f in bm.faces if f[lk] and not f[lh] and not (lt and f[lt]) for v in f.verts}


def ss(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


moved = 0
for v in shell:
    p = M @ v.co
    d = Vector()
    for c in (cl, cr):
        r = (p - c).length
        if r < R_CORNER:
            w = ss(1 - r / R_CORNER); d += Vector((0, BACK * w, LIFT * w))
        side = 1 if c.x > 0 else -1
        ch = c + Vector((0.012 * side, 0, 0.013))
        r2 = (p - ch).length
        if r2 < R_CHEEK and p.y < -0.04:
            w = ss(1 - r2 / R_CHEEK); d += Vector((0, -CHEEK * w, CHEEK * 0.5 * w))
    if d.length > 0:
        v.co = Mi @ (p + d); moved += 1
bm.to_mesh(me); me.update()
print('SMILE', json.dumps({'lip_verts': len(lipv), 'corners': [[round(x, 4) for x in cl], [round(x, 4) for x in cr]],
                           'mouth_z': round(mouthz, 4), 'moved': moved, 'lift': LIFT, 'cheek': CHEEK}))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
