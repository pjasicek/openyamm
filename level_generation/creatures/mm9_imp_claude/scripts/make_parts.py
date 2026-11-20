"""Tier parts: B's shin wraps (MM9's IMP2 skin paints them on; here rigid sleeves on helper bones under the calves) and C's
tongue (painted on the chin in IMP3; here a rigid strip on a helper bone under the head). They become per-descriptor
attachments, so only that tier draws them. Args: <in blend> <out blend>"""
import bpy, bmesh, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
bpy.context.view_layer.update()
M = body.matrix_world
bm0 = bmesh.new(); bm0.from_mesh(body.data); bm0.transform(M)
bmesh.ops.triangulate(bm0, faces=bm0.faces)
bvh = BVHTree.FromBMesh(bm0)
V0, V1, U0, U1 = 0.0, 656 / 1024, 0.0, 0.5           # wrap swatch in the atlas
head = lambda n: rig.matrix_world @ rig.data.bones[n].head_local
parts = []


def new_obj(name, bm, bone):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    ob.parent = rig; ob.matrix_parent_inverse = rig.matrix_world.inverted()
    g = ob.vertex_groups.new(name=bone); g.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
    m = ob.modifiers.new('Armature', 'ARMATURE'); m.object = rig
    parts.append(ob)
    print('PARTS', name, len(me.polygons))


def wrap(S):
    a, b = head(f'Bip01 {S} Calf'), head(f'Bip01 {S} Foot')
    ax = (b - a).normalized()
    u = ax.cross(Vector((1, 0, 0))).normalized(); w = ax.cross(u).normalized()
    N = 14
    ts = [0.40, 0.42, 0.52, 0.62, 0.72, 0.82, 0.84]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for k, t in enumerate(ts):
        c = a + (b - a) * t
        ring = []
        for j in range(N):
            th = 2 * math.pi * j / N
            d = u * math.cos(th) + w * math.sin(th)
            loc = None
            hit, nrm, fi, dist = bvh.ray_cast(c + d * 0.2, -d, 0.2)
            r = (hit - c).length if hit is not None else 0.04
            off = 0.0045 if 0 < k < len(ts) - 1 else -0.002
            ring.append(bm.verts.new(c + d * (r + off)))
        rings.append(ring)
    vs = [V1 - (V1 - V0) * (t - ts[0]) / (ts[-1] - ts[0]) for t in ts]
    for k in range(len(ts) - 1):
        for j in range(N):
            jn = (j + 1) % N
            f = bm.faces.new([rings[k][j], rings[k + 1][j], rings[k + 1][jn], rings[k][jn]])
            uu = [j / N, j / N, (j + 1) / N, (j + 1) / N]
            vv = [vs[k], vs[k + 1], vs[k + 1], vs[k]]
            for l, x, y in zip(f.loops, uu, vv):
                l[uvl].uv = (U0 + (U1 - U0) * x, y)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY')
    new_obj(f'Wrap{S}', bm, f'Xwrap {S}')


def tongue():
    path = [Vector(p) for p in ((0, -0.30, 0.286), (0, -0.328, 0.286), (0, -0.347, 0.277), (0, -0.351, 0.259), (0, -0.345, 0.241), (0, -0.334, 0.228))]
    wid = [0.012, 0.0135, 0.014, 0.012, 0.0075, 0.001]
    thick = 0.003
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rows = []
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        n = t.cross(Vector((1, 0, 0))).normalized()
        if n.y > 0:
            n = -n
        w = wid[i]; x = Vector((1, 0, 0))
        rows.append([bm.verts.new(p - x * w), bm.verts.new(p + n * thick), bm.verts.new(p + x * w), bm.verts.new(p - n * thick)])
    U = [0.0, 0.5, 1.0, 0.5]
    for i in range(len(rows) - 1):
        for j in range(4):
            jn = (j + 1) % 4
            f = bm.faces.new([rows[i][j], rows[i + 1][j], rows[i + 1][jn], rows[i][jn]])
            uu = [U[j], U[j], U[jn], U[jn]]
            vv = [i / 5, (i + 1) / 5, (i + 1) / 5, i / 5]
            for l, a, b in zip(f.loops, uu, vv):
                l[uvl].uv = (0.5 + 0.25 * a, 656 / 1024 * (1 - b))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY')
    new_obj('Tongue', bm, 'Xtongue')


# helper bones first
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
for name, parent in (('Xwrap L', 'Bip01 L Calf'), ('Xwrap R', 'Bip01 R Calf'), ('Xtongue', 'Bip01 Head')):
    p = rig.data.edit_bones[parent]
    e = rig.data.edit_bones.new(name); e.head = p.head.copy(); e.tail = p.tail.copy(); e.roll = p.roll; e.parent = p
bpy.ops.object.mode_set(mode='OBJECT')
wrap('L'); wrap('R'); tongue()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('DONE parts')
