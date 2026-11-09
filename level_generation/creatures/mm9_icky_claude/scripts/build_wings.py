"""Build the two wings and their wrist claws from work/wing_mesh2d.json (prep_wings.py) on the MM9 wing surface.

Args: <fit blend (MM9_Rig + MM9 meshes + Body)> <out blend> <report json>

Per side: the image is mapped onto the MM9 wing seen from above by a 2D similarity (image root -> the middle of the
MM9 wing's inner edge, image tip -> the MM9 wing tip). Each vertex takes z, and its skin weights, from the MM9 wing
triangle under it (nearest in the top projection, barycentric; the MM9 wing is rigidly skinned per vertex, so this
reproduces its flap, membrane stretch included). The leaf is closed: top and bottom offset by +-THICK * h along the
triangle normal, sharing the outline (h = 0). UVs are the image points (textures/icky_wing_basecolor_src.png crop).
Claws: six-sided cones from the claw base to its tip, raised CLAW_RISE of their length, UVs projected from the top
view, rigid with the wing weights at their base. One object 'Wings' (material Icky_Wing), parented to MM9_Rig.
"""
import bpy, bmesh, sys, json, math, os
from mathutils import Vector, geometry, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
FIT, OUT, REP = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prof = json.load(open(os.path.join(HERE, 'work', 'wing_mesh2d.json')))
THICK = 0.0025
CLAW_RISE = 0.25
CLAW_SEG = 6

bpy.ops.wm.open_mainfile(filepath=FIT)
arm = bpy.data.objects['MM9_Rig']
cx = prof['centre_x']
x0, y0, x1, y1 = prof['crop']


def conv(p):
    """image px -> complex with model orientation (image right = -X, image down = +Y)"""
    return complex(-(p[0] - cx), p[1])


def uv_of(p):
    return ((p[0] - x0) / (x1 - x0), 1.0 - (p[1] - y0) / (y1 - y0))


rep = {}
bm = bmesh.new()
uvl = bm.loops.layers.uv.new('UVMap')
dl = bm.verts.layers.deform.verify()
groups = {}
for side, mm9_name in (('right', 'wing.mesh'), ('left', 'wing01.mesh')):
    w = prof['wings'][side]
    src = bpy.data.objects[mm9_name]
    mb = bmesh.new()
    mb.from_mesh(src.data)
    mb.transform(src.matrix_world)
    mdl = mb.verts.layers.deform.verify()
    mb.verts.ensure_lookup_table()
    vg = {i: g.name for i, g in enumerate(src.vertex_groups)}
    label = [vg[max(v[mdl].items(), key=lambda kv: kv[1])[0]] for v in mb.verts]
    inner = [v.co for v in mb.verts if abs(v.co.x) < 0.03]
    R = sum(inner, Vector()) / len(inner)
    T = max(mb.verts, key=lambda v: abs(v.co.x)).co.copy()
    # flattened copy for the top-projection lookup
    flat = bmesh.new()
    for v in mb.verts:
        flat.verts.new((v.co.x, v.co.y, 0.0))
    flat.verts.ensure_lookup_table()
    mb.faces.ensure_lookup_table()
    flat_src = []  # flat face index -> MM9 face index (double-sided duplicates are skipped)
    for f in mb.faces:
        try:
            flat.faces.new([flat.verts[v.index] for v in f.verts])
            flat_src.append(f.index)
        except ValueError:
            pass
    flat.faces.ensure_lookup_table()
    mb.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(flat)
    qr, qt = conv(w['root']), conv(w['tip'])
    c = (complex(T.x, T.y) - complex(R.x, R.y)) / (qt - qr)

    def xy(img):
        z = complex(R.x, R.y) + (conv(img) - qr) * c
        return z.real, z.imag

    def surface(x, y):
        """z, unit normal and {bone: weight} of the MM9 wing mid-surface at the top-view point (x, y): the MM9 wing
        is a two-layer slab, so every MM9 triangle under the point (both layers) is averaged"""
        q = Vector((x, y, 0.0))
        loc0, _, fi0, d0 = bvh.find_nearest(q)
        hits = bvh.find_nearest_range(q, d0 + 1e-5) or [(loc0, None, fi0, d0)]
        zs, ns, wsum = [], [], {}
        for loc, _, fi, dist in hits:
            if dist > d0 + 1e-5:
                continue
            src_f = mb.faces[flat_src[fi]]
            tri = src_f.verts
            fa = flat.faces[fi].verts
            a, b, cc = (t.co for t in fa[:3])
            bary = geometry.barycentric_transform(loc, a, b, cc, Vector((1, 0, 0)), Vector((0, 1, 0)),
                                                  Vector((0, 0, 1)))
            bw = [max(0.0, x_) for x_ in bary]
            s_ = sum(bw) or 1.0
            bw = [x_ / s_ for x_ in bw]
            zs.append(sum(bw[k] * tri[k].co.z for k in range(3)))
            n = src_f.normal.copy()
            ns.append(n if n.z >= 0 else -n)
            for t, wt in zip(tri[:3], bw):
                wsum[label[t.index]] = wsum.get(label[t.index], 0.0) + wt
        n = sum(ns, Vector()).normalized()
        return sum(zs) / len(zs), n, wsum

    def set_w(v, wsum):
        tot = sum(wsum.values())
        for g, wt in wsum.items():
            if wt / tot > 0.01:
                gi = groups.setdefault(g, len(groups))
                v[dl][gi] = wt / tot

    P = w['verts']; h = w['h']
    top, bot = [], []
    for k, img in enumerate(P):
        x, y = xy(img)
        zz, n, wsum = surface(x, y)
        p = Vector((x, y, zz))
        vt = bm.verts.new(p + n * THICK * h[k])
        set_w(vt, wsum)
        top.append(vt)
        if h[k] <= 0.0:
            bot.append(vt)
        else:
            vb = bm.verts.new(p - n * THICK * h[k])
            set_w(vb, wsum)
            bot.append(vb)
    nf = 0
    for t in w['tris']:
        a2, b2, c2 = [P[i] for i in t]
        # image triangles: orient the top face up (+Z) in model space
        pa, pb, pc = (Vector((*xy(q), 0)) for q in (a2, b2, c2))
        up = (pb - pa).cross(pc - pa).z > 0
        order = list(t) if up else [t[0], t[2], t[1]]
        for layer, flip in ((top, False), (bot, True)):
            ids = order[::-1] if flip else order
            vs = [layer[i] for i in ids]
            if len(set(vs)) < 3:
                continue
            try:
                f = bm.faces.new(vs)
            except ValueError:
                continue
            for loop, i in zip(f.loops, ids):
                loop[uvl].uv = uv_of(P[i])
            f.smooth = True
            nf += 1
    # claw cone
    cw = w['claw']
    claw_tris = 0
    if cw:
        bx, by = xy(cw['base']); tx, ty = xy(cw['tip'])
        zb, nb, wb = surface(bx, by)
        base = Vector((bx, by, zb))
        L = (Vector((tx, ty, 0)) - Vector((bx, by, 0))).length
        tipv = Vector((tx, ty, zb + CLAW_RISE * L))
        ax = (tipv - base).normalized()
        base = base - ax * 0.15 * L  # root sunk into the leading edge
        rad = cw['half_width'] * abs(c) * 1.15
        ref = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
        e1 = ax.cross(ref).normalized(); e2 = ax.cross(e1)
        ring = []
        for k in range(CLAW_SEG):
            a_ = 2 * math.pi * k / CLAW_SEG
            q = base + (e1 * math.cos(a_) + e2 * math.sin(a_)) * rad
            v = bm.verts.new(q); set_w(v, wb); ring.append(v)
        apex = bm.verts.new(tipv); set_w(apex, wb)
        cap = bm.verts.new(base - ax * 0.002); set_w(cap, wb)

        def img_of(q):
            z = (complex(q.x, q.y) - complex(R.x, R.y)) / c + qr
            return (-z.real + cx, z.imag)
        for k in range(CLAW_SEG):
            a_, b_ = ring[k], ring[(k + 1) % CLAW_SEG]
            for vs in ((a_, b_, apex), (b_, a_, cap)):
                f = bm.faces.new(vs)
                # outward: the side faces' normal must point away from the axis
                mid = sum((v.co for v in vs), Vector()) / 3
                f.normal_update()
                if vs[2] is apex and f.normal.dot(mid - (base + ax * (mid - base).dot(ax))) < 0:
                    f.normal_flip()
                if vs[2] is cap and f.normal.dot(-ax) < 0:
                    f.normal_flip()
                for loop in f.loops:
                    loop[uvl].uv = uv_of(img_of(loop.vert.co))
                f.smooth = True
                claw_tris += 1
    rep[side] = {'root_mm9': list(R), 'tip_mm9': list(T), 'scale_m_per_px': abs(c), 'faces': nf,
                 'claw_tris': claw_tris}
    mb.free(); flat.free()

for e in bm.edges:
    if len(e.link_faces) == 2:
        f0, f1 = e.link_faces
        if f0.normal.dot(f1.normal) < 0.2:
            e.smooth = False
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
me = bpy.data.meshes.new('Wings')
bm.to_mesh(me)
ob = bpy.data.objects.new('Wings', me)
bpy.context.scene.collection.objects.link(ob)
for g, gi in sorted(groups.items(), key=lambda kv: kv[1]):
    ob.vertex_groups.new(name=g)
ob.parent = arm
ob.matrix_parent_inverse = arm.matrix_world.inverted()
mod = ob.modifiers.new('Armature', 'ARMATURE')
mod.object = arm
mat = bpy.data.materials.new('Icky_Wing')
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(nd for nd in nt.nodes if nd.type == 'BSDF_PRINCIPLED')
img = bpy.data.images.load(os.path.join(HERE, 'textures', 'icky_wing_basecolor_src.png'))
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = img
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.6
bsdf.inputs['Metallic'].default_value = 0.0
me.materials.append(mat)
bnd = sum(1 for e in bm.edges if e.is_boundary)
rep.update({'tris': len(me.polygons), 'groups': list(groups), 'boundary_edges': bnd})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('WINGS ' + json.dumps(rep))
