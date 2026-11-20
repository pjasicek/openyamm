"""Rebuild the last part of each sleeve on the UV master without touching the painted layout elsewhere. Meshy's shell ends raggedly (open underside, inverted faces) a few cm short of the lace cuff,
and fit_ghost.py's rings bridged only part of it, so the forearm ended in thin strands. Cut at the last complete ring (bisect keeps UVs), extrude three rings into the cuff, and give them a new chart in free
atlas space; the texels of that chart are copied from the forearm above the cut, same column (compose_ghost.py applies work/sleeve_<side>.npz). Faces of the arm that point into it are flipped.
Args: <in blend> <out blend>"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
A = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=A[0])
body = bpy.data.objects['Body']; arm = body.parent
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
uvl = bm.loops.layers.uv['UVMap']
pl = bm.faces.layers.int['part']; hl = bm.faces.layers.int['hand']
SHIFT = 0.15
import json
RJ = json.load(open(os.path.join(os.path.dirname(A[0]), 'sleeve_rects.json')))     # free rectangles of the atlas, from the 2K coverage
SIZE = 2048
W_, H_ = RJ['W'], RJ['H']


cuffz = {}
# find cuff comps: not connected to anything but near the wrist; the sleeve test skips them
sides = {'01': 1.0, '': -1.0}
out = {}
for tag, sign in sides.items():
    s0, wr = J['Zarmpiv' + tag], J['Zhand' + tag]
    L = float(np.linalg.norm(wr - s0)); u = (wr - s0) / L
    uv = Vector(u.tolist())
    # sleeve faces: on this arm, not hand; cuff pieces are the small islands
    seen = set(); isl = []
    for f in bm.faces:
        if f in seen or f[hl] or f[pl] or f.calc_center_median().x * sign < 0.2:
            continue
        st = [f]; cur = [f]; seen.add(f)
        while st:
            x = st.pop()
            for e in x.edges:
                for y in e.link_faces:
                    if y not in seen and not y[hl] and not y[pl]:
                        seen.add(y); st.append(y); cur.append(y)
        isl.append(cur)
    isl.sort(key=len, reverse=True)
    shell = set(isl[0])
    print('ISLANDS', [len(x) for x in isl][:6])
    vs = list({v for f in shell for v in f.verts})
    bvh = BVHTree.FromPolygons([v.co.copy() for v in vs], [[vs.index(v) for v in f.verts] for f in shell]) if False else None
    idx = {v: i for i, v in enumerate(vs)}
    fl = list(shell)
    bvh = BVHTree.FromPolygons([v.co.copy() for v in vs], [[idx[v] for v in f.verts] for f in fl])
    p0 = Vector(s0.tolist())
    # perpendicular frame
    ref = Vector((0, 1, 0)); e1 = (ref - uv * ref.dot(uv)).normalized(); e2 = uv.cross(e1)


    def ray(al, th):
        c = p0 + uv * al; d = e1 * math.cos(th) + e2 * math.sin(th)
        hit = bvh.ray_cast(c + d * 0.2, -d, 0.2)
        return hit


    cut = None
    for al in np.arange(L - 0.02, 0.2, -0.004):
        if all(ray(al, t * 2 * math.pi / 28)[0] is not None for t in range(28)):
            cut = float(al); break
    cut -= 0.004
    print('CUT at', cut, 'of', L)
    # source of the new chart's texels, before the cut: hit face -> barycentric UV
    x, y = RJ['rects'][0 if tag else 1]
    src = np.zeros((H_, W_, 2), np.float32); ok = np.zeros((H_, W_), bool)
    from mathutils.geometry import barycentric_transform
    for j in range(H_):
        al = cut - SHIFT + (j + 0.5) / H_ * SHIFT
        for i in range(W_):
            th = (i + 0.5) / W_ * 2 * math.pi
            hit = ray(al, th)
            if hit[0] is None:
                continue
            f = fl[hit[2]]
            co = [l.vert.co for l in f.loops]; uvs = [Vector((l[uvl].uv.x, l[uvl].uv.y, 0)) for l in f.loops]
            q = barycentric_transform(hit[0], co[0], co[1], co[2], uvs[0], uvs[1], uvs[2])
            src[j, i] = (q.x, q.y); ok[j, i] = True
    print('SOURCE ok', ok.mean())
    np.savez(os.path.join(os.path.dirname(A[1]), f'sleeve_{"R" if tag else "L"}.npz'), rect=np.array([x, y, W_, H_]), src=src, ok=ok)
    # cut
    geom = list({e for f in shell for e in f.edges}) + list(vs) + list(shell)
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=p0 + uv * cut, plane_no=uv, clear_outer=True, dist=1e-5)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    ring = [e for e in bm.edges if e.is_boundary and all(abs((v.co - p0).dot(uv) - cut) < 2e-4 for v in e.verts)]
    rv = list({v for e in ring for v in e.verts})
    print('RING edges', len(ring), 'verts', len(rv))
    cen = sum((v.co for v in rv), Vector()) / len(rv)
    a_cuff = L + 0.012
    rings = [ring]
    for k, (fa, fr) in enumerate(((1 / 3, 0.99), (2 / 3, 0.95), (1.0, 0.86))):
        ex = bmesh.ops.extrude_edge_only(bm, edges=rings[-1])
        nv = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMVert)]
        ne = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMEdge) and all(v in nv for v in g.verts)]
        nf = [g for g in ex['geom'] if isinstance(g, bmesh.types.BMFace)]
        tgt = cen + uv * (a_cuff - cut) * fa
        for v in nv:
            al = (v.co - p0).dot(uv)
            rr = v.co - p0 - uv * al
            r0 = rr - (cen - p0 - uv * (cen - p0).dot(uv))
            v.co = tgt + r0 * (fr / ([0.99, 0.95, 0.86][k - 1] if k else 1.0))
        for f in nf:
            f[pl] = 0; f[hl] = 0
            for l in f.loops:
                p = l.vert.co - p0
                al = p.dot(uv); th = math.atan2((p - uv * al).dot(e2), (p - uv * al).dot(e1)) % (2 * math.pi)
                fv = (al - cut) / (a_cuff - cut)
                l[uvl].uv = ((x + th / (2 * math.pi) * W_) / SIZE, 1 - (y + (1 - fv) * H_) / SIZE)
            # the column across the seam
            us = [l[uvl].uv.x for l in f.loops]
            if max(us) - min(us) > 0.5 * W_ / SIZE:
                for l in f.loops:
                    if l[uvl].uv.x < (x + 0.5 * W_) / SIZE:
                        l[uvl].uv.x += W_ / SIZE
        rings.append(ne)
    # every arm face points away from its axis
    n = 0
    for f in bm.faces:
        if f[hl] or f[pl] or f.calc_center_median().x * sign < 0.25:
            continue
        f.normal_update()
        c = f.calc_center_median() - p0
        al = c.dot(uv)
        if al < 0.1 or f not in shell and False:
            continue
        if f.is_valid and (c - uv * al).length < 0.11 and (c - uv * al).dot(f.normal) < 0 and al < L + 0.002 and not any(g in isl[1:] for g in [f]):
            pass
    flip = []
    for f in bm.faces:
        if f[hl] or f[pl] or f.calc_center_median().x * sign < 0.25:
            continue
        f.normal_update()
        c = f.calc_center_median() - p0
        al = c.dot(uv); rad = c - uv * al
        if 0.1 < al and rad.length < 0.11 and f.calc_area() > 0 and rad.dot(f.normal) < 0:
            flip.append(f)
    # the cuff islands are lace with inner sides: leave them out
    flipset = [f for f in flip if not any(f in i for i in isl[1:])]
    if flipset:
        bmesh.ops.reverse_faces(bm, faces=flipset)
    print('FLIPPED', len(flipset))
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3], quad_method='FIXED')
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=A[1])
print('REPAIRED', len(me.vertices), len(me.polygons))
