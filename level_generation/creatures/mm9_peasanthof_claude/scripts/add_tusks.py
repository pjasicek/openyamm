"""Two small modelled lower tusks (MM9's half-orc women show the lower canines over the upper lip at the mouth corners;
the head retextures painted them flat on the lips for one tier and not at all for the other). Per side a slightly curved
cone (8 sides, 5 rings) from 1.5 mm inside the lower lip at height Z_BASE up past the lip line to Z_TIP, its tip
TIP_OUT in front of the upper lip; x at the face centre +- XOFF (MM9 frame, the face looks along -y). Rigid on Bip01 Head,
face attribute head = 1, HeadUV in the ivory swatch (tusk_swatch.py paints it into every head set) with v along the
tusk (darker root). Args: <in blend> <out blend>   Env: XC (face centre x), XOFF, Z_BASE, Z_TIP, LEN_R (base radius)"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data; rig = ob.parent
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
mw = ob.matrix_world; mwi = mw.inverted()
XC = float(os.environ.get('XC', '-0.006')); XOFF = float(os.environ.get('XOFF', '0.0185'))
ZB = float(os.environ.get('Z_BASE', '0.7265')); ZT = float(os.environ.get('Z_TIP', '0.7425'))
R0 = float(os.environ.get('LEN_R', '0.0024')); OUT = float(os.environ.get('TIP_OUT', '0.0022'))
U0, V0, US, VS = 0.03, 0.90, 0.04, 0.06          # swatch in HeadUV (Blender v up: the image's empty top band)
bm = bmesh.new(); bm.from_mesh(me); bm.transform(mw)
bvh = BVHTree.FromBMesh(bm)
heads = [f for f in bm.faces if False]
lh = bm.faces.layers.int.get('head'); lhand = bm.faces.layers.int.get('hand')
uvl = bm.loops.layers.uv['HeadUV']; uvm = bm.loops.layers.uv.get('UVMap')
dl = bm.verts.layers.deform.verify(); gi = ob.vertex_groups['Bip01 Head'].index
SEG, RINGS = 8, 5
made = 0
for side in (1, -1):
    x = XC + side * XOFF
    hb = bvh.ray_cast(Vector((x, -0.3, ZB)), Vector((0, 1, 0)), 1.0)
    ht = bvh.ray_cast(Vector((x + side * 0.001, -0.3, ZT)), Vector((0, 1, 0)), 1.0)
    if hb[0] is None or ht[0] is None:
        print('TUSK miss', side); continue
    base = hb[0] + Vector((0, 0.0015, 0))                 # 1.5 mm into the lip
    tip = ht[0] + Vector((0, -OUT, 0))                     # in front of the upper lip
    axis = (tip - base); L = axis.length; axis.normalize()
    side_v = Vector((1, 0, 0)); side_v = (side_v - axis * side_v.dot(axis)).normalized(); fwd = axis.cross(side_v)
    rings = []
    for r in range(RINGS):
        t = r / (RINGS - 1)
        c = base + axis * (L * t) + fwd * (-0.0012 * math.sin(math.pi * t))     # gentle curve, belly forward
        rad = R0 * (1 - t) ** 0.8 + 0.0002
        ring = []
        for s in range(SEG):
            ang = 2 * math.pi * s / SEG
            p = c + side_v * (rad * math.cos(ang)) + fwd * (rad * math.sin(ang))
            v = bm.verts.new(p); v[dl][gi] = 1.0; ring.append(v)
        rings.append(ring)
    tipv = bm.verts.new(tip + axis * 0.0008); tipv[dl][gi] = 1.0
    faces = []
    for r in range(RINGS - 1):
        for s in range(SEG):
            q = [rings[r][s], rings[r][(s + 1) % SEG], rings[r + 1][(s + 1) % SEG], rings[r + 1][s]]
            faces.append((bm.faces.new(q), [r, r, r + 1, r + 1], [s, s + 1, s + 1, s]))
    for s in range(SEG):
        faces.append((bm.faces.new([rings[-1][s], rings[-1][(s + 1) % SEG], tipv]), [RINGS - 1, RINGS - 1, RINGS], [s, s + 1, s]))
    for f, rr, ss in faces:
        f.smooth = True
        if lh is not None: f[lh] = 1
        if lhand is not None: f[lhand] = 0
        for lp, r_, s_ in zip(f.loops, rr, ss):
            lp[uvl].uv = (U0 + US * (s_ / SEG), V0 + VS * (r_ / RINGS))
            if uvm is not None: lp[uvm].uv = (0.999, 0.999)
        made += 1
    # outward normals: away from the cone axis
    for f, _, _ in faces:
        f.normal_update()
        c = f.calc_center_median()
        if f.normal.dot(c - (base + axis * axis.dot(c - base))) < 0:
            f.normal_flip()
bm.transform(mwi)
bm.to_mesh(me); me.update()
print('TUSKS faces', made, 'tris', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=a[1])
