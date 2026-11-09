"""Raw Meshy parts -> symmetric labelled parts, Blender frame (faces -Y, z up), MM9's origin (soles at z = -0.9366). Robe: +x half mirrored. Hands: posed MPFB, wrist 0.523 m from the shoulder (MM9's arm length), stub into the sleeve.
Head: head-only ST placed by the eyes, ears and hair pressed inside the hood's lining, the part behind the ears removed (the hood hides it). Shoes moved to MM9's feet. Shins: a plain tube, Calf only. Args: <body raw> <head raw> <hand npz> <out npz>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
BODY, HEAD, HAND, OUT = sys.argv[sys.argv.index('--') + 1:]
Z0 = -0.9366; X0 = 0.0035
D = np.load(BODY); co, tri, comp = D['co'] + [X0, 0, Z0], D['tri'], D['comp']
H = np.load(HEAD); hco, htri, hcomp = H['co'], H['tri'], H['comp']
# ---- shells of comp 0 (robe, head, a chin fragment), over manifold edges
f0 = np.where(comp[tri[:, 0]] == 0)[0]
from collections import defaultdict
ed = defaultdict(list)
for f in f0:
    a, b, c = tri[f]
    for e in ((a, b), (b, c), (c, a)): ed[tuple(sorted(e))].append(f)
adj = defaultdict(list)
for e, fs in ed.items():
    if len(fs) == 2: adj[fs[0]].append(fs[1]); adj[fs[1]].append(fs[0])
lab = {}; sizes = []
for f in f0:
    if f in lab: continue
    n = len(sizes); st = [f]; lab[f] = n; c = 0
    while st:
        x = st.pop(); c += 1
        for y in adj[x]:
            if y not in lab: lab[y] = n; st.append(y)
    sizes.append(c)
robe_f = np.array([f for f in f0 if lab[f] == int(np.argmax(sizes))])
print('ROBE faces', len(robe_f), 'shells', sizes)
bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection
def mesh(name, c, t):
    u, inv = np.unique(t.ravel(), return_inverse=True)
    me = bpy.data.meshes.new(name); me.from_pydata(c[u].tolist(), [], inv.reshape(-1, 3).tolist()); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return o
def C(*cs): return tri[np.isin(comp[tri[:, 0]], cs)]
def mirror_mid(o, keep_positive=True):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=not keep_positive, clear_inner=keep_positive, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.mirror(bm, geom=g, axis='X', merge_dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
def pair(o):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    g = list(bm.verts) + list(bm.edges) + list(bm.faces); ret = bmesh.ops.duplicate(bm, geom=g)
    for e in ret['geom']:
        if isinstance(e, bmesh.types.BMVert): e.co.x = -e.co.x
    bmesh.ops.reverse_faces(bm, faces=[e for e in ret['geom'] if isinstance(e, bmesh.types.BMFace)]); bm.to_mesh(me); bm.free()
def move(o, f):
    for v in o.data.vertices: v.co = Vector(f(np.array(v.co[:])))
parts = {}
parts['robe'] = mesh('robe', co, tri[robe_f]); mirror_mid(parts['robe'])
parts['belt'] = mesh('belt', co, C(3)); mirror_mid(parts['belt'])
parts['knots'] = mesh('knots', co, C(4)); pair(parts['knots'])
parts['cords'] = mesh('cords', co, C(12)); pair(parts['cords'])
s = mesh('shoes', co, C(7, 14)); move(s, lambda p: p + [-0.03, 0.025, 0]); pair(s); parts['shoes'] = s
# ---- shin: a tube from the shoe's top ring up, in the Calf's frame (MM9's Calf at x 0.118, z -0.394)
top = co[np.unique(C(7).ravel())]; top = top[top[:, 2] > top[:, 2].max() - 0.012] + [-0.03, 0.025, 0]
c0 = top.mean(0); r0 = float(np.linalg.norm(top - c0, axis=1).mean()) * 1.05
print('SHIN top ring', c0.round(3), r0)
N = 10; rings = [(c0 + [0, 0, -0.03], r0), (c0 + [0, 0, 0.10], r0 * 1.05), (np.array([0.116, 0.0, -0.46]), r0 * 1.25)]
V = []; T = []
for i, (c_, r_) in enumerate(rings):
    for k in range(N):
        a = 2 * np.pi * k / N; V.append(c_ + [r_ * np.cos(a), r_ * np.sin(a), 0])
    if i:
        for k in range(N):
            a, b = (i - 1) * N + k, (i - 1) * N + (k + 1) % N; T += [[a, b, b + N], [a, b + N, a + N]]
parts['shins'] = mesh('shins', np.array(V), np.array(T)); pair(parts['shins'])
# ---- the sleeve axis and hands
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meshlib import section, nearest_loop
me = parts['robe'].data; me.calc_loop_triangles()
rc = np.array([v.co[:] for v in me.vertices]); rt = np.array([lt.vertices[:] for lt in me.loop_triangles])
d = np.array([.78, -.3, -.55]); d /= np.linalg.norm(d); p = np.array([.28, -.007, .42]); line = []
for i in range(14):
    l = nearest_loop(section(rc, rt, p, d), p)
    if l is None or np.linalg.norm(l['c'] - p) > .06: break
    line.append(l['c']); p = l['c'] + d * .025
line = np.array(line); ax = line[-3] - line[0]; ax /= np.linalg.norm(ax); print('SLEEVE axis', ax.round(3), line[0].round(3), line[-1].round(3))
MM9_SH = np.array([0.229, 0, 0.470]); sh = line[0] + ax * ((MM9_SH[0] - line[0][0]) / ax[0]); wr = sh + ax * 0.523
print('SHOULDER', sh.round(3), 'WRIST', wr.round(3))
Hd = np.load(HAND); hc, ht = Hd['co'], Hd['tri']; hj = json.loads(str(Hd['joints'])); F = json.loads(str(Hd['frame']))
w0, hd, t0, n0 = [np.array(F[k]) for k in ('w', 'hd', 't', 'n')]
S = 0.205 / F['L']
# target frame: fingers along the arm axis a little below it, thumb forward (-y), palm down
fd = ax.copy(); th = np.array([0, -1.0, 0]); th -= fd * (th @ fd); th /= np.linalg.norm(th)
# MPFB frame: hd fingers, t from pinky to index (the thumb side), n palm normal
A = np.c_[hd, t0, np.cross(hd, t0)]; nz = np.cross(fd, th); B = np.c_[fd, th, nz]
Rm = B @ A.T
print('HAND det', np.linalg.det(Rm), 'scale', S)
def tf(p): return (np.asarray(p) - w0) @ Rm.T * S + wr
hq0 = tf(hc)
# the stub (behind the wrist) straightened onto the sleeve axis, by a rotation about the wrist that fades over the first 3 cm into the hand
al = (hq0 - wr) @ fd; beh = hq0[al < -0.05]; sd = (wr - beh.mean(0)); sd /= np.linalg.norm(sd); print('HAND stub axis vs sleeve deg', np.degrees(np.arccos(np.clip(sd @ fd, -1, 1))))
def rodr(a, b, k):
    v = np.cross(a, b); s_ = np.linalg.norm(v); th_ = np.arctan2(s_, a @ b) * k
    if s_ < 1e-9: return np.eye(3)
    v /= s_; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(th_) * K + (1 - np.cos(th_)) * K @ K
def straighten(p):
    p = np.atleast_2d(p); a = (p - wr) @ fd; k = np.clip((0.03 - a) / 0.06, 0, 1); k = k * k * (3 - 2 * k)
    out = p.copy()
    for i in range(len(p)):
        out[i] = wr + rodr(sd, fd, k[i]) @ (p[i] - wr)
    return out
_tf = tf
def tf(p): return straighten(_tf(p))
o = mesh('hands', tf(hc), ht)
hj2 = {k: tf(np.array(v)).tolist() for k, v in hj.items()}
# weights carried by position (welded order may change)
pair(o); parts['hands'] = o
# ---- head
Eh = np.array([hco[hcomp == 1].mean(0), hco[hcomp == 2].mean(0)]); Eb = np.array([co[comp == 8].mean(0), co[comp == 9].mean(0)])
xm = Eh[:, 0].mean(); HS = float(os.environ.get('HSCALE', '0.94'))
Sh = np.linalg.norm(Eb[1] - Eb[0]) / np.linalg.norm(Eh[1] - Eh[0]) * HS
hq = (hco - [xm, 0, 0]) * Sh + [0, Eb[:, 1].mean() - Eh[:, 1].mean() * Sh + float(os.environ.get('HDY', '-0.012')), Eb[:, 2].mean() - Eh[:, 2].mean() * Sh + float(os.environ.get('HDZ', '-0.01'))]
print('HEAD scale', Sh, 'eye gap', np.linalg.norm(Eh[1] - Eh[0]) * Sh, 'z', hq[:, 2].min(), hq[:, 2].max(), 'y', hq[:, 1].min(), hq[:, 1].max(), 'x', hq[:, 0].min(), hq[:, 0].max())
o = mesh('head', hq, htri[hcomp[htri[:, 0]] == 0]); e = mesh('eyes0', hq, htri[hcomp[htri[:, 0]] == 2]); pair(e)
mirror_mid(o, keep_positive=False); parts['head'] = o
# one closed surface: head + eyeballs through a fine voxel remesh, so Meshy's cracks at brow, lips and chin close; the iris is paint on it
for x in bpy.data.objects: x.select_set(x in (o, e))
bpy.context.view_layer.objects.active = o
bpy.ops.object.join()
md = o.modifiers.new('r', 'REMESH'); md.mode = 'VOXEL'; md.voxel_size = 0.0011; md.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='r')
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); print('HEAD remesh', len(bm.verts))
band = [v for v in bm.verts if abs(v.co.x) < 0.010]
for _ in range(5): bmesh.ops.smooth_vert(bm, verts=band, factor=0.5, use_axis_x=False, use_axis_y=True, use_axis_z=True)
# inside the hood's lining: a ray from the axis to each vertex must not pass the robe
ro = parts['robe']; bpy.context.view_layer.update()
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromObject(ro, bpy.context.evaluated_depsgraph_get())
n = 0; pressed = set()
for v in bm.verts:
    if v.co.z < 0.60: continue
    c = Vector((0, -0.02, v.co.z)); d_ = v.co - c; L = d_.length
    if L < 1e-4: continue
    hit = bvh.ray_cast(c, d_.normalized(), L + 0.03)
    if hit[0] is not None and hit[3] < L + 0.006:
        v.co = c + d_.normalized() * (hit[3] - 0.006); n += 1; pressed.add(v)
print('HEAD pressed in', n)
ring = {v for v in pressed if v.co.y > -0.045}
for _ in range(4): ring |= {e_.other_vert(v) for v in list(ring) for e_ in v.link_edges if e_.other_vert(v).co.y > -0.05}
print('HEAD smoothing', len(ring))
for _ in range(25): bmesh.ops.smooth_vert(bm, verts=list(ring), factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
back = [v for v in bm.verts if v.co.y > 0.035]
bmesh.ops.delete(bm, geom=back, context='VERTS'); bm.to_mesh(o.data); bm.free()
# the small keyhole at the V under the chin: faired
bm = bmesh.new(); bm.from_mesh(parts['robe'].data)
vz = [v for v in bm.verts if (Vector((0, v.co.y, 0.615)) - Vector((0, -0.125, 0.615))).length < 0.05 and abs(v.co.x) < 0.04 and abs(v.co.z - 0.615) < 0.035]
print('ROBE keyhole verts', len(vz))
for _ in range(6): bmesh.ops.smooth_vert(bm, verts=vz, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(parts['robe'].data); bm.free()
for k, x in parts.items():
    print('RAW', k, sum(len(p.vertices) - 2 for p in x.data.polygons))
for o in parts.values():
    for p in o.data.polygons: p.use_smooth = True
BUDGET = dict(head=int(os.environ.get('HEADT', '3800')), robe=99999, belt=380, knots=520, cords=330, shoes=620, shins=99999, hands=99999)
def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
for nm, o in parts.items():
    t0 = tris(o)
    if t0 > BUDGET[nm] * 1.02:
        bpy.context.view_layer.objects.active = o
        for x in bpy.data.objects: x.select_set(x is o)
        m = o.modifiers.new('d', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = BUDGET[nm] / t0; m.use_symmetry = True; m.symmetry_axis = 'X'; m.use_collapse_triangulate = True
        if nm == 'head':
            m.use_symmetry = False
            bm = bmesh.new(); bm.from_mesh(o.data); g = list(bm.verts) + list(bm.edges) + list(bm.faces)
            bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
            bm.to_mesh(o.data); bm.free(); m.ratio = 0.5 * BUDGET[nm] / tris(o)
        bpy.ops.object.modifier_apply(modifier='d')
        if nm == 'head': mirror_mid(o, keep_positive=False)
    print('PART', nm, t0, '->', tris(o))
names = list(parts); Co = []; Tr = []; Pa = []; base = 0
for k, nm in enumerate(names):
    me = parts[nm].data; me.calc_loop_triangles()
    c = np.array([v.co[:] for v in me.vertices]); t = np.array([lt.vertices[:] for lt in me.loop_triangles])
    Co.append(c); Tr.append(t + base); Pa.append(np.full(len(c), k)); base += len(c)
np.savez(OUT, co=np.vstack(Co), tri=np.vstack(Tr), comp=np.concatenate(Pa), names=np.array(names), sh=sh, wr=wr, ax=ax, hj=json.dumps(hj2), hand_scale=S, hand_co=tf(hc), hand_W=Hd['W'], hand_bones=Hd['bones'])
print('SAVED', base, sum(len(t) for t in Tr))
