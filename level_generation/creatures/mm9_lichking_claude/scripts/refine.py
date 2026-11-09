"""(Lich King) Edge rings where the rig bends: the reduction left flat panels and limbs with few rows. Panels: a row every 8.5 cm. Knees and elbows: four rings across the limb. Args: <in npz> <rig json> <out npz>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
IN, RIG, OUT = sys.argv[sys.argv.index('--') + 1:]
D = np.load(IN); co, tri, comp = D['co'], D['tri'], D['comp']; names = [str(x) for x in D['names']]
J = json.load(open(RIG))['joints']
bpy.ops.wm.read_factory_settings(use_empty=True)
Co = []; Tr = []; Pa = []; base = 0
for k, nm in enumerate(names):
    v = np.where(comp == k)[0]; rem = -np.ones(len(co), int); rem[v] = np.arange(len(v))
    t = rem[tri[comp[tri[:, 0]] == k]]
    if nm == 'skull':                       # untouched: its vertex order carries the Lich's UVs
        Co.append(co[v]); Tr.append(t + base); Pa.append(np.full(len(v), k)); base += len(v); print('PART skull kept', len(t)); continue
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in co[v].tolist()]
    for f in t.tolist():
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bm.normal_update()
    def cut(pt, n, side=0):
        g = list(bm.verts) + list(bm.edges) + list(bm.faces)
        if side:
            fs = [f for f in bm.faces if f.calc_center_median().x * side > 0.02]
            g = list({v for f in fs for v in f.verts}) + list({e for f in fs for e in f.edges}) + fs
        bmesh.ops.bisect_plane(bm, geom=g, plane_co=pt, plane_no=n, dist=1e-4)
    if nm == 'tabard':
        for z in np.arange(0.40, 0.92, 0.08): cut((0, 0, float(z)), (0, 0, 1))
    def limb(a, b, c, ds, part_side=True):
        for s in (1, -1):
            A, B_, C = [np.array(J[f'Bip01 R {x}']) * [s, 1, 1] for x in (a, b, c)]
            u = (C - A) / np.linalg.norm(C - A)
            for d in ds: cut(Vector(B_ + u * d), Vector(u), s)
    if nm in ('boots', 'pants'):
        limb('Thigh', 'Calf', 'Foot', (-0.06, -0.025, 0.025, 0.06))
    if nm == 'uarms':
        limb('UpperArm', 'Forearm', 'Hand', (-0.05, -0.02))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=2e-4)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.verts.ensure_lookup_table(); bm.verts.index_update()
    c_ = np.array([v.co[:] for v in bm.verts]); t_ = np.array([[v.index for v in f.verts] for f in bm.faces])
    print('PART', nm, len(t), '->', len(t_))
    Co.append(c_); Tr.append(t_ + base); Pa.append(np.full(len(c_), k)); base += len(c_); bm.free()
np.savez(OUT, co=np.vstack(Co), tri=np.vstack(Tr), comp=np.concatenate(Pa), names=np.array(names))
print('SAVED', base, sum(len(t) for t in Tr))
