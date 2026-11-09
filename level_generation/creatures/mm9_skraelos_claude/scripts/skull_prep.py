"""Skull-only Smart Topology (step1_clean.py npz, 0.22 m tall, faces -Y) -> the head part: cranium and jaw mirrored from +x, the teeth kept
(each tooth a piece), Meshy's eyeball spheres shrunk and set back into the sockets as small embers, reduced (cranium/jaw and teeth
separately). Writes co, tri, label (0 cranium, 1 jaw, 2 teeth, 3 eyes), eye_c (between the eye centres), width (cranium x extent).
Args: <skull npz> <out npz>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]
D = np.load(A[0]); co, tri, comp = D['co'], D['tri'], D['comp']
E = lambda k, d: float(os.environ.get(k, d))
bpy.ops.wm.read_factory_settings(use_empty=True); coll = bpy.context.scene.collection


def mesh(name, c, t):
    u, inv = np.unique(t.ravel(), return_inverse=True)
    me = bpy.data.meshes.new(name); me.from_pydata(c[u].tolist(), [], inv.reshape(-1, 3).tolist()); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free(); return o


def arrays(o):
    me = o.data; me.calc_loop_triangles()
    return np.array([v.co[:] for v in me.vertices]), np.array([lt.vertices[:] for lt in me.loop_triangles])


def mirror_mid(o):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=bm.faces); bm.verts.ensure_lookup_table()
    c = np.array([v.co[:] for v in bm.verts]); t = np.array([[v.index for v in f.verts] for f in bm.faces]); bm.free()
    c[np.abs(c[:, 0]) < 1e-4, 0] = 0; n = len(c); mid = np.abs(c[:, 0]) < 1e-9
    idx = np.arange(n) + n; idx[mid] = np.where(mid)[0]
    c2 = np.vstack([c, c * [-1, 1, 1]]); t2 = np.vstack([t, idx[t][:, ::-1]]); used, inv = np.unique(t2.ravel(), return_inverse=True)
    me.clear_geometry(); me.from_pydata(c2[used].tolist(), [], inv.reshape(-1, 3).tolist()); me.update()


def decimate(o, target, sym=True):
    t0 = len(arrays(o)[1])
    if t0 <= target: return
    for x in bpy.data.objects: x.select_set(x is o)
    bpy.context.view_layer.objects.active = o
    md = o.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = target / t0; md.use_collapse_triangulate = True
    if sym: md.use_symmetry = True; md.symmetry_axis = 'X'
    bpy.ops.object.modifier_apply(modifier='d'); print('REDUCE', o.name, t0, '->', len(arrays(o)[1]))


sizes = np.bincount(comp)
cran = mesh('cranium', co, tri[comp[tri[:, 0]] == 0]); mirror_mid(cran)
jaw = mesh('jaw', co, tri[comp[tri[:, 0]] == 1]); mirror_mid(jaw)
eyes = [k for k in (2, 3)]
teeth_ids = [k for k in range(4, comp.max() + 1)]
teeth = mesh('teeth', co, tri[np.isin(comp[tri[:, 0]], teeth_ids)])
decimate(cran, int(E('B_CRAN', '1700'))); decimate(jaw, int(E('B_JAW', '500'))); decimate(teeth, int(E('B_TEETH', '700')), sym=False)
# eyes: Meshy's spheres -> small embers set back in the sockets
ec = []; eo = []
for k in eyes:
    q = co[comp == k]; c = q.mean(0); r = float(np.linalg.norm(q - c, axis=1).mean()); ec.append(c)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=7, radius=r * E('EYE_K', '0.55'))
    for v in bm.verts: v.co = v.co + Vector(c + np.array([0, r * E('EYE_BACK', '0.45'), 0]))
    bmesh.ops.triangulate(bm, faces=bm.faces); me = bpy.data.meshes.new('eye'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('eye', me); coll.objects.link(o); eo.append(o)
    print('EYE', k, c.round(4), 'r', round(r, 4))
ec = np.array(ec); eye_c = ec.mean(0); eye_c[0] = 0
Co = []; Tr = []; La = []; base = 0
for lab, objs in ((0, [cran]), (1, [jaw]), (2, [teeth]), (3, eo)):
    for o in objs:
        c, t = arrays(o); Co.append(c); Tr.append(t + base); La.append(np.full(len(c), lab)); base += len(c)
co2 = np.vstack(Co); width = float(np.ptp(co2[np.concatenate(La) == 0][:, 0]))
np.savez(A[1], co=co2, tri=np.vstack(Tr), label=np.concatenate(La), eye_c=eye_c, width=width)
print('SKULL tris', sum(len(t) for t in Tr), 'width', round(width, 4), 'eye_c', eye_c.round(4))
