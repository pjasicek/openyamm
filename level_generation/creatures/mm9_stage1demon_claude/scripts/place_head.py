"""Step B: the head-only Meshy model onto MM9's head. Similarity fit (scale, pitch about x, y/z shift; x stays 0 so the head
stays symmetric) of the head core (|x| < core_x, no horns) to MM9's head surface, by alternating nearest points; then the
near half (x < 0) is kept and mirrored. Components become parts: 10 head shell, 12 teeth, 13 eyes, 14 tongue.
The fitted body's holes at the neck are capped. Args: <fit blend> <head glb> <mm9 npz> <config json> <out blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
FIT, HEAD, MM9, CFG, OUT = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(CFG))['head']
_d = np.load(MM9); A = _d['A']; J = dict(zip([str(x) for x in _d['jn']], _d['jp']))
bpy.ops.wm.open_mainfile(filepath=FIT)
body = bpy.data.objects['Body']
ex = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=HEAD)
new = [o for o in bpy.data.objects if o not in ex]
hd = next(o for o in new if o.type == 'MESH'); Mw = hd.matrix_world.copy(); hd.parent = None; hd.matrix_world = Mw
for o in new:
    if o is not hd: bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.objects.active = hd
for o in bpy.data.objects: o.select_set(o is hd)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
hd.data.materials.clear()
bm = bmesh.new(); bm.from_mesh(hd.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(hd.data); bm.free()
me = hd.data; H = np.array([v.co[:] for v in me.vertices]); n = len(H)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices; nbr[a].append(b); nbr[b].append(a)
comp = -np.ones(n, int); k = 0
for i in range(n):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = k
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = k; st.append(y)
    k += 1
sizes = np.bincount(comp); order = np.argsort(-sizes)
main = order[0]
PART = np.full(n, 12)                                   # teeth by default (small pieces)
PART[comp == main] = 10
for c in order[1:]:
    m = comp == c; ctr = H[m].mean(0)
    if sizes[c] > 100 and abs(ctr[0]) > 0.03 and ctr[2] > cfg['eye_z_raw']: PART[m] = 13      # eyes
    elif sizes[c] > 250: PART[m] = 14                                                         # tongue
print('HEAD comps', k, {int(p): int((PART == p).sum()) for p in np.unique(PART)})
# MM9 head surface: in front of the neck, above the chest
mh = (A[:, 1] < cfg['mm9_y_max']) & (A[:, 2] > cfg['mm9_z_min']) & (A[:, 2] < cfg['mm9_z_max']) & (np.abs(A[:, 0]) < cfg['core_x'])
T = A[mh]
core = (PART == 10) & (np.abs(H[:, 0]) < cfg['core_x_raw']) & (H[:, 2] > cfg['core_z_min_raw']) & (H[:, 1] < cfg['core_y_max_raw'])
S = H[core]
print('FIT points mm9', len(T), 'head core', len(S))


def apply(X, s, a, t):
    c, sn = np.cos(a), np.sin(a); R = np.array([[1, 0, 0], [0, c, -sn], [0, sn, c]])
    return (X @ R.T) * s + t


kt = KDTree(len(T))
for i, p in enumerate(T): kt.insert(p, i)
kt.balance()
s = np.ptp(T[:, 1]) / np.ptp(S[:, 1]); a = np.radians(cfg.get('pitch0_deg', 0))
t = T.mean(0) - apply(S, s, a, 0).mean(0); t[0] = 0
for it in range(60):
    X = apply(S, s, a, t)
    nn = np.array([kt.find(p)[1] for p in X]); Y = T[nn]
    ks = KDTree(len(X))
    for i, p in enumerate(X): ks.insert(p, i)
    ks.balance()
    nn2 = np.array([ks.find(p)[1] for p in T])
    src = np.r_[S, S[nn2]]; dst = np.r_[Y, T]
    best = None
    for da in np.radians(np.linspace(-3, 3, 13)):
        a2 = a + da; c, sn = np.cos(a2), np.sin(a2); R = np.array([[1, 0, 0], [0, c, -sn], [0, sn, c]])
        Rs = src @ R.T; ms, md = Rs.mean(0), dst.mean(0)
        s2 = float(((Rs - ms)[:, 1:] * (dst - md)[:, 1:]).sum() / ((Rs - ms)[:, 1:] ** 2).sum())
        t2 = md - ms * s2; t2[0] = 0
        err = float((np.linalg.norm(Rs * s2 + t2 - dst, axis=1) ** 2).mean())
        if best is None or err < best[0]: best = (err, a2, s2, t2)
    _, a, s, t = best
    if it % 10 == 0 or it == 59: print('ICP', it, 'rms %.4f' % np.sqrt(best[0]), 'scale %.3f' % s, 'pitch %.1f' % np.degrees(a), t.round(3))
s *= cfg.get('scale_gain', 1.0)
t = t + np.array(cfg.get('offset', [0, 0, 0]))
H2 = apply(H, s, a, t)
for v, p in zip(me.vertices, H2): v.co = Vector(p)
pa = me.attributes.new('part', 'INT', 'POINT'); pa.data.foreach_set('value', PART.tolist())
for nm in ('drop', 'digit'):
    q = me.attributes.new(nm, 'INT', 'POINT'); q.data.foreach_set('value', ([0] if nm == 'drop' else [-1]) * n)
me.update()
bm = bmesh.new(); bm.from_mesh(me)
g = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-4: v.co.x = 0
g = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.mirror(bm, geom=g, axis='X', merge_dist=1e-4)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
print('HEAD placed: snout tip', H2[PART == 10][np.argmin(H2[PART == 10][:, 1])].round(3), 'mm9 XheadB', J['XheadB'].round(3), 'jawpiv', J['Xjawpiv'].round(3))
# body: Meshy's own head (main skin in the head box) is removed and its hole capped; the head model's open neck ring is capped too
bm = bmesh.new(); bm.from_mesh(body.data); ol = bm.verts.layers.int['oldhead']; pl = bm.verts.layers.int['part']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[ol]], context='VERTS')
bnd = [e for e in bm.edges if e.is_boundary and all(v[pl] == 0 for v in e.verts) and min(v.co.z for v in e.verts) > cfg['cap_z_min'] and max(v.co.y for v in e.verts) < -0.3]
r_ = bmesh.ops.holes_fill(bm, edges=bnd, sides=0); bmesh.ops.triangulate(bm, faces=r_['faces'])
capv = {v for f in r_['faces'] for v in f.verts}
print('NECK caps', len(r_['faces']), 'boundary edges', len(bnd))
bm.to_mesh(body.data); bm.free()
bm = bmesh.new(); bm.from_mesh(me); pl = bm.verts.layers.int['part']
bnd = [e for e in bm.edges if e.is_boundary and all(v[pl] == 10 for v in e.verts)]
r_ = bmesh.ops.holes_fill(bm, edges=bnd, sides=0); bmesh.ops.triangulate(bm, faces=r_['faces'])
print('HEAD bottom caps', len(r_['faces']), 'boundary edges', len(bnd))
bm.to_mesh(me); bm.free()
for o in bpy.data.objects: o.select_set(o in (body, hd))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print('JOINED verts', len(body.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
