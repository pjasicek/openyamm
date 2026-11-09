"""Close the mouth (review 4: dark shards at the mouth corners and between the lips). Meshy modelled the lips slightly
parted with a mouth bag behind them; through the slit the bag's back faces show and are culled by the viewer/engine.
1. Mouth-bag faces: skin (piece 0) faces in the mouth box whose normal points backward (+Y) or that lie behind the
   lip surface, grown through connected faces behind the lips; deleted with their loose vertices.
2. The opening left at the lips is filled (one polygon per boundary loop, BEAUTY triangulation): no new vertices, the
   lip rim's weights carry it. Faces: head = 1, smooth.
3. Their HeadUV: a planar front projection packed into a free square of the head atlas (from the HeadUV raster);
   face_nearest.py then colours them from the head model's lip line.
4. The folded philtrum triangles under the nose (two back-facing faces) are relaxed (Laplacian, 5 mm).
In place on <blend>. Args: -- <blend>"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOX = (-0.034, 0.020, 1.510, 1.535)          # x0, x1, z0, z1 (seeds)
GROW = (-0.048, 0.034, 1.495, 1.548)         # the bag reaches past the lips inside the head
LIP_Y = -0.1235                              # the lip surface's front at the slit; faces behind it are the bag
PHILTRUM = Vector((-0.010, -0.123, 1.5327))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
body = bpy.data.objects['Body']; me = body.data
if me.get('mouth_closed'):
    print('MOUTH already closed'); sys.exit(0)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.normal_update()
pl = bm.verts.layers.int['piece']; hl = bm.faces.layers.int['head']; huv = bm.loops.layers.uv['HeadUV']


def in_box(c):
    return BOX[0] < c.x < BOX[1] and BOX[2] < c.z < BOX[3]


from mathutils.bvhtree import BVHTree
bm.faces.ensure_lookup_table()
skin_faces = [f for f in bm.faces if f.verts[0][pl] == 0]
tree = BVHTree.FromBMesh(bm)


def hidden(f):
    """inside the mouth: a ray from the face toward the front (-Y) meets another face within 6 cm"""
    c = f.calc_center_median()
    loc, n, i, d = tree.ray_cast(c + Vector((0, -1e-4, 0)), Vector((0, -1, 0)), 0.06)
    return loc is not None and i != f.index


seed = [f for f in skin_faces if in_box(f.calc_center_median()) and hidden(f)]
bag = set(seed); st = list(seed)
while st:
    f = st.pop()
    for e in f.edges:
        for g in e.link_faces:
            if g in bag or g.verts[0][pl] != 0:
                continue
            c = g.calc_center_median()
            if GROW[0] < c.x < GROW[1] and GROW[2] < c.z < GROW[3] and hidden(g):
                bag.add(g); st.append(g)
verts = {v for f in bag for v in f.verts}
bmesh.ops.delete(bm, geom=list(bag), context='FACES_ONLY')
lone = [v for v in verts if v.is_valid and not v.link_faces]
bmesh.ops.delete(bm, geom=lone, context='VERTS')
edges = [e for e in bm.edges if e.is_boundary and all(v[pl] == 0 for v in e.verts)
         and all(GROW[0] < v.co.x < GROW[1] and GROW[2] < v.co.z < GROW[3] for v in e.verts)]
_bv = [v.co for e in edges for v in e.verts]
print('MOUTH rim edges', len(edges), 'y range', round(min(p.y for p in _bv), 4) if _bv else None, round(max(p.y for p in _bv), 4) if _bv else None)
res = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
tri = bmesh.ops.triangulate(bm, faces=res['faces'], quad_method='BEAUTY', ngon_method='BEAUTY')['faces']
# dangling leftovers: faces whose edges are all open, and wire edges (no faces) in the mouth region
dang = [f for f in bm.faces if f.verts[0][pl] == 0 and all(e.is_boundary for e in f.edges)
        and all(GROW[0] < v.co.x < GROW[1] and GROW[2] < v.co.z < GROW[3] for v in f.verts)]
bmesh.ops.delete(bm, geom=dang, context='FACES')
wire = [e for e in bm.edges if not e.link_faces and all(GROW[0] < v.co.x < GROW[1] and GROW[2] < v.co.z < GROW[3] for v in e.verts)]
bmesh.ops.delete(bm, geom=wire, context='EDGES')
tri = [f for f in tri if f.is_valid]
print('MOUTH dangling faces', len(dang), 'wire edges', len(wire))
# leftover small loops (a 3-edge hole at the lip centre stayed open): one face each
left = [e for e in bm.edges if e.is_boundary and all(v[pl] == 0 for v in e.verts)
        and all(GROW[0] < v.co.x < GROW[1] and GROW[2] < v.co.z < GROW[3] for v in e.verts)]
for e in left:
    if not e.is_boundary:
        continue
    loop = [e.verts[0], e.verts[1]]
    while len(loop) < 12:
        nxt = [x.other_vert(loop[-1]) for x in loop[-1].link_edges if x.is_boundary and x.other_vert(loop[-1]) not in loop[-2:]]
        if not nxt:
            break
        if nxt[0] is loop[0]:
            try:
                tri.append(bm.faces.new(loop))
            except ValueError:
                pass
            break
        loop.append(nxt[0])
for f in tri:
    f[hl] = 1; f.smooth = True; f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
print('MOUTH bag faces removed', len(bag), 'loose vertices', len(lone), 'cap faces', len(tri))
# free square in the head atlas (no scipy in Blender: box test on an integral image of the covered raster)
R = np.load(os.path.join(HERE, 'work', 'uvraster_HeadUV.npz')); cov = (R['piece'] >= 0).astype(np.int32)
N = cov.shape[0]; S, PAD = 36, 3
I = np.pad(cov, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
B = S + 2 * PAD
box = I[B:, B:] - I[:-B, B:] - I[B:, :-B] + I[:-B, :-B]
ys, xs = np.nonzero(box == 0)
if len(ys) == 0:
    raise RuntimeError('no free square for the mouth cap')
y0, x0 = int(ys[0]) + PAD, int(xs[0]) + PAD
if tri:
    P = [l.vert.co for f in tri for l in f.loops]
    xa, xb = min(p.x for p in P), max(p.x for p in P); za, zb = min(p.z for p in P), max(p.z for p in P)
    sc = S / max(xb - xa, zb - za, 1e-6)
    for f in tri:
        for l in f.loops:
            px = x0 + (l.vert.co.x - xa) * sc; py = y0 + (zb - l.vert.co.z) * sc
            l[huv].uv = (px / N, 1 - py / N)
# philtrum fold
sel = [v for v in bm.verts if v[pl] == 0 and (v.co - PHILTRUM).length < 0.005 and not any(e.is_boundary for e in v.link_edges)]
for _ in range(8):
    new = {v: v.co.lerp(sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges),
                        0.6 * (1 - (v.co - PHILTRUM).length / 0.005)) for v in sel}
    for v, p in new.items():
        v.co = p
bm.to_mesh(me); bm.free(); me['mouth_closed'] = 1; me.update()
bpy.ops.wm.save_mainfile()
print('MOUTH cap UV square', x0, y0, S, 'philtrum vertices relaxed', len(sel))
