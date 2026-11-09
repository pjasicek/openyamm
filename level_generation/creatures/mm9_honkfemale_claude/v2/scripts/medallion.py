"""Clean medallion, buckle shards off, neck skirt (Honk bodies, 2026-10-30 night pass). Run after robe_lining.py.

Args (Blender): <in blend> <out blend> <report json> centre=x,y,z radius=m atlas=u,v,r_uv [buckle=x,y,z] [skirt=0.05]
- Meshy's medallion is a heap of small plates that fly apart at close range (Hit) under blotchy paint. Every loose body part inside
  1.6 x radius of `centre` goes; a shallow dome in its place carries a planar map on a free circle of the body atlas
  (`atlas`; medallion_paint.py paints it from the HD head master). Rigid, on the old part's weights without the braid bones (the
  female's medallion moved with her hair).
- `buckle`: small loose shards (under 12 faces) lying on the buckle are deleted.
- Neck skirt: the head shell's lower ring and the robe's neck ring were separate edges with a gap, and the background showed at the
  throat (female, at Standing). The ring is extruded `skirt` metres down and 8 % towards the neck axis, hidden under the robe,
  on the ring's own skin texels and weights."""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
opt = dict(a.split('=', 1) for a in argv[3:])
C = Vector([float(x) for x in opt['centre'].split(',')])
R = float(opt['radius'])
UC, VC, RUV = [float(x) for x in opt['atlas'].split(',')]
SKIRT = float(opt.get('skirt', 0.05))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
M, Mi = body.matrix_world, body.matrix_world.inverted()
names = [g.name for g in body.vertex_groups]
floor = min((M @ v.co).z for v in me.vertices)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
dl = bm.verts.layers.deform.active
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
uvb, uvh = bm.loops.layers.uv['UVMap'], bm.loops.layers.uv['HeadUV']


def parts():
    seen, out = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        st, cur = [v], []
        seen.add(v)
        while st:
            x = st.pop(); cur.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in seen:
                    seen.add(y); st.append(y)
        out.append(cur)
    return out


rep = {}
gone = []
area_n = Vector()
acc = {}
for p in parts():
    fs = {f for v in p for f in v.link_faces}
    if any(f[lh] or f[lk] for f in fs):
        continue
    if all(((M @ v.co) - C).length < 1.6 * R for v in p):
        gone += list(fs)
        for f in fs:
            area_n += (M.to_3x3() @ f.normal) * f.calc_area()
        for v in p:
            for g, w in v[dl].items():
                if 'Ponytail' not in names[g] and not names[g].startswith(('Y', 'X')):
                    acc[g] = acc.get(g, 0) + w
rep['medallion_faces_removed'] = len(gone)
n = area_n.normalized()
if abs(n.y) < 0.5:
    n = Vector((0, -1, 0))
if n.y > 0:
    n = -n
top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
tot = sum(w for _, w in top)
W = [(g, w / tot) for g, w in top]
rep['medallion_weights'] = [(names[g], round(w, 3)) for g, w in W]
rep['normal'] = [round(x, 3) for x in n]
template = gone[0]
smooth = template.smooth
bmesh.ops.delete(bm, geom=gone, context='FACES_ONLY')
for v in [v for v in bm.verts if not v.link_faces]:
    bm.verts.remove(v)
if 'buckle' in opt:
    B = Vector([float(x) for x in opt['buckle'].split(',')])
    drop = []
    for p in parts():
        fs = {f for v in p for f in v.link_faces}
        if len(fs) < 12 and all(((M @ v.co) - B).length < 0.07 for v in p) and not any(f[lh] or f[lk] for f in fs):
            drop += list(fs)
    rep['buckle_shards'] = len(drop)
    bmesh.ops.delete(bm, geom=drop, context='FACES_ONLY')
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
# ---- the disc
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
X = Vector((1, 0, 0)); X = (X - n * X.dot(n)).normalized()
Y = n.cross(X).normalized()
if Y.z < 0:
    Y = -Y
SEG = 24
DOME, BACK = 0.005, 0.006
rings = []
for rr, h in ((0.33, 0.8), (0.72, 0.65), (0.97, 0.45), (1.0, 0.0), (1.0, -1.2)):
    ring = []
    for i in range(SEG):
        a = 2 * math.pi * i / SEG
        ox, oy = math.cos(a) * rr * R, math.sin(a) * rr * R
        ring.append((bm.verts.new(Mi @ (C + X * ox + Y * oy + n * (DOME * h))), ox / R, oy / R))
    rings.append(ring)
cv = bm.verts.new(Mi @ (C + n * DOME)), 0.0, 0.0
new = []
for i in range(SEG):
    j = (i + 1) % SEG
    new.append((cv, rings[0][i], rings[0][j]))
for ra, rb in zip(rings[:-1], rings[1:]):
    for i in range(SEG):
        j = (i + 1) % SEG
        new.append((ra[i], rb[i], rb[j]))
        new.append((ra[i], rb[j], ra[j]))
disc = []
for tri in new:
    f = bm.faces.new([t[0] for t in tri])
    f[lh] = 0; f[lk] = 0; f.smooth = smooth
    f.normal_update()
    if (M.to_3x3() @ f.normal).dot(((M @ f.calc_center_median()) - C + n * 0.02)) < 0:
        f.normal_flip()
    by = {t[0]: t for t in tri}
    for l in f.loops:
        t = by[l.vert]
        uv = (UC + t[1] * RUV, VC + t[2] * RUV)
        l[uvb].uv = uv; l[uvh].uv = uv
    disc.append(f)
for v in {v for f in disc for v in f.verts}:
    for g, w in W:
        v[dl][g] = w
rep['disc_faces'] = len(disc)
# ---- neck skirt
seen, loops = set(), []
for e in bm.edges:
    if not e.is_boundary or e in seen or not e.link_faces[0][lh]:
        continue
    lp, st = [], [e]
    while st:
        x = st.pop()
        if x in seen:
            continue
        seen.add(x); lp.append(x)
        for v in x.verts:
            st += [y for y in v.link_edges if y.is_boundary and y not in seen]
    loops.append(lp)


def info(lp):
    vs = {v for x in lp for v in x.verts}
    c = sum((M @ v.co for v in vs), Vector()) / len(vs)
    return c, max(((M @ v.co) - c).length for v in vs), vs


cand = []
for lp in loops:
    c, r, vs = info(lp)
    if 1.40 < c.z - floor < 1.56 and r > 0.07 and len(lp) > 15:
        cand.append((r, lp, c))
assert cand, 'no neck ring'
r, lp, c = max(cand, key=lambda t: t[0])
rep['neck_ring'] = {'edges': len(lp), 'radius': round(r, 3), 'height': round(c.z - floor, 3)}
out = bmesh.ops.extrude_edge_only(bm, edges=lp)
nv = [g for g in out['geom'] if isinstance(g, bmesh.types.BMVert)]
for v in nv:
    p = M @ v.co
    q = Vector((c.x + (p.x - c.x) * 0.92, c.y + (p.y - c.y) * 0.92, p.z - SKIRT))
    v.co = Mi @ q
skirt = [g for g in out['geom'] if isinstance(g, bmesh.types.BMFace)]
for f in skirt:
    f[lh] = 1; f[lk] = 0; f.smooth = True
    f.normal_update()
    cen = M @ f.calc_center_median()
    if (M.to_3x3() @ f.normal).dot(Vector((cen.x - c.x, cen.y - c.y, 0))) < 0:
        f.normal_flip()
rep['skirt_faces'] = len(skirt)
rep['tris'] = len(bm.faces)
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('MEDALLION', json.dumps(rep))
json.dump(rep, open(REP, 'w'), indent=1)
