"""Elf ears for row 73 (PEASANTBOY1E = PEASANTBOY1's body + one 14-vertex piece, Boy_1a: two pointed ears through the
hair). Built procedurally after MM9's piece (base inside the hair at the ear, the tip up, out and slightly back, about
7 cm long, the concave front facing forward and out) as a thin leaf: a dished front, a back offset by a thickness that
tapers to the tip, a rim joining them; the base edge stays open inside the hair.
They are added to 'Body' weighted 100 % to a new joint `Bip01 ElfEars` (child of Bip01 Head, rest at the head joint),
so split_attachment.py can take them out of the body GLB as an attachment that only row 73's descriptor carries.
Faces get `head` = 1 and HeadUV islands in the head set's free band (Blender UV u 0.04..0.76, v 0.82..0.99; the head
square is the lower-left 0.8, the hands the right column), painted by elf_ear_paint.py. UVMap copies HeadUV (the export
copies HeadUV over UVMap for head faces anyway). Args: <in blend> <out blend>"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector, Matrix

IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
me = body.data
JOINT = 'Bip01 ElfEars'
# --- the joint
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
hd = eb['Bip01 Head']
if JOINT not in eb:
    nb = eb.new(JOINT)
    nb.head = hd.head.copy(); nb.tail = hd.tail.copy(); nb.roll = hd.roll
    nb.parent = hd; nb.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
HJ = rig.matrix_world @ rig.data.bones['Bip01 Head'].head_local

# --- geometry (right side x > 0, mirrored for the left)
B = Vector((0.074, 0.020, 0.733))       # base centre, inside the hair (hair surface |x| ~0.086 at this height)
T = Vector((0.127, 0.040, 0.797))       # tip: up, out, slightly back (MM9: base x 0.062, tip x 0.108, rise 5 cm)
D = (T - B); L = D.length; D.normalize()
N0 = Vector((0.80, -0.60, 0.0)).normalized()          # the concave front looks out and forward (MM9: the leaf reads in profile)
N = (N0 - D * N0.dot(D)).normalized()
Wd = D.cross(N).normalized()                          # across the ear (toward the back of the head)
NU, NV = 11, 8
WMAX, DISH = 0.0185, 0.005


def halfw(u):
    return WMAX * (1 - u) ** 0.85 * (0.62 + 0.38 * math.sin(math.pi * min(u / 0.7, 1.0)))


def thick(u):
    return 0.0042 * (1 - u) + 0.0012 * u


def front(u, v, side):
    w = halfw(u)
    dish = DISH * (1 - v * v) * math.sin(math.pi * min(u / 0.9, 1.0)) * (1 - u) ** 0.3
    p = B + D * (L * u) + Wd * (v * w) - N * dish
    # the rim (|v| near 1) curls slightly forward like a helix
    p += N * (0.0018 * max(0.0, abs(v) - 0.7) / 0.3)
    return Vector((p.x * side, p.y, p.z))


bm = bmesh.new()
deform = bm.verts.layers.deform.verify()
uvl_h = bm.loops.layers.uv.new('HeadUV')
uvl_b = bm.loops.layers.uv.new('UVMap')
# islands: per side a front and a back panel, 0.17 x 0.15 of the head set each
ISL = {(1, 'f'): (0.04, 0.83), (1, 'b'): (0.22, 0.83), (-1, 'f'): (0.40, 0.83), (-1, 'b'): (0.58, 0.83)}
SU, SV = 0.16, 0.15
faces_made = []
for side in (1, -1):
    F = [[None] * NV for _ in range(NU)]
    K = [[None] * NV for _ in range(NU)]
    for i in range(NU):
        u = i / (NU - 1) * 0.985
        for j in range(NV):
            v = -1 + 2 * j / (NV - 1)
            pf = front(u, v, side)
            nrm = Vector((N.x * side, N.y, N.z))
            F[i][j] = bm.verts.new(pf)
            K[i][j] = bm.verts.new(pf - nrm * thick(u))
    tip_f = bm.verts.new(front(1.0, 0, side))
    for grid, key, flip in ((F, 'f', side < 0), (K, 'b', side > 0)):
        u0, v0 = ISL[(side, key)]
        def uv(i, j):
            return (u0 + SU * (j / (NV - 1)), v0 + SV * (i / (NU - 1)))
        for i in range(NU - 1):
            for j in range(NV - 1):
                q = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
                ij = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                if flip:
                    q.reverse(); ij.reverse()
                f = bm.faces.new(q)
                for l, (a, b) in zip(f.loops, ij):
                    l[uvl_h].uv = uv(a, b)
                faces_made.append((f, key))
        # tip fan
        for j in range(NV - 1):
            q = [grid[NU - 1][j], tip_f, grid[NU - 1][j + 1]]
            ij = [(NU - 1, j), (NU - 1, (NV - 1) / 2), (NU - 1, j + 1)]
            if not flip:
                q.reverse(); ij.reverse()
            f = bm.faces.new(q)
            for l, (a, b) in zip(f.loops, ij):
                l[uvl_h].uv = (u0 + SU * (b / (NV - 1)), v0 + SV * min(1.0, a / (NU - 1) + 0.04))
            faces_made.append((f, key))
    # rim strips along both long edges (v = -1 and v = +1), on the front island's edge texels
    u0, v0 = ISL[(side, 'f')]
    for j, jn in ((0, 0), (NV - 1, NV - 1)):
        for i in range(NU - 1):
            q = [F[i][j], F[i + 1][j], K[i + 1][j], K[i][j]]
            if (j == 0) == (side > 0):
                q.reverse()
            f = bm.faces.new(q)
            for l in f.loops:
                l[uvl_h].uv = (u0 + SU * (jn / (NV - 1)) + (0.004 if jn == 0 else -0.004), v0 + SV * 0.5)
            faces_made.append((f, 'r'))
bm.normal_update()
# orientation check: front faces should look along +-N (out of the dish), back faces the other way
bmesh.ops.triangulate(bm, faces=bm.faces[:])
for f in bm.faces:
    for l in f.loops:
        l[uvl_b].uv = l[uvl_h].uv
ear = bpy.data.meshes.new('ears')
bm.to_mesh(ear); bm.free()
eo = bpy.data.objects.new('Ears', ear); bpy.context.scene.collection.objects.link(eo)
eo.parent = rig; eo.matrix_parent_inverse = rig.matrix_world.inverted()
eo.matrix_world = body.matrix_world.copy()
vg = eo.vertex_groups.new(name=JOINT)
vg.add(list(range(len(ear.vertices))), 1.0, 'REPLACE')
# attributes as on Body
for a in me.attributes:
    if a.name.startswith('.') or a.name in ear.attributes or a.name in ('position',):
        continue
    if a.domain in ('FACE', 'POINT') and a.data_type in ('INT', 'FLOAT', 'BOOLEAN'):
        try:
            ear.attributes.new(a.name, a.data_type, a.domain)
        except Exception:
            pass
ear.attributes['head'].data.foreach_set('value', [1] * len(ear.polygons))
for a in ear.attributes:
    if a.domain == 'FACE' and a.name not in ('head',) and a.data_type == 'INT':
        a.data.foreach_set('value', [0] * len(ear.polygons))
for p in ear.polygons:
    p.use_smooth = True
for uvn in [l.name for l in me.uv_layers]:
    if uvn not in ear.uv_layers:
        ear.uv_layers.new(name=uvn)
        src = ear.uv_layers['HeadUV'].data
        dst = ear.uv_layers[uvn].data
        for k in range(len(src)):
            dst[k].uv = src[k].uv
nv0 = len(me.vertices)
for o in bpy.data.objects:
    o.select_set(o in (body, eo))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
print('ELFEARS', {'verts': len(me.vertices) - nv0, 'faces_total': len(me.polygons), 'L_m': round(L, 4),
                  'tip': [round(x, 3) for x in T], 'head_joint': [round(x, 3) for x in HJ]})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
