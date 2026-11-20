"""Make the fitted 'Body' exactly mirror-symmetric about x = 0 (the MM9 body is): the kept half (KEEP=neg: the
animal's right, -X; KEEP=pos: its left, +X) is mirrored onto the other side and welded on the midline. Separate
pieces (eyes, teeth, claws) are mirrored with it. The per-vertex 'chain' attribute of the mirrored half is swapped to
the matching left/right leg chain (fit_quad.py CHAINS order: 0 fl, 1 fr, 2 hl, 3 hr, 4 tail).

Before mirroring, the tail (chain 4) is centred on the midline: its vertices are binned along the tail's principal
axis in the y-z plane and each bin's mean x is removed, faded in over TAIL_FADE of the tail length from where it
leaves the rump (the first bin no wider than 1.5x the median; a
tail that leaves the midline would be cut lengthwise into two). After mirroring, a band of MID_BAND around x = 0 is
relaxed (MID_ITERS Laplacian steps, weight falling off with |x|, midline vertices kept at x = 0) so the mirror seam
leaves no crease; the result is made exactly symmetric again from the kept half.

Args: <fit blend> <out blend> <report json> [out glb: the Body alone, for a second fit_quad.py pass]   env KEEP=neg|pos (default neg), MID_BAND (model units), MID_ITERS,
TAIL_FADE (fraction)
"""
import bpy, bmesh, sys, json, os
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
OUT_GLB = argv[3] if len(argv) > 3 else None
KEEP = os.environ.get('KEEP', 'neg')
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
me = body.data
co0 = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
chain0 = np.array([d.value for d in me.attributes['chain'].data])
tail = np.nonzero(chain0 == 4)[0]
tail_rep = {}
if len(tail):
    from mathutils import Vector
    T = co0[tail]
    c = T[:, 1:].mean(0)
    u, sv, vt = np.linalg.svd(T[:, 1:] - c)
    ax = vt[0]
    t = (T[:, 1:] - c) @ ax
    # the root end is the end nearer the body centre (y = 0 side of the bounding box of the whole body)
    body_c = co0[:, 1:].mean(0)
    if np.dot(body_c - c, ax) > 0:
        t = -t
    t = t - t.min()
    L = t.max()
    nb = 24
    edges = np.linspace(0, L, nb + 1)
    mids = (edges[:-1] + edges[1:]) / 2
    mx = np.array([T[(t >= a) & (t <= b), 0].mean() if ((t >= a) & (t <= b)).any() else np.nan
                   for a, b in zip(edges[:-1], edges[1:])])
    ok = ~np.isnan(mx)
    off = np.interp(t, mids[ok], mx[ok])
    # the chain region starts with rump skin: the tail proper begins at the first bin no wider than 1.5x the median
    wid = np.array([np.ptp(T[(t >= a) & (t <= b), 0]) if ((t >= a) & (t <= b)).any() else np.nan
                    for a, b in zip(edges[:-1], edges[1:])])
    start = float(mids[np.nonzero(ok & (wid < 1.5 * np.nanmedian(wid)))[0][0]])
    fade = float(os.environ.get('TAIL_FADE', '0.15'))
    f = np.clip((t - start) / max(fade * L, 1e-9), 0, 1)
    f = f * f * (3 - 2 * f)
    shift = off * f
    inv = body.matrix_world.inverted()
    for k, i in enumerate(tail):
        p = co0[i].copy(); p[0] -= shift[k]
        me.vertices[int(i)].co = inv @ Vector(tuple(p))
    me.update()
    tail_rep = {'tail_verts': int(len(tail)), 'tail_len': round(float(L), 4),
                'tail_start': round(start, 4), 'centre_offset_max': round(float(np.abs(off[t > start]).max()), 4)}
bm = bmesh.new()
bm.from_mesh(me)
before = len(bm.verts)
# '-X' keeps the negative side and mirrors it to +X ('X' the other way)
bmesh.ops.symmetrize(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:], direction='-X' if KEEP == 'neg' else 'X',
                     dist=1e-5)
bm.to_mesh(me)
bm.free()
me.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
chain = me.attributes['chain']
swap = {0: 1, 1: 0, 2: 3, 3: 2}
mirrored = (co[:, 0] > 1e-6) if KEEP == 'neg' else (co[:, 0] < -1e-6)
fixed = 0
for i in np.nonzero(mirrored)[0]:
    c = chain.data[int(i)].value
    want = {1: 0, 3: 2} if KEEP == 'neg' else {0: 1, 2: 3}
    if c in want:
        chain.data[int(i)].value = want[c]
        fixed += 1
for p in me.polygons:
    p.use_smooth = True
# relax the mirror seam
band = float(os.environ.get('MID_BAND', '0.02'))
iters = int(os.environ.get('MID_ITERS', '12'))
from mathutils.kdtree import KDTree
from mathutils import Vector
k0 = KDTree(len(co))
for i, p in enumerate(co):
    k0.insert(p, i)
k0.balance()
partner = np.array([k0.find((-p[0], p[1], p[2]))[1] for p in co])
E = np.array([tuple(e.vertices) for e in me.edges])
piece = np.array([d.value for d in me.attributes['piece'].data])
deg = np.maximum(np.bincount(E.ravel(), minlength=len(co)), 1)
w = np.clip(1 - np.abs(co[:, 0]) / band, 0, 1) * (piece == 0)
P = co.copy()
for _ in range(iters):
    acc = np.zeros_like(P)
    np.add.at(acc, E[:, 0], P[E[:, 1]]); np.add.at(acc, E[:, 1], P[E[:, 0]])
    P = P + 0.5 * w[:, None] * (acc / deg[:, None] - P)
mid = np.abs(co[:, 0]) < 1e-6
P[mid, 0] = 0
keep = (co[:, 0] <= 1e-6) if KEEP == 'neg' else (co[:, 0] >= -1e-6)
P[~keep] = P[partner[~keep]] * np.array([-1, 1, 1])
inv = body.matrix_world.inverted()
for i in np.nonzero(w > 0)[0]:
    me.vertices[int(i)].co = inv @ Vector(tuple(P[i]))
for i in np.nonzero(~keep)[0]:
    me.vertices[int(i)].co = inv @ Vector(tuple(P[i]))
me.update()
seam_move = float(np.linalg.norm(P - co, axis=1).max())
co = P
# symmetry check: every vertex has a mirror partner
from mathutils.kdtree import KDTree
k = KDTree(len(co))
for i, p in enumerate(co):
    k.insert(p, i)
k.balance()
err = np.array([k.find((-p[0], p[1], p[2]))[2] for p in co])
rep = {'keep': KEEP, 'tail': tail_rep, 'seam_relax_max_move': round(seam_move, 4), 'verts_before': before, 'verts_after': len(co), 'chain_swapped': fixed,
       'mirror_error_max': float(err.max()), 'mirror_error_p99': float(np.percentile(err, 99))}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
if OUT_GLB:
    for o in bpy.data.objects:
        o.select_set(o == body)
    bpy.context.view_layer.objects.active = body
    body.parent = None
    bpy.ops.export_scene.gltf(filepath=OUT_GLB, use_selection=True, export_format='GLB', export_yup=True,
                              export_materials='NONE', export_skins=False, export_animations=False,
                              export_attributes=False)
json.dump(rep, open(REP, 'w'), indent=1)
print('SYM ' + json.dumps(rep))
