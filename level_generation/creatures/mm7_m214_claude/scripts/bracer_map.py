"""Texel map for the right forearm bracer (user review 2026-10-20: Meshy painted the left forearm's tooled leather
bracer but left the right forearm bare skin). Rest pose of work/rig_v6.blend: every body-set texel (UVMap, 1024) of the
right forearm shell (piece 11) is mirrored to the left (x -> -x) and matched to the closest point of the left forearm
shell (piece 12); writes its source UV and the 3x3 that carries a tangent-space normal (Meshy's +y-down convention)
from the source triangle's frame through the mirror into the target triangle's frame. bracer_apply.py copies the maps.
Args: -- <blend> <out npz>   (env SRC=12 DST=11 N=1024 PAD=2)"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); out = a[1]
SRC, DST = int(os.environ.get('SRC', '12')), int(os.environ.get('DST', '11'))
N, PAD = int(os.environ.get('N', '1024')), int(os.environ.get('PAD', '2'))
body = bpy.data.objects['Body']; me = body.data
me.calc_loop_triangles()
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
uvl = me.uv_layers['UVMap'].data
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
tris = [t for t in me.loop_triangles]
src = [t for t in tris if pv[t.vertices[0]] == SRC]
dst = [t for t in tris if pv[t.vertices[0]] == DST]
MIR = np.diag([-1.0, 1.0, 1.0])


def frame(t):
    """Columns: +u direction, -v direction (Meshy's +y down the image), normal; per triangle."""
    P = co[list(t.vertices)]; U = np.array([tuple(uvl[l].uv) for l in t.loops])
    e1, e2 = P[1] - P[0], P[2] - P[0]; d1, d2 = U[1] - U[0], U[2] - U[0]
    det = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(det) < 1e-12:
        return None, P, U
    tu = (e1 * d2[1] - e2 * d1[1]) / det; tv = (e2 * d1[0] - e1 * d2[0]) / det
    n = np.cross(e1, e2); n /= np.linalg.norm(n)
    tu -= n * (tu @ n); tu /= np.linalg.norm(tu)
    tv -= n * (tv @ n) + tu * (tv @ tu); tv /= np.linalg.norm(tv)
    return np.stack([tu, -tv, n], 1), P, U


sf = [frame(t) for t in src]
bvh = BVHTree.FromPolygons([Vector(tuple(c @ MIR)) for c in co], [tuple(t.vertices) for t in src])
rows, cols, suv, mats = [], [], [], []
for t in dst:
    Bt, P, U = frame(t)
    if Bt is None:
        continue
    px = U * N
    lo = np.floor(px.min(0)).astype(int) - PAD; hi = np.ceil(px.max(0)).astype(int) + PAD
    xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
    pts = np.stack([xs.ravel() + 0.5, ys.ravel() + 0.5], 1)
    T = np.array([[px[0, 0] - px[2, 0], px[1, 0] - px[2, 0]], [px[0, 1] - px[2, 1], px[1, 1] - px[2, 1]]])
    if abs(np.linalg.det(T)) < 1e-9:
        continue
    l12 = np.linalg.solve(T, (pts - px[2]).T).T; bc = np.column_stack([l12, 1 - l12.sum(1)])
    # inside, or within PAD texels of the triangle (seam padding)
    edge = PAD / max(np.linalg.norm(px[1] - px[0]), np.linalg.norm(px[2] - px[0]), 1.0)
    ok = (bc >= -edge).all(1)
    for (x, y), b in zip(pts[ok], np.clip(bc[ok], 0, None)):
        b = b / b.sum(); p = b @ P
        hit = bvh.find_nearest(Vector(tuple(p)))
        if hit[0] is None:
            continue
        s = src[hit[2]]; Bs, Ps, Us = sf[hit[2]]
        if Bs is None:
            continue
        q = np.array(hit[0]) @ MIR                                    # back on the left shell
        A = np.column_stack([Ps[0] - Ps[2], Ps[1] - Ps[2]])
        l2 = np.linalg.lstsq(A, q - Ps[2], rcond=None)[0]; bs = np.clip(np.append(l2, 1 - l2.sum()), 0, 1); bs /= bs.sum()
        rows.append(N - 1 - int(y)); cols.append(int(x)); suv.append(bs @ Us)
        mats.append(Bt.T @ MIR @ Bs)
rows, cols = np.array(rows), np.array(cols)
keep = (rows >= 0) & (rows < N) & (cols >= 0) & (cols < N)
np.savez(out, rows=rows[keep], cols=cols[keep], suv=np.array(suv)[keep], mats=np.array(mats)[keep], n=N)
print(f'BRACERMAP {len(dst)} target / {len(src)} source triangles, {int(keep.sum())} texels -> {out}')
