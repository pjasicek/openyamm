"""After the Meshy job: the lower belt buckle (three tiny pieces, crumpled by the reduction and painted leather-dark by
Meshy) is replaced by a clean rectangular frame with a prong, fitted to the pieces (principal axes, extents), rigid with
their mean weights, on a fifth flat colour square (gold), chest_part 5. Every other face and UV is untouched, so the
returned texture still fits. Reads the layout Meshy painted (work/ladder_body_meshy.blend, work/body_uv_meshy.npz) and
writes work/ladder_body.blend and work/body_uv.npz. Usage: blender -b -P buckle_uv.py"""
import json, os, bmesh, bpy
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 2080, 1024; SQ = (.18, .004, .022); TRI = [(.25, .25), (.75, .25), (.5, .75)]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_body_meshy.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
cand = bpy.data.objects['Cand_62']; me = cand.data; mw = cand.matrix_world; inv = mw.inverted()
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
part_layer = bm.faces.layers.int['chest_part']; uvl = bm.loops.layers.uv[me.uv_layers[0].name]
deform = bm.verts.layers.deform.verify()

# the old buckle pieces
seen, old_v = set(), set()
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); stack.append(y)
    cc = sum((mw @ x.co for x in comp), Vector()) / len(comp)
    if len(comp) <= 20 and .95 < cc.z < 1.01 and cc.y < -.165:
        old_v |= set(comp)
old_faces = {f.index for v in old_v for f in v.link_faces}
pts = np.array([(mw @ v.co)[:] for v in old_v]); c = pts.mean(0)
wsum = {}
for v in old_v:
    for gi, wt in v[deform].items():
        wsum[gi] = wsum.get(gi, 0) + wt / len(old_v)
top = sorted(wsum.items(), key=lambda x: -x[1])[:4]; tot = sum(w for _, w in top); wts = [(g, w / tot) for g, w in top]
_, _, vt = np.linalg.svd(pts - c); ax_long, ax_n = vt[0], vt[2]
if ax_n[1] > 0:
    ax_n = -ax_n                                                     # frame faces the front (-Y)
ax_short = np.cross(ax_n, ax_long)
ext = np.abs((pts - c) @ np.stack([ax_long, ax_short]).T).max(0)
hw, hh = float(np.clip(ext[0], .018, .028)), float(np.clip(ext[1], .014, .02))
BAR, DEP = .0042, .003
print('BUCKLE old verts', len(old_v), 'faces', len(old_faces), 'centre', c.round(3).tolist(), 'half size', round(hw, 4), round(hh, 4))

# body_uv bookkeeping: triangle order of body faces before the change
uv0 = me.uv_layers[0].data
body_before = [p.index for p in me.polygons if np.mean([uv0[li].uv[0] for li in p.loop_indices]) < .5]
me.calc_loop_triangles()
order = [t.polygon_index for t in me.loop_triangles if t.polygon_index in set(body_before)]
d = dict(np.load(os.path.join(HERE, 'work', 'body_uv_meshy.npz')))
keep = np.array([pi not in old_faces for pi in order])
for k in ('uv', 'pos', 'detail', 'cls', 'part'):
    d[k] = d[k][keep]

bmesh.ops.delete(bm, geom=list(old_v), context='VERTS')
new_tris = []


def box(center, half):
    vs = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                p = center + ax_long * sx * half[0] + ax_short * sy * half[1] + ax_n * sz * half[2]
                v = bm.verts.new(inv @ Vector(p))
                for gi, wt in wts:
                    v[deform][gi] = wt
                vs[(sx, sy, sz)] = v
    quads = [[(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)],
             [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)], [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)],
             [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], [(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)]]
    for q in quads:
        for t in ([q[0], q[1], q[2]], [q[0], q[2], q[3]]):
            tv = [vs[k] for k in t]
            # outward winding in world space (frame basis is right-handed or not depending on the SVD signs)
            a, b, cc = [mw @ x.co for x in tv]; n = (b - a).cross(cc - a); mid = (a + b + cc) / 3
            if n.dot(mid - Vector(center)) < 0:
                tv = tv[::-1]
            f = bm.faces.new(tv); f.material_index = 0; f.smooth = False; f[part_layer] = 5
            for k, loop in enumerate(f.loops):
                u, v = TRI[k]; loop[uvl].uv = ((SQ[0] + u * SQ[2]) * H / W, SQ[1] + v * SQ[2])
            new_tris.append([(mw @ x.co)[:] for x in tv])


for sx in (-1, 1):
    box(c + ax_long * sx * (hw - BAR), (BAR, hh, DEP))
for sy in (-1, 1):
    box(c + ax_short * sy * (hh - BAR), (hw - 2 * BAR, BAR, DEP))
box(c + ax_long * hw * .1, (hw * .8, BAR * .5, DEP * .7))
bm.to_mesh(me); bm.free(); me.update()
n = len(new_tris)
d['uv'] = np.concatenate([d['uv'], np.tile(np.array([[(SQ[0] + u * SQ[2], SQ[1] + v * SQ[2]) for u, v in TRI]]), (n, 1, 1))])
d['pos'] = np.concatenate([d['pos'], np.array(new_tris)]); d['detail'] = np.concatenate([d['detail'], np.zeros(n, bool)])
d['cls'] = np.concatenate([d['cls'], np.zeros(n, d['cls'].dtype)]); d['part'] = np.concatenate([d['part'], np.full(n, 5, d['part'].dtype)])
np.savez(os.path.join(HERE, 'work', 'body_uv.npz'), **d)
sq = json.load(open(os.path.join(HERE, 'work', 'flat_squares.json'))); sq['5'] = list(SQ)
json.dump(sq, open(os.path.join(HERE, 'work', 'flat_squares.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder_body.blend'))
print('BUCKLE new tris', n, 'total', sum(len(p.vertices) - 2 for p in me.polygons))
