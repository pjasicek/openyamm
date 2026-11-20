"""Spear and buckler meshes for natm, in prop space, textured by planar projection of the HD prop references
(textures/props/*, prop_textures.py). Writes work/props.blend (objects SpearMesh, BucklerMesh, each with 'UVMap' and an
image material) and prints triangle counts.
Spear prop space: +Y toward the tip, origin at the grip centre (0.70 m from the butt), 1.90 m long (references: 1509 px
= 1.9 m); octagonal shaft r 1.4 cm, leather grip r 1.6 cm, bindings r 1.55 cm, socket narrowing to the blade, leaf blade
with a diamond section (profile = the reference alpha), two-sided feather tassel cut from the reference silhouette.
Buckler prop space: face normal +Z (outward), long axis +Y (along the forearm), origin at the forearm line behind the
straps; oval 0.42 x 0.50 m dome 6.5 cm, rolled rim, two strap loops on the back."""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
P = json.load(open(R('textures', 'props', 'spear_profile.json')))
rows = {int(k): v for k, v in P['rows'].items()}; feath = {int(k): v for k, v in P['feathers'].items()}
PX = 1.9 / (1519 - 10); GRIP_ROW = 1519 - 0.70 / PX
X0, CW, IH, AXC = P['crop_x0'], P['crop_w'], P['img_h'], P['axis_col']
bpy.ops.wm.read_factory_settings(use_empty=True)


def y_of(r):
    return (GRIP_ROW - r) * PX


def uv_px(x, r):
    return ((x - X0) / CW, 1.0 - r / IH)


def material(name, img):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    t = m.node_tree.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(R('textures', 'props', img))
    m.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.7
    return m


def finish(bm, name, mat):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return o


# ------------------------------------------------------------------ spear
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
SIDES = 8


def radius(r):
    if 700 <= r <= 940: return 0.016                       # leather grip wrap
    if 270 <= r <= 360 or 640 <= r <= 690 or 1440 <= r <= 1519: return 0.0155   # bindings
    if r < 262: return 0.0095 + (r - 235) / 27 * 0.0045     # socket
    return 0.014


ring_rows = [235, 248, 262, 270, 315, 360, 440, 520, 600, 640, 690, 700, 760, 820, 880, 940, 1040, 1140, 1240, 1340, 1440, 1480, 1519]
rings = []
for r in ring_rows:
    rad = radius(r); ring = []
    for k in range(SIDES):
        th = 2 * math.pi * k / SIDES
        ring.append((bm.verts.new((rad * math.cos(th), y_of(r), rad * math.sin(th))), th))
    rings.append((r, ring))


def shaft_u(th):
    return uv_px(273 + 32 * abs(th - math.pi) / math.pi, 0)[0]


for (r0, a), (r1, b) in zip(rings[:-1], rings[1:]):
    for k in range(SIDES):
        k2 = (k + 1) % SIDES
        f = bm.faces.new((a[k][0], b[k][0], b[k2][0], a[k2][0]))
        th2 = a[k2][1] if k2 else 2 * math.pi
        for loop, (th, rr) in zip(f.loops, ((a[k][1], r0), (b[k][1], r1), (th2, r1), (th2, r0))):
            loop[uvl].uv = (shaft_u(th), 1.0 - rr / IH)
cap = bm.faces.new([v for v, _ in reversed(rings[-1][1])])                 # butt cap
for loop in cap.loops:
    loop[uvl].uv = (shaft_u(math.pi), 1.0 - 1515 / IH)
# blade: diamond section; ridge thickness 7 mm at the centre line tapering to the tip
brow = [r for r in range(12, 236, 14)] + [235]
prev = None
top = bm.verts.new((0, y_of(10), 0))
for r in brow:
    lo, hi = rows.get(r, [AXC - 2, AXC + 2]); cx = (lo + hi) / 2
    hw = max(0.0015, (hi - lo) / 2 * PX); t = 0.0035 * min(1.0, (r - 10) / 60)
    vl = bm.verts.new((-hw, y_of(r), 0)); vr = bm.verts.new((hw, y_of(r), 0))
    vf = bm.verts.new((0, y_of(r), t)); vb = bm.verts.new((0, y_of(r), -t))
    cur = ((vl, lo), (vf, cx), (vr, hi), (vb, cx))
    if prev is None:
        for (a_, xa), (b_, xb) in zip(cur, cur[1:] + cur[:1]):
            f = bm.faces.new((top, b_, a_))
            for loop, (x, rr) in zip(f.loops, ((AXC, 10), (xb, r), (xa, r))):
                loop[uvl].uv = uv_px(x, rr)
    else:
        for i in range(4):
            j = (i + 1) % 4
            f = bm.faces.new((prev[i][0], prev[j][0], cur[j][0], cur[i][0]))
            for loop, (x, rr) in zip(f.loops, ((prev[i][1], prow), (prev[j][1], prow), (cur[j][1], r), (cur[i][1], r))):
                loop[uvl].uv = uv_px(x, rr)
    prev, prow = cur, r
# feather tassel: two-sided flat strip following the reference silhouette, hanging right of the shaft (+X), from the
# binding at row 300 (a thin cord until the feathers start)
frows = list(range(300, 588, 12)) + [587]
strip = []
for r in frows:
    if r in feath and r >= 358:
        lo, hi = feath[r]
    else:
        c = 306 + (r - 300) * 0.25; lo, hi = c - 1.5, c + 1.5
    strip.append(((lo - AXC) * PX, (hi - AXC) * PX, r, lo, hi))
for side in (1, -1):
    pv = None
    for xa, xb, r, lo, hi in strip:
        z = 0.004 * side
        cur = (bm.verts.new((xa, y_of(r), z)), bm.verts.new((xb, y_of(r), z)), lo, hi, r)
        if pv:
            q = (pv[0], cur[0], cur[1], pv[1]) if side > 0 else (pv[1], cur[1], cur[0], pv[0])
            f = bm.faces.new(q)
            pts = ((pv[2], pv[4]), (cur[2], cur[4]), (cur[3], cur[4]), (pv[3], pv[4]))
            if side < 0: pts = (pts[3], pts[2], pts[1], pts[0])
            for loop, (x, rr) in zip(f.loops, pts):
                loop[uvl].uv = uv_px(x, rr)
        pv = cur
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
spear = finish(bm, 'SpearMesh', material('SpearMat', 'spear.png'))
# ------------------------------------------------------------------ buckler
# atlas textures/props/buckler_atlas.png: left half = the front (green leather dome), right half = the back (wood,
# straps), each the reference oval stretched to its half; (xn, yn) = position in the unit oval
A_, B_, DOME, RIM = 0.21, 0.25, 0.065, 0.012
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
front_uv = lambda xn, yn: (0.25 + 0.235 * xn, 0.5 + 0.47 * yn)
back_uv = lambda xn, yn: (0.75 - 0.235 * xn, 0.5 + 0.47 * yn)


def grid(fn_xyz, fn_uv, nu, nv, flip=False, wrap=True):
    vs = [[bm.verts.new(fn_xyz(i / nu, j / nv)) for j in range(nv + (0 if wrap else 1))] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            j2 = (j + 1) % nv if wrap else j + 1
            q = [vs[i][j], vs[i + 1][j], vs[i + 1][j2], vs[i][j2]]
            uv = [fn_uv(i / nu, j / nv), fn_uv((i + 1) / nu, j / nv), fn_uv((i + 1) / nu, (j + 1) / nv), fn_uv(i / nu, (j + 1) / nv)]
            if flip:
                q.reverse(); uv.reverse()
            f = bm.faces.new(q)
            for loop, t in zip(f.loops, uv):
                loop[uvl].uv = t
    return vs


def oval(s, a):
    th = 2 * math.pi * a; return s * math.cos(th), s * math.sin(th)


S0 = 0.12                                                     # inner ring (closed by a fan)
front = grid(lambda s, a: (A_ * oval(S0 + (1 - S0) * s, a)[0], B_ * oval(S0 + (1 - S0) * s, a)[1], 0.02 + DOME * (1 - (S0 + (1 - S0) * s) ** 2)),
             lambda s, a: front_uv(*oval(S0 + (1 - S0) * s, a)), 5, 24, flip=True)
c = bm.verts.new((0, 0, 0.02 + DOME))
for j in range(24):
    f = bm.faces.new((c, front[0][j], front[0][(j + 1) % 24]))
    for loop, t in zip(f.loops, ((0.25, 0.5), front_uv(*oval(S0, j / 24)), front_uv(*oval(S0, (j + 1) / 24)))):
        loop[uvl].uv = t
rim = grid(lambda s, a: ((A_ + RIM * math.sin(math.pi * s)) * math.cos(2 * math.pi * a), (B_ + RIM * math.sin(math.pi * s)) * math.sin(2 * math.pi * a), 0.02 * (1 - s)),
           lambda s, a: front_uv(*[0.98 * x for x in oval(1.0, a)]), 3, 24, flip=True)
backs = grid(lambda s, a: (A_ * oval(S0 + (1 - S0) * s, a)[0], B_ * oval(S0 + (1 - S0) * s, a)[1], 0.0),
             lambda s, a: back_uv(*oval(S0 + (1 - S0) * s, a)), 3, 24)
cb = bm.verts.new((0, 0, 0.0))
for j in range(24):
    f = bm.faces.new((cb, backs[0][(j + 1) % 24], backs[0][j]))
    for loop, t in zip(f.loops, ((0.75, 0.5), back_uv(*oval(S0, (j + 1) / 24)), back_uv(*oval(S0, j / 24)))):
        loop[uvl].uv = t
for yc in (-0.09, 0.09):                                      # strap loops across the width; the forearm runs along +Y
    for side in (1, -1):                                      # outer and inner face of the strap (thin band)
        off = 0.0 if side > 0 else 0.004
        grid(lambda s, a, yc=yc, off=off: ((s - 0.5) * 0.17, yc + (a - 0.5) * 0.05, -0.003 - off - 0.045 * math.sin(math.pi * s)),
             lambda s, a, yc=yc: back_uv((s - 0.5) * 0.17 / A_, (yc + (a - 0.5) * 0.05) / B_), 6, 1, flip=(side < 0), wrap=False)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
buck = finish(bm, 'BucklerMesh', material('BucklerMat', 'buckler_atlas.png'))
for o in (spear, buck):
    print('PROP', o.name, sum(len(p.vertices) - 2 for p in o.data.polygons), 'tris')
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'props.blend'))
