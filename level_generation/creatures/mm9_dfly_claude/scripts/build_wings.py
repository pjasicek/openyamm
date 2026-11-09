"""Build the four wings: thin closed leaves on the MM9 wing planes, outlined and textured from the HD top view.

Args: <rig blend> <mm9 tier1 glb> <out blend> <report json>

Per MM9 wing piece: root, tip and plane come from the MM9 bind mesh; the outline comes from work/wing_profiles.json
(prep_wings.py): image points are mapped by a 2D similarity (image root/tip -> MM9 root/tip seen from above) and
lifted onto the MM9 wing plane, so the UVs are those image points (textures/dfly_wing_basecolor_src.png crop).
Weights: barycentric blend of the MM9 wing triangle under each vertex (the MM9 wing is rigidly skinned per vertex,
so this reproduces its deformation, membrane stretch included).
"""
import bpy, bmesh, sys, json, math, os
from mathutils import Vector, geometry
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
RIG, MM9, OUT, REP = argv
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prof = json.load(open(os.path.join(HERE, 'work', 'wing_profiles.json')))
NT = 5          # samples across (outline points shared by top and bottom)
THICK = 0.004   # half thickness at the centre line (m, model units)

bpy.ops.wm.open_mainfile(filepath=RIG)
arm = bpy.data.objects['MM9_Rig']
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MM9)
imported = [o for o in bpy.data.objects if o not in before]
cx, ry = prof['centre_x'], prof['root_y']
x0, y0, x1, y1 = prof['crop']


def conv(p):
    return complex(-(p[0] - cx), (p[1] - ry))


rep = {}
bm = bmesh.new()
uvl = bm.loops.layers.uv.new('UVMap')
dl = bm.verts.layers.deform.verify()
groups = {}
for name, w in prof['wings'].items():
    src = next(o for o in imported if o.name.startswith(name))
    mb = bmesh.new()
    mb.from_mesh(src.data)
    mb.transform(src.matrix_world)
    mdl = mb.verts.layers.deform.verify()
    bmesh.ops.remove_doubles(mb, verts=mb.verts, dist=1e-4)
    mb.verts.ensure_lookup_table()
    mb.faces.ensure_lookup_table()
    vg = {i: g.name for i, g in enumerate(src.vertex_groups)}
    label = [vg[max(v[mdl].items(), key=lambda kv: kv[1])[0]] for v in mb.verts]
    R = min(mb.verts, key=lambda v: abs(v.co.x)).co.copy()
    T = max(mb.verts, key=lambda v: (v.co - R).length).co.copy()
    u = (T - R).normalized()
    ring = sorted(mb.verts, key=lambda v: abs((v.co - R).dot(u) - 0.35 * (T - R).length))[:4]
    pair = max(((a, b) for a in ring for b in ring if a != b), key=lambda ab: (ab[0].co - ab[1].co).length)
    wv = pair[1].co - pair[0].co
    wv = (wv - u * wv.dot(u)).normalized()
    n = u.cross(wv).normalized()
    if n.z < 0:
        n = -n
    bvh = BVHTree.FromBMesh(mb)
    qr, qt = conv(w['root']), conv(w['tip'])
    c = (complex(T.x, T.y) - complex(R.x, R.y)) / (qt - qr)

    def lift(img):
        z = complex(R.x, R.y) + (conv(img) - qr) * c
        x, y = z.real, z.imag
        zz = R.z - (n.x * (x - R.x) + n.y * (y - R.y)) / n.z
        return Vector((x, y, zz))

    root = Vector(w['root'])
    axis, perp, L = Vector(w['axis']), Vector(w['perp']), w['length']
    st = w['stations']
    grid_top, grid_bot = [], []
    for k, (f, t0, t1) in enumerate(st):
        row_t, row_b = [], []
        for j in range(NT):
            tf = j / (NT - 1)
            img = root + axis * (f * L) + perp * (t0 + (t1 - t0) * tf)
            p = lift(img)
            uv = ((img.x - x0) / (x1 - x0), 1.0 - (img.y - y0) / (y1 - y0))
            h = THICK * math.sin(math.pi * tf) * min(1.0, 4 * f, 4 * (1 - f))
            if k == 0 or k == len(st) - 1:
                h = 0.0
            row_t.append((p + n * h, uv))
            row_b.append((p - n * h, uv))
        grid_top.append(row_t)
        grid_bot.append(row_b)
    # vertices: ends are single points; outline (j = 0, NT-1) shared between top and bottom
    vt = {}

    def vert(k, j, side):
        last = len(st) - 1
        if k in (0, last):
            key = (k, 0, 't')
        elif j in (0, NT - 1):
            key = (k, j, 't')
        else:
            key = (k, j, side)
        if key not in vt:
            co = (grid_top if key[2] == 't' else grid_bot)[k][j][0]
            vt[key] = bm.verts.new(co)
        return vt[key]

    faces = []
    for side, grid in (('t', grid_top), ('b', grid_bot)):
        for k in range(len(st) - 1):
            for j in range(NT - 1):
                quad = [(k, j), (k + 1, j), (k + 1, j + 1), (k, j + 1)]
                vs = [vert(a, b, side) for a, b in quad]
                uvs = [grid[a][b][1] for a, b in quad]
                if side == 'b':
                    vs, uvs = vs[::-1], uvs[::-1]
                # drop collapsed corners at the single-point ends
                seen, vv, uu = set(), [], []
                for v, uv in zip(vs, uvs):
                    if v not in seen:
                        seen.add(v)
                        vv.append(v)
                        uu.append(uv)
                if len(vv) < 3:
                    continue
                try:
                    face = bm.faces.new(vv)
                except ValueError:
                    continue
                for loop, uv in zip(face.loops, uu):
                    loop[uvl].uv = uv
                face.smooth = True
                faces.append(face)
    # weights from the MM9 triangle under each vertex
    for v in set(vt.values()):
        loc, nrm, fi, dist = bvh.find_nearest(v.co)
        tri = mb.faces[fi].verts
        a, b, cc = (t.co for t in tri[:3])
        bary = geometry.barycentric_transform(loc, a, b, cc, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        wsum = {}
        for t, wt in zip(tri[:3], bary):
            wt = max(0.0, wt)
            wsum[label[t.index]] = wsum.get(label[t.index], 0.0) + wt
        tot = sum(wsum.values())
        for g, wt in wsum.items():
            if wt / tot > 0.01:
                gi = groups.setdefault(g, len(groups))
                v[dl][gi] = wt / tot
    rep[name] = {'root': list(R), 'tip': list(T), 'normal': list(n), 'faces': len(faces), 'length': (T - R).length}
    mb.free()

for o in imported:
    bpy.data.objects.remove(o)
# sharp outline edges (top meets bottom)
for e in bm.edges:
    if len(e.link_faces) == 2:
        f0, f1 = e.link_faces
        if f0.normal.dot(f1.normal) < 0.2:
            e.smooth = False
bmesh.ops.triangulate(bm, faces=bm.faces)
# each wing is a closed leaf: orient every face outward (one side's grid winding is mirrored)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('Dfly_Wings')
bm.to_mesh(me)
ob = bpy.data.objects.new('Dfly_Wings', me)
bpy.context.scene.collection.objects.link(ob)
for g, gi in sorted(groups.items(), key=lambda kv: kv[1]):
    ob.vertex_groups.new(name=g)
ob.parent = arm
ob.matrix_parent_inverse = arm.matrix_world.inverted()
mod = ob.modifiers.new('Armature', 'ARMATURE')
mod.object = arm
mat = bpy.data.materials.new('Dfly_Wing')
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(nd for nd in nt.nodes if nd.type == 'BSDF_PRINCIPLED')
img = bpy.data.images.load(os.path.join(HERE, 'textures', 'dfly_wing_basecolor_src.png'))
tex = nt.nodes.new('ShaderNodeTexImage')
tex.image = img
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.55
bsdf.inputs['Metallic'].default_value = 0.0
me.materials.append(mat)
rep['tris'] = len(me.polygons)
rep['groups'] = list(groups)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('WINGS ' + json.dumps(rep))
