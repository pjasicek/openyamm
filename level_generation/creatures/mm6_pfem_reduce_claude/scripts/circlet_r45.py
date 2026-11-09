"""Round 2: the reduced circlet (Headband piece) was ragged, with flaps hanging onto the temples. It is rebuilt as a
clean ribbon fitted to the old band: plane by PCA, outer radius per angle (smoothed around the head), height from the
old band; outer face plus top and bottom edges (the inner face lies on the hair). Weights from the nearest old band
vertex, UVs in a dedicated square of the head atlas (compose paints the band flat brass). In place."""
import bpy, bmesh, json, math, os
import numpy as np
from mathutils import Vector, kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'r45_master.blend'))
PARTS = json.loads(bpy.context.scene['pfem_parts']); HB = PARTS.index('Headband')
ob = bpy.data.objects['Peasant']; me = ob.data
part = np.array([a.value for a in me.attributes['part'].data])
faces = [p for p in me.polygons if part[p.index] == HB]
vids = sorted({v for p in faces for v in p.vertices})
X = np.array([me.vertices[i].co[:] for i in vids])
c = X.mean(0); _, _, vt = np.linalg.svd(X - c); e1, e2, nrm = vt[0], vt[1], vt[2]
if nrm[2] < 0:
    nrm = -nrm
rel = X - c; a = np.arctan2(rel @ e2, rel @ e1); rad = np.hypot(rel @ e1, rel @ e2); hgt = rel @ nrm
NS = 48; bins = np.linspace(-math.pi, math.pi, NS + 1)
r_out = np.array([np.percentile(rad[(a >= bins[i]) & (a < bins[i + 1])], 90) if ((a >= bins[i]) & (a < bins[i + 1])).sum() else np.nan for i in range(NS)])
r_out = np.where(np.isnan(r_out), np.nanmedian(r_out), r_out)
k = np.exp(-0.5 * (np.arange(-3, 4) / 1.5) ** 2); k /= k.sum()
r_out = np.array([sum(k[j] * r_out[(i + j - 3) % NS] for j in range(7)) for i in range(NS)])
mid = np.array([np.median(hgt[(a >= bins[i]) & (a < bins[i + 1])]) if ((a >= bins[i]) & (a < bins[i + 1])).sum() else np.nan for i in range(NS)])
mid = np.where(np.isnan(mid), np.nanmedian(mid), mid)
mid = np.array([sum(k[j] * mid[(i + j - 3) % NS] for j in range(7)) for i in range(NS)])
half = float(np.clip(np.percentile(np.abs(hgt - np.median(hgt)), 80), 0.002, 0.004)); depth = 0.0025
# UV: a dedicated square in the largest empty area of the head atlas (compose paints it brass); a few texels inside
# an old band island mipmapped into the surrounding hair and turned the ribbon brown at a distance
me.calc_loop_triangles(); uvl = me.uv_layers.active.data
head = np.array([a.value for a in me.attributes['head'].data]); R = 512
occ = np.zeros((R, R), bool)
for t in me.loop_triangles:
    if head[t.polygon_index] and part[t.polygon_index] != HB:
        q = np.array([uvl[l].uv[:] for l in t.loops]) * R
        x0, y0 = np.floor(q.min(0)).astype(int); x1, y1 = np.ceil(q.max(0)).astype(int)
        occ[max(y0, 0):min(y1, R - 1) + 1, max(x0, 0):min(x1, R - 1) + 1] = True     # bounding boxes: conservative
sq = np.zeros((R, R), np.int32)                        # largest empty square ending at each texel
for y in range(1, R):
    for x in range(1, R):
        if not occ[y, x]:
            sq[y, x] = 1 + min(sq[y - 1, x], sq[y, x - 1], sq[y - 1, x - 1])
iy, ix = np.unravel_index(np.argmax(sq), sq.shape); n = int(sq[iy, ix])
uvc = Vector(((ix + 1 - n / 2) / R, (iy + 1 - n / 2) / R)); side = 0.3 * n / R
uvd = [Vector((-side, -side)), Vector((side, -side)), Vector((side, side)), Vector((-side, side))]
print('CIRCLET UV square at', tuple(round(x, 3) for x in uvc), 'half side', round(side, 4))
tree = kdtree.KDTree(len(vids))
for i, v in enumerate(vids):
    tree.insert(me.vertices[v].co, i)
tree.balance()
weights = {i: [(g.group, g.weight) for g in me.vertices[v].groups] for i, v in enumerate(vids)}
mat = faces[0].material_index
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if part[f.index] == HB], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
pl = bm.faces.layers.int.get('part'); hl = bm.faces.layers.int.get('head'); dl = bm.verts.layers.deform.verify(); ul = bm.loops.layers.uv.active
rings = []
for (dr, dh) in ((0.0, half), (depth, half), (depth, -half), (0.0, -half)):   # inner-top, outer-top, outer-bottom, inner-bottom
    ring = []
    for i in range(NS):
        ang = (bins[i] + bins[i + 1]) / 2
        p = c + (r_out[i] - depth + dr) * (math.cos(ang) * e1 + math.sin(ang) * e2) + (mid[i] + dh) * nrm
        v = bm.verts.new(Vector(p))
        for g, w in weights[tree.find(Vector(p))[1]]:
            v[dl][g] = w
        ring.append(v)
    rings.append(ring)
new = 0
for r in range(3):                                     # top, outer face, bottom
    for i in range(NS):
        j = (i + 1) % NS
        quad = [rings[r][i], rings[r][j], rings[r + 1][j], rings[r + 1][i]]
        f = bm.faces.new(quad)
        f.material_index = mat; f[pl] = HB; f[hl] = 1; f.smooth = True
        for li, loop in enumerate(f.loops):
            loop[ul].uv = uvc + uvd[li % 4]
        new += 1
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[pl] == HB])
# outward check: outer face normals point away from the ring centre
outer = [f for f in bm.faces if f[pl] == HB]
cen = Vector(c)
flip = [f for f in outer if (f.calc_center_median() - cen).dot(f.normal) < 0]
if len(flip) > len(outer) / 2:
    bmesh.ops.reverse_faces(bm, faces=outer)
bmesh.ops.triangulate(bm, faces=outer)
bm.to_mesh(me); bm.free(); me.update()
assert all(v.groups for v in me.vertices)
print('CIRCLET old faces', len(faces), 'new quads', new, 'radius mm', round(float(np.median(r_out)) * 1000, 1),
      'height mm', round(2000 * half, 1), 'triangles', len(me.loop_triangles) if me.loop_triangles else sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_mainfile()
