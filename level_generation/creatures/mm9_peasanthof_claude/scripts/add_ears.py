"""Procedural pointed half-orc ears (MM9's PeasantHOF1/HOF2 show long pointed ears standing out of the hair, up and back;
the Smart Topology hid them under its rounded hair shell). A cupped leaf with a rim per side (F8's / PeasantGirl1e's
`assemble_pg.py` shape), its root 1.2 cm inside the hair surface at ear height, tip out, up and back through the hair.
Joined into 'Body' as its own loose part, 100 % on Bip01 Head (rigid with the head), face attribute 'ear' = 1.
Args: <in blend> <out blend>   Env: EAR_Z (root height, MM9 frame), EAR_Y, EAR_LEN, EAR_W, EAR_DIR (x,y,z for +x side)"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data; rig = ob.parent
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
mw = ob.matrix_world; mwi = mw.inverted()
dg = bpy.context.evaluated_depsgraph_get()
bm0 = bmesh.new(); bm0.from_mesh(me); bm0.transform(mw)
bvh = BVHTree.FromBMesh(bm0)
EZ = float(os.environ.get('EAR_Z', '0.790')); EY = float(os.environ.get('EAR_Y', '0.020'))
EL = float(os.environ.get('EAR_LEN', '0.085')); EW = float(os.environ.get('EAR_W', '0.038'))
d0 = np.array([float(x) for x in os.environ.get('EAR_DIR', '0.62,0.30,0.72').split(',')])
NU, NV = 12, 7
allV = []; allT = []
hx = []
for sx in (1, -1):
    hit = bvh.ray_cast(Vector((sx * 0.4, EY, EZ)), Vector((-sx, 0, 0)), 1.0)
    hx.append(abs(hit[0].x) if hit[0] else 0.11)
HX = float(os.environ['EAR_X']) if os.environ.get('EAR_X') else max(hx)   # EAR_X: fixed root (HOF2: the ray hits the kerchief)
print('EAR hits', [round(x, 4) for x in hx])
for sx in (1, -1):
    surf = np.array([sx * HX, EY, EZ])
    ER = surf - np.array([sx * 0.012, 0, 0])
    eu = d0 * np.array([sx, 1, 1]); eu = eu / np.linalg.norm(eu)
    en = np.array([sx * 1.0, -0.55, 0.0]); en -= eu * (en @ eu); en /= np.linalg.norm(en)
    ev = np.cross(en, eu); ev /= np.linalg.norm(ev)
    print('EAR', sx, 'surface', np.round(surf, 4).tolist(), 'tip', np.round(ER + eu * EL, 4).tolist())
    V = []; T = []
    uu = np.linspace(0, 1, NU); vv = np.linspace(-1, 1, NV)
    for side, sgn in (('front', 1), ('back', -1)):
        for i, u in enumerate(uu):
            wid = EW * (1 - u) ** 0.85 * (0.75 + 0.6 * u * (1 - u) * 4)
            th_ = 0.0045 * (1 - u) ** 0.7 + 0.0010
            for j, v in enumerate(vv):
                cup = 0.005 * (1 - v * v) * np.sin(np.pi * min(u * 1.1, 1)) if sgn > 0 else 0.0
                rim = 0.0016 * np.exp(-((abs(v) - 1) / 0.3) ** 2) * (1 - u) if sgn > 0 else 0.0
                off = sgn * th_ * np.sqrt(max(1 - v * v, 0.0)) - cup + rim
                V.append(ER + eu * (u * EL) + ev * (v * wid * 0.5) + en * off)
    nf = NU * NV
    for s in (0, 1):
        for i in range(NU - 1):
            for j in range(NV - 1):
                p = s * nf + i * NV + j; b = p + 1; c_ = p + NV; d_ = c_ + 1
                T += [[p, b, d_], [p, d_, c_]] if s == 0 else [[p, d_, b], [p, c_, d_]]
    for i in range(NU - 1):
        for j in (0, NV - 1):
            p, c_ = i * NV + j, (i + 1) * NV + j; b, d_ = nf + p, nf + c_
            T += [[p, c_, d_], [p, d_, b]] if j == 0 else [[p, d_, c_], [p, b, d_]]
    V = np.array(V); V[(NU - 1) * NV:nf] = V[(NU - 1) * NV:nf].mean(0); V[nf + (NU - 1) * NV:] = V[(NU - 1) * NV:nf].mean(0)
    base = sum(len(x) for x in allV)
    allV.append(V); allT += [[t + base for t in tri] for tri in T]
V = np.vstack(allV)
bm = bmesh.new(); bm.from_mesh(me)
ear_layer = bm.faces.layers.int.get('ear') or bm.faces.layers.int.new('ear')
dl = bm.verts.layers.deform.verify()
gi = ob.vertex_groups['Bip01 Head'].index
nv = [bm.verts.new(mwi @ Vector(p.tolist())) for p in V]
new_f = []
for t in allT:
    try:
        f = bm.faces.new([nv[i] for i in t]); f[ear_layer] = 1; f.smooth = True; new_f.append(f)
    except ValueError:
        pass
for v in nv:
    v[dl][gi] = 1.0
bmesh.ops.remove_doubles(bm, verts=nv, dist=1e-5)
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.is_valid and f[ear_layer]])
bm.to_mesh(me); me.update()
print('EARS faces', len(new_f), 'tris', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
