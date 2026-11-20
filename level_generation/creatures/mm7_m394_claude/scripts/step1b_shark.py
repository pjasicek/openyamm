"""Step 1b (shark), on work/step1.blend (Smart Topology, length 2 m, facing -Y):
- Straighten: the return swims with a lateral S-bend (the tail tip 18 cm to its right). Per vertex, x -= the smoothed
  centreline x at its y (trimmed slab centroids of the skin, piece 0); z is untouched (the tail's upper lobe rises).
- Holes: the four 4-6 vertex flakes (pieces 37-40) sat in a 9-vertex hole on the back; they are deleted and every
  skin boundary loop of <= 12 vertices is closed by a flat fan.
- Mouth: the slit's two boundary loops (lip edge and inner edge) are each closed by a fan to a centre pushed
  MOUTH_DEPTH into the head (+Y), so an opening jaw shows a throat, not a hole; the fan faces get face attribute
  'mouth' = 1 (class 7, painted dark in compose).
- Teeth (pieces 1-36) are kept; rig_shark.py binds each wholly to Head or Jaw.
Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
MOUTH_DEPTH = 0.07
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
ob = bpy.data.objects['Body']; me = ob.data
co = np.array([tuple(v.co) for v in me.vertices]); pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
skin = co[pv == 0]
ys = np.linspace(-1, 1, 41); xs = []
for y in ys:
    c = skin[np.abs(skin[:, 1] - y) < 0.04][:, [0, 2]]
    m = c.mean(0)
    for _ in range(4):
        d = np.linalg.norm(c - m, axis=1); m = c[d <= np.percentile(d, 60)].mean(0)
    xs.append(m[0])
xs = np.array(xs); k = np.exp(-0.5 * (np.arange(-3, 4) / 1.5) ** 2); k /= k.sum()
xs = np.convolve(np.pad(xs, 3, mode='edge'), k, 'valid')
xs -= xs[np.argmin(np.abs(ys - (-0.5)))]                                  # keep the head where it is
print('STRAIGHT centreline x (cm) snout..tail', np.round(100 * xs[::5], 1).tolist())
co[:, 0] -= np.interp(co[:, 1], ys, xs)
me.vertices.foreach_set('co', co.ravel()); me.update()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
pl = bm.verts.layers.int['piece']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[pl] >= 37], context='VERTS')
ml = bm.faces.layers.int.new('mouth')


def loops():
    edges = {e for e in bm.edges if e.is_boundary and e.verts[0][pl] == 0}
    adj = {}
    for e in edges:
        for v in e.verts:
            adj.setdefault(v, []).append(e)
    out = []
    while edges:
        e0 = edges.pop(); lp = [e0.verts[0], e0.verts[1]]; cur = e0.verts[1]
        while True:
            nx = next((e for e in adj[cur] if e in edges), None)
            if nx is None:
                break
            edges.discard(nx); cur = nx.other_vert(cur)
            if cur == lp[0]:
                break
            lp.append(cur)
        out.append(lp)
    return out


small = mouth = 0
for lp in loops():
    is_mouth = len(lp) > 12
    e = bm.edges.get((lp[0], lp[1])); f_adj = e.link_faces[0]; lv = [l.vert for l in f_adj.loops]; i = lv.index(lp[0])
    if lv[(i + 1) % len(lv)] == lp[1]:
        lp = lp[::-1]
    c = sum((v.co for v in lp), Vector()) / len(lp) + Vector((0, MOUTH_DEPTH if is_mouth else 0.0, 0))
    cv = bm.verts.new(c); cv[pl] = 0
    for k in range(len(lp)):
        try:
            f = bm.faces.new((lp[k], lp[(k + 1) % len(lp)], cv)); f[ml] = int(is_mouth)
        except ValueError:
            pass
    mouth += int(is_mouth); small += int(not is_mouth)
left = sum(1 for e in bm.edges if e.is_boundary and e.verts[0][pl] == 0)
bm.to_mesh(me); bm.free()
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes['orig_co'].data.foreach_set('vector', co.ravel())
print('HOLES small filled', small, 'mouth loops closed', mouth, 'skin boundary edges left', left, 'verts', len(co))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
