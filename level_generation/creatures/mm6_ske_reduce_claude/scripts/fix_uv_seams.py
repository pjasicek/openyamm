"""UV repair of a texture-aware candidate (djn r62: a black shard on the neck). A collapse across a UV seam can leave a
face whose UVs land in the atlas's unpainted background. Per candidate face, the source UV coverage (rasterised source
triangles, padded 2 px) is sampled at the face's UV centroid and corners; a face outside it takes new UVs from the
source triangle nearest its 3D centroid: each corner's barycentric coordinates on that triangle's plane (extrapolated
when outside) give one consistent island. In/out: work/ladder.blend (REA_CAND, default Cand_70).
Usage: blender -b -P fix_uv_seams.py"""
import os
import bpy
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = 1024
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
src = bpy.data.objects['Body']; cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_70')]
sm, cm = src.data, cand.data
sm.calc_loop_triangles(); suv = sm.uv_layers.active.data
ST = [(t, [Vector(sm.vertices[v].co) for v in t.vertices], [Vector(suv[l].uv) for l in t.loops]) for t in sm.loop_triangles]
# coverage raster of the source layout
cov = np.zeros((N, N), bool)
for _, _, U in ST:
    P = np.array([[u.x * N, u.y * N] for u in U])
    x0, y0 = np.floor(P.min(0)).astype(int) - 2; x1, y1 = np.ceil(P.max(0)).astype(int) + 2
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, N - 1), min(y1, N - 1)
    if x1 < x0 or y1 < y0:
        continue
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
    a, b, c = P
    den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(den) < 1e-12:
        continue
    w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
    w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
    m = (w0 >= -.05) & (w1 >= -.05) & (1 - w0 - w1 >= -.05)
    cov[(ys[m] - .5).astype(int), (xs[m] - .5).astype(int)] = True
for _ in range(2):                                     # dilate by 2 px (Blender's Python has no scipy)
    c2 = cov.copy(); c2[1:] |= cov[:-1]; c2[:-1] |= cov[1:]; c2[:, 1:] |= cov[:, :-1]; c2[:, :-1] |= cov[:, 1:]; cov = c2
# djn atlas: body set u < 0.5, head set u > 0.5 (every head-set face lies above HEAD_Z). Body faces are matched only
# against body-side source triangles: the goatee tip hangs over the neck, and a neck face whose nearest source
# triangle was the goatee's underside took the beard's black island (a shard under the chin).
HEAD_Z = float(os.environ.get('UV_HEAD_Z', '1.755'))
BODY = [i for i, (_, V, U) in enumerate(ST) if sum(U, Vector((0, 0))).x / 3 < .5]
tree = KDTree(len(BODY))
for k, i in enumerate(BODY):
    V = ST[i][1]; tree.insert((V[0] + V[1] + V[2]) / 3, k)
tree.balance()


def inside(u):
    x, y = int(np.clip(u.x * N, 0, N - 1)), int(np.clip(u.y * N, 0, N - 1))
    return cov[y, x]


def uv_on(j, q):
    """UV of point q on source triangle j's plane (barycentric, extrapolated outside the triangle)"""
    _, V, SU = ST[j]
    e0, e1 = V[1] - V[0], V[2] - V[0]; n = e0.cross(e1)
    d00, d01, d11 = e0.dot(e0), e0.dot(e1), e1.dot(e1); den = d00 * d11 - d01 * d01
    q = q - n * ((q - V[0]).dot(n) / max(n.dot(n), 1e-18)) - V[0]
    b1 = (d11 * q.dot(e0) - d01 * q.dot(e1)) / den; b2 = (d00 * q.dot(e1) - d01 * q.dot(e0)) / den
    return SU[0] * (1 - b1 - b2) + SU[1] * b1 + SU[2] * b2


cuv = cm.uv_layers.active.data; fixed = []
for p in cm.polygons:
    U = [Vector(cuv[l].uv) for l in p.loop_indices]
    cen = sum(U, Vector((0, 0))) / len(U)
    co = [Vector(cm.vertices[v].co) for v in p.vertices]
    cc = sum(co, Vector()) / len(co)
    if cc.z >= HEAD_Z - .002 and cen.x > .5:
        continue                                        # head set: protected, the installed faces and UVs
    near = [BODY[k] for _, k, _ in tree.find_n(cc, 4)]
    # wrong island: the face's UV centroid is far from what every nearby body triangle maps this point to
    expected = min((uv_on(j, cc) - cen).length for j in near)
    if cen.x < .5 and inside(cen) and all(inside(u) for u in U) and expected < .012:
        continue
    j = near[0]
    _, V, SU = ST[j]
    e0, e1 = V[1] - V[0], V[2] - V[0]; n = e0.cross(e1)
    d00, d01, d11 = e0.dot(e0), e0.dot(e1), e1.dot(e1); den = d00 * d11 - d01 * d01
    for l, q in zip(p.loop_indices, co):
        q = q - n * ((q - V[0]).dot(n) / max(n.dot(n), 1e-18)) - V[0]
        b1 = (d11 * q.dot(e0) - d01 * q.dot(e1)) / den; b2 = (d00 * q.dot(e1) - d01 * q.dot(e0)) / den
        cuv[l].uv = SU[0] * (1 - b1 - b2) + SU[1] * b1 + SU[2] * b2
    fixed.append((p.index, tuple(round(x, 3) for x in (sum(co, Vector()) / len(co)))))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
print('UVFIX', len(fixed), 'faces re-mapped', fixed[:20])
