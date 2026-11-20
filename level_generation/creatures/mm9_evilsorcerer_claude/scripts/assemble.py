"""Step 2: raw Meshy parts -> symmetric labelled parts on one figure, Blender frame (faces -Y, z up). Paired parts: the +x part mirrored. Midline parts: bisected, +x half mirrored. Head from the head-only ST:
placed by the eyes, mirrored from its -x (near camera) half about its own midline. Back panels merged and hung straight. Each part reduced to its budget with symmetric collapse.
Args: <body raw npz> <head raw npz> <out npz>. env NOREDUCE=1 keeps the raw density."""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
BODY, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
D = np.load(BODY); co, tri, comp = D['co'], D['tri'], D['comp']
H = np.load(HEAD); hco, htri, hcomp = H['co'], H['tri'], H['comp']
bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection
def make(name, comps, src=(co, tri, comp)):
    c, t, k = src; keep = np.isin(k, comps); idx = -np.ones(len(c), int); idx[keep] = np.arange(keep.sum())
    tt = idx[t[keep[t[:, 0]]]]
    me = bpy.data.meshes.new(name); me.from_pydata(c[keep].tolist(), [], tt.tolist()); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return o
def mirror_mid(o, keep_positive=True, x0=0.0):
    """bisect at x0, keep one half, mirror about x=0 after moving x0 to 0"""
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    for v in bm.verts: v.co.x -= x0
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=not keep_positive, clear_inner=keep_positive, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.mirror(bm, geom=g, axis='X', merge_dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
def pair(name, comp_left, xcheck=True):
    o = make(name, [comp_left]); me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    ret = bmesh.ops.duplicate(bm, geom=g)
    vs = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]; fs = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMFace)]
    for v in vs: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=fs)
    bm.to_mesh(me); bm.free(); return o
parts = {}
# ---- head parts: placed by the eyes
Eh = np.array([hco[hcomp == 4].mean(0), hco[hcomp == 5].mean(0)]); Eb = np.array([co[comp == 27].mean(0), co[comp == 28].mean(0)])
S = np.linalg.norm(Eb[1] - Eb[0]) / np.linalg.norm(Eh[1] - Eh[0]) * float(os.environ.get('HSCALE', '1.0'))
xm = Eh[:, 0].mean()
hq = (hco - [xm, 0, 0]) * S + np.array([0, Eb[:, 1].mean() - Eh[:, 1].mean() * S, Eb[:, 2].mean() - Eh[:, 2].mean() * S])
print('HEAD scale', S, 'mid x', xm, 'z range', hq[:, 2].min(), hq[:, 2].max())
hs = (hq, htri, hcomp)
parts['head'] = make('head', [0], hs)
parts['eyes'] = make('eyes', [4, 5], hs)
parts['crown'] = make('crown', [1, 2, 3, 7], hs)      # ring, spike, plate, boss
for k in ('head', 'crown'): mirror_mid(parts[k], keep_positive=False)
me = parts['eyes'].data; bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x > 0], context='VERTS')
g = list(bm.verts) + list(bm.edges) + list(bm.faces); ret = bmesh.ops.duplicate(bm, geom=g)
for e in ret['geom']:
    if isinstance(e, bmesh.types.BMVert): e.co.x = -e.co.x
bmesh.ops.reverse_faces(bm, faces=[e for e in ret['geom'] if isinstance(e, bmesh.types.BMFace)]); bm.to_mesh(me); bm.free()
# ---- midline
for nm, cs in (('torso', [1]), ('legs', [5]), ('belt', [8]), ('buckle', [9]), ('yokeB', [10]), ('yokeF', [20]), ('panelF', [17]), ('panelB', [18, 19])):
    o = make(nm, cs); parts[nm] = o
    if nm != 'panelB': mirror_mid(o)
for nm, c in (('hands', 3), ('pauldrons', 6), ('shoes', 11), ('boots', 14), ('bracers', 15), ('greaves', 22), ('flapF', 23), ('flapB', 25)):
    parts[nm] = pair(nm, c)
# ---- back yoke: Meshy's reaches the belt; MM9's ends in a low V on the upper back
bm = bmesh.new(); bm.from_mesh(parts['yokeB'].data)
for sx in (1, -1):
    # plane z = zc + a|x|: the part below goes
    n = Vector((-sx * 0.55, 0, 1)).normalized(); pc = Vector((0, 0, 1.30))
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=pc, plane_no=n, clear_inner=True, dist=1e-5)
bm.to_mesh(parts['yokeB'].data); bm.free()
# ---- back panel: one strip hung straight, MM9's width
me = parts['panelB'].data
P = np.array([v.co[:] for v in me.vertices]); z = P[:, 2]
ymid = np.polyval(np.polyfit(z, P[:, 1], 2), z)
ztop = z.max(); u = np.clip((ztop - z) / (ztop - z.min()), 0, 1)
sx = 0.58 + 0.0 * u
P2 = P.copy(); P2[:, 0] = P[:, 0] * sx; P2[:, 1] = float(os.environ.get('BACKY', '0.135')) + (P[:, 1] - ymid) * 0.75
# the two Meshy strips drift apart going down: their inner edges come back to the midline, so the back reads as one panel
bins = np.linspace(z.min(), z.max(), 14); bc = 0.5 * (bins[1:] + bins[:-1]); xp = np.abs(P2[:, 0])
inner = np.array([xp[(z >= a) & (z <= b)].min() if ((z >= a) & (z <= b)).any() else 0 for a, b in zip(bins[:-1], bins[1:])])
P2[:, 0] = np.sign(P2[:, 0]) * np.maximum(xp - np.interp(z, bc, inner) + 0.0015, 0.0015)
for v, p in zip(me.vertices, P2): v.co = Vector(p)
mirror_mid(parts['panelB'])
for o in parts.values():
    for p in o.data.polygons: p.use_smooth = True
BUDGET = dict(head=2300, eyes=120, crown=1200, torso=1300, legs=800, belt=420, buckle=300, yokeB=250, yokeF=250, panelF=320, panelB=320, hands=1200, pauldrons=760, shoes=520, boots=420, bracers=420, greaves=340, flapF=240, flapB=240)
def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
total = 0
for nm, o in parts.items():
    t0 = tris(o)
    if not os.environ.get('NOREDUCE') and t0 > BUDGET[nm] * 1.02:
        bpy.context.view_layer.objects.active = o
        for x in bpy.data.objects: x.select_set(x is o)
        m = o.modifiers.new('d', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = BUDGET[nm] / t0; m.use_symmetry = True; m.symmetry_axis = 'X'; m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='d')
    print('PART', nm, t0, '->', tris(o)); total += tris(o)
print('TOTAL tris', total)
names = list(parts); Co = []; Tr = []; Pa = []; base = 0
for k, nm in enumerate(names):
    o = parts[nm]; me = o.data
    me.calc_loop_triangles()
    c = np.array([v.co[:] for v in me.vertices]); t = np.array([lt.vertices[:] for lt in me.loop_triangles])
    Co.append(c); Tr.append(t + base); Pa.append(np.full(len(c), k)); base += len(c)
np.savez(OUT, co=np.vstack(Co), tri=np.vstack(Tr), comp=np.concatenate(Pa), names=np.array(names))
print('SAVED', base)
