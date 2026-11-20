"""The trident: geometry from the HD master's silhouette (references_hd/05_trident.png), textured by planar projection of
the same image. Shaft, collar and butt are 8-sided lathes of the alpha's half-width, the three blades diamond sections per
image column. Writes object Trident into the blend, rigid on Yweaponbase, which moves to the solved grip; Yweapon (the
RangeAttack socket) moves with it to the tip. Args: <in blend> <out blend> <grip json> <lift>"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
IN, OUT, GRIP, LIFT = sys.argv[sys.argv.index('--') + 1:]
LIFT = float(LIFT)
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
grip = json.load(open(GRIP))
g2b = lambda p: Vector((p[0], -p[2], p[1]))
C = g2b(grip['shaft_point']) - Vector((0, 0, LIFT))
D = g2b(grip['shaft_dir']).normalized()
# rest of the bones: move the weapon joints
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o is rig)
Mi = rig.matrix_world.inverted()
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones['Yweaponbase']; ew = rig.data.edit_bones['Yweapon']
delta = (Mi @ C) - eb.head
eb.head += delta; eb.tail += delta; ew.head += delta; ew.tail += delta
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
img = bpy.data.images.load(sys.path[0] + '/../references_hd/05_trident.png' if False else bpy.path.abspath('//../references_hd/05_trident.png'))
W_, H_ = img.size
px = np.array(img.pixels[:], np.float32).reshape(H_, W_, 4)[::-1]
al = px[..., 3] > 0.5
PX = 1.294 / (1503 - 34)
XG = 1002          # grip column
Yc = 502.5
V0 = Vector((0, 0, -1))
V = (V0 - D * V0.dot(D)).normalized()
Wd = D.cross(V).normalized()


def pos(x, y, w):
    """image column x, image row y, thickness offset w (metres)"""
    return C + D * ((XG - x) * PX) + V * ((y - Yc) * PX) + Wd * w


def uv(x, y):
    # atlas textures/imp_props_basecolor.png: master rows 370..646 at 4/3 in the top rows of 2048 x 1024
    return (x / W_, 1 - (y - 370) * (4 / 3) / 1024)


def runs(x):
    r = np.nonzero(al[:, int(x)])[0]
    out = []
    if not len(r):
        return out
    s = p = r[0]
    for v in r[1:]:
        if v != p + 1:
            out.append((int(s), int(p))); s = v
        p = v
    out.append((int(s), int(p)))
    return out


bm = bmesh.new()
uvl = bm.loops.layers.uv.new('UVMap')


def face(vs, uvs):
    f = bm.faces.new(vs)
    for l, u in zip(f.loops, uvs):
        l[uvl].uv = u


def lathe(cols, n=8):
    rings = []
    for x in cols:
        rr = [r for r in runs(x) if r[0] < Yc + 3 and r[1] > Yc - 3]
        hw = max(0.5, (rr[0][1] - rr[0][0] + 1) / 2) if rr else 0.5
        cy = (rr[0][0] + rr[0][1]) / 2 if rr else Yc
        ring = []
        for k in range(n):
            a = 2 * math.pi * (k + 0.5) / n
            ring.append((bm.verts.new(pos(x, cy + hw * math.cos(a), hw * PX * math.sin(a))), x, cy + 0.9 * hw * math.cos(a)))
        rings.append(ring)
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(n):
            a, b = r0[k], r0[(k + 1) % n]; c, d = r1[(k + 1) % n], r1[k]
            face([a[0], b[0], c[0]], [uv(a[1], a[2]), uv(b[1], b[2]), uv(c[1], c[2])])
            face([a[0], c[0], d[0]], [uv(a[1], a[2]), uv(c[1], c[2]), uv(d[1], d[2])])
    for ring, rev in ((rings[0], True), (rings[-1], False)):
        vs = list(reversed(ring)) if rev else ring
        for k in range(1, n - 1):
            q = [vs[0], vs[k], vs[k + 1]]
            face([v[0] for v in q], [uv(v[1], v[2]) for v in q])


def blade(sections, thick):
    """sections: [(x, y0, y1)]; diamond cross-section"""
    rows = []
    for k, (x, y0, y1) in enumerate(sections):
        ym = (y0 + y1) / 2
        t = thick * min(1.0, (y1 - y0) / 30)
        rows.append([(bm.verts.new(pos(x, y0, 0)), x, y0), (bm.verts.new(pos(x, ym, t)), x, ym), (bm.verts.new(pos(x, y1, 0)), x, y1), (bm.verts.new(pos(x, ym, -t)), x, ym)])
    for r0, r1 in zip(rows[:-1], rows[1:]):
        for k in range(4):
            a, b = r0[k], r0[(k + 1) % 4]; c, d = r1[(k + 1) % 4], r1[k]
            face([a[0], b[0], c[0]], [uv(a[1], a[2]), uv(b[1], b[2]), uv(c[1], c[2])])
            face([a[0], c[0], d[0]], [uv(a[1], a[2]), uv(c[1], c[2]), uv(d[1], d[2])])
    for row, rev in ((rows[0], False), (rows[-1], True)):
        vs = list(reversed(row)) if rev else row
        for k in (1, 2):
            q = [vs[0], vs[k], vs[k + 1]]
            face([v[0] for v in q], [uv(v[1], v[2]) for v in q])


# shaft, collar, butt (x from the collar to the red tip)
lathe([352, 356, 372, 392, 396, 1398, 1404, 1425, 1441, 1460, 1480, 1502], 8)
# blades
tips = {}
cols = [36, 90, 150, 215, 262, 278, 296, 316, 332, 348]
centre = []
upper = []
lower = []
for x in cols:
    rs = runs(x)
    if len(rs) == 3:
        upper.append((x, rs[0][0], rs[0][1])); centre.append((x, rs[1][0], rs[1][1])); lower.append((x, rs[2][0], rs[2][1]))
    elif len(rs) == 1:
        centre.append((x, rs[0][0], rs[0][1]))
# the blade roots run on to the collar
print('TRIDENT runs', len(upper), upper[-1], centre[-1], lower[-1])
blade([(34, 502, 504)] + centre, 0.008)
ux, u0, u1 = upper[-1]; lx, l0, l1 = lower[-1]
root_u = (352, 462, 486); root_l = (352, 519, 543)
blade([(34, 376, 378)] + upper + [root_u], 0.005)
blade([(34, 636, 638)] + lower + [root_l], 0.005)
me = bpy.data.meshes.new('Trident'); bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new('Trident', me); bpy.context.scene.collection.objects.link(ob)
for p in me.polygons:
    p.use_smooth = True
ob.parent = rig; ob.matrix_parent_inverse = rig.matrix_world.inverted()
g = ob.vertex_groups.new(name='Yweaponbase'); g.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
m = ob.modifiers.new('Armature', 'ARMATURE'); m.object = rig
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('TRIDENT', len(me.polygons), 'tris', 'tip', tuple(round(x, 3) for x in pos(34, 503, 0)))
