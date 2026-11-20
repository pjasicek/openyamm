"""Replace the tube ponytail with a short three-strand plait, a wrapped tie and a lobed tuft (reference 02_back/03_left).

Works on the rest-pose master (work/final_v3.blend): deletes the old 'Braid' faces, builds new geometry hanging
straight down the back of the neck (clear of the skin), re-places the Braid_1..3 bones along the new path, weights
it (Head at the root, braid chain below), lays out its UVs as vertical strips in free atlas space and joins it.
Scene property 'pfem_braid' records the tie height for texturing.
"""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

mesh = bpy.data.objects['Peasant']; rig = bpy.data.objects['Peasant_Rig']; me = mesh.data
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
BRAID = PARTS.index('Braid')
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)

# ---------------------------------------------------------------- surfaces to hang against
verts = [mesh.matrix_world @ v.co for v in me.vertices]
hair_tree = BVHTree.FromPolygons(verts, [tuple(p.vertices) for p in me.polygons if PARTS[part[p.index]] == 'Hair'])
skin_tree = BVHTree.FromPolygons(verts, [tuple(p.vertices) for p in me.polygons
                                         if PARTS[part[p.index]] in ('Body', 'Hair')])


def back_y(tree, z, x=0.0):
    hit = tree.ray_cast(Vector((x, 0.6, z)), Vector((0, -1, 0)), 1.2)
    return hit[0].y if hit[0] is not None else None


Z_TOP, Z_TIE, Z_TIE_BOTTOM, Z_END = 1.452, 1.334, 1.322, 1.248
R_PLAIT, GAP = 0.024, 0.002
zs = np.linspace(Z_TOP, Z_END, 60)
ys = []
for z in zs:
    s = back_y(skin_tree, z) or 0.06
    r = R_PLAIT if z > Z_TIE else 0.022
    ys.append(s + r + GAP)
ys = np.array(ys)
y_root = (back_y(hair_tree, Z_TOP) or 0.08) - 0.022          # root sinks into the hair mass
ys[0] = y_root
blend = np.clip((Z_TOP - zs) / 0.07, 0, 1)                   # leave the hair mass, then hug the neck
ys = np.maximum(ys, y_root * (1 - blend) + ys * blend)
for i, z in enumerate(zs):                                    # while hair covers the nape, run just under its surface
    hb = back_y(hair_tree, z)
    if hb is not None and z > 1.385:
        ys[i] = min(ys[i], hb - 0.006)
for _ in range(4):
    ys[1:-1] = (ys[:-2] + 2 * ys[1:-1] + ys[2:]) / 4


def path_at(z):
    return Vector((0.0, float(np.interp(-z, -zs, ys)), z))


def frame_at(z):
    a, b = path_at(z + 0.004), path_at(z - 0.004)
    t = (b - a).normalized()
    x = Vector((1, 0, 0)); x = (x - t * x.dot(t)).normalized()
    return t, x, t.cross(x).normalized()          # tangent (down), side, depth (+back)


vs, faces, uvs, groups, strips = [], [], [], [], []


def add_tube(rings, u_scale=1.0):
    """rings: list of lists of Vector (closed). Returns face index range; records strip for UV layout."""
    n = len(rings[0]); base = len(vs)
    for r in rings:
        vs.extend(r)
    f0 = len(faces)
    for i in range(len(rings) - 1):
        for j in range(n):
            a = base + i * n + j; b = base + i * n + (j + 1) % n
            faces.append((a, b, b + n, a + n))
    strips.append((f0, len(faces), len(rings), n, rings))
    return f0, len(faces)


# three-strand plait between the root and the tie
PITCH, SEG = 0.048, 7
for strand in range(3):
    phase = 2 * math.pi * strand / 3
    rings = []
    zz = np.linspace(Z_TOP + 0.004, Z_TIE - 0.004, 30)
    for z in zz:
        u = (Z_TOP - z) / (Z_TOP - Z_TIE)
        t, x, d = frame_at(z)
        spread = 1.15 - 0.25 * u                       # gathered hair is wider at the root
        ramp = min(1.0, (Z_TOP - z) / 0.035); ramp = ramp * ramp * (3 - 2 * ramp)   # emerge from the hair mass
        th = 2 * math.pi * (Z_TOP - z) / PITCH + phase
        centre = path_at(z) + (x * (0.48 * R_PLAIT * spread * math.sin(th)) + d * (0.40 * R_PLAIT * math.sin(2 * th))) * ramp
        rs = 0.0145 * spread * (0.90 + 0.10 * math.cos(2 * th)) * (0.55 + 0.45 * ramp)
        rings.append([centre + (x * math.cos(2 * math.pi * k / SEG) * 1.15 + d * math.sin(2 * math.pi * k / SEG)) * rs
                      for k in range(SEG)])
    add_tube(rings)

# wrapped tie
t, x, d = frame_at((Z_TIE + Z_TIE_BOTTOM) / 2)
tie_rings = []
for z, r in ((Z_TIE + 0.002, 0.0150), (Z_TIE, 0.0168), (Z_TIE_BOTTOM, 0.0168), (Z_TIE_BOTTOM - 0.002, 0.0150)):
    c = path_at(z)
    tie_rings.append([c + (x * math.cos(2 * math.pi * k / 10) + d * math.sin(2 * math.pi * k / 10)) * r for k in range(10)])
add_tube(tie_rings)

# lobed tuft below the tie, rounded end
TSEG, TR = 12, 16
tuft = []
for i in range(TR):
    u = i / (TR - 1)
    z = Z_TIE_BOTTOM + 0.003 - (Z_TIE_BOTTOM + 0.003 - Z_END) * u
    t, x, d = frame_at(z)
    prof = (0.0165 + 0.013 * math.sin(math.pi * min(u / 0.85, 1.0) * 0.75)) * (math.sqrt(max(0.0, 1 - ((u - 0.55) / 0.45) ** 2))
                                                                         if u > 0.55 else 1.0)
    prof = max(prof, 0.004)
    ring = []
    for k in range(TSEG):
        a = 2 * math.pi * k / TSEG
        lobe = 1.0 + 0.16 * math.cos(4 * a + 6.0 * u) + 0.07 * math.cos(9 * a - 4.0 * u)
        ring.append(path_at(z) + (x * math.cos(a) * 1.1 + d * math.sin(a)) * prof * lobe)
    tuft.append(ring)
add_tube(tuft)
end_centre = path_at(Z_END - 0.002)
base = len(vs); vs.append(end_centre); last = base - TSEG
for k in range(TSEG):
    faces.append((last + k, base, last + (k + 1) % TSEG))

# ---------------------------------------------------------------- UVs: vertical strips in free atlas space
uv_layer = me.uv_layers.active.data
R = 512
occ = np.zeros((R, R), bool)
me.calc_loop_triangles()
for t in me.loop_triangles:
    if part[t.polygon_index] == BRAID:
        continue
    p = np.array([tuple(uv_layer[li].uv) for li in t.loops]) * R
    x0, y0 = np.floor(p.min(0)).astype(int) - 1; x1, y1 = np.ceil(p.max(0)).astype(int) + 1
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, R - 1), min(y1, R - 1)
    if x1 < x0 or y1 < y0:
        continue
    gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    a, b, c = p
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-12:
        continue
    w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / d
    w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / d
    inside = (w0 > -0.3) & (w1 > -0.3) & (1 - w0 - w1 > -0.3)
    occ[y0:y1 + 1, x0:x1 + 1] |= inside
TEXEL = 7.0 * 100 / 2048                          # braid colour is procedural; low density is enough
loop_uv = {}
for (f0, f1, nr, n, rings) in strips:
    circ = sum((rings[nr // 2][k] - rings[nr // 2][(k + 1) % n]).length for k in range(n))
    length = sum((sum(rings[i + 1], Vector()) / n - sum(rings[i], Vector()) / n).length for i in range(nr - 1))
    w, h = (circ * TEXEL), (length * TEXEL)
    cw, ch = int(math.ceil(w * R)) + 2, int(math.ceil(h * R)) + 2
    spot = next(((xx, yy) for yy in range(R - ch) for xx in range(R - cw) if not occ[yy:yy + ch, xx:xx + cw].any()), None)
    if spot is None:
        raise RuntimeError('no free atlas space for braid strip')
    occ[spot[1]:spot[1] + ch, spot[0]:spot[0] + cw] = True
    ox, oy = (spot[0] + 1) / R, (spot[1] + 1) / R
    for fi in range(f0, f1):
        i, j = divmod(fi - f0, n)
        for (ri, kj) in ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)):
            loop_uv[(fi, ri, kj)] = (ox + w * kj / n, oy + h * (1 - ri / (nr - 1)))
    strips_uv_end = (ox, oy, w, h)

# ---------------------------------------------------------------- build object
bm = bmesh.new()
bv = [bm.verts.new(v) for v in vs]
bm.verts.ensure_lookup_table()
uvl = bm.loops.layers.uv.new('UVMap')
partl = bm.faces.layers.int.new('part')
strip_of = {}
for si, (f0, f1, nr, n, rings) in enumerate(strips):
    for fi in range(f0, f1):
        strip_of[fi] = (si, f0, n)
for fi, f in enumerate(faces):
    face = bm.faces.new([bv[i] for i in f])
    face[partl] = BRAID
    if fi in strip_of:
        si, f0, n = strip_of[fi]
        i, j = divmod(fi - f0, n)
        for loop, key in zip(face.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
            loop[uvl].uv = loop_uv[(fi, key[0], key[1])]
    else:                                         # tuft end cap: collapse onto the strip's last row
        ox, oy, w, h = strips_uv_end
        for loop in face.loops:
            loop[uvl].uv = (ox + w * 0.5, oy + 0.002)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
new_me = bpy.data.meshes.new('BraidNew'); bm.to_mesh(new_me); bm.free()
for p in new_me.polygons:
    p.use_smooth = True
braid = bpy.data.objects.new('BraidNew', new_me); bpy.context.scene.collection.objects.link(braid)
braid.matrix_world = mesh.matrix_world.copy()

# ---------------------------------------------------------------- bones along the new path
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
inv = rig.matrix_world.inverted()
knots = [Z_TOP - 0.01, Z_TIE, Z_TIE_BOTTOM - 0.035, Z_END]
for k in range(3):
    b = rig.data.edit_bones[f'Braid_{k + 1}']
    b.use_connect = False
    b.head = inv @ path_at(knots[k]); b.tail = inv @ path_at(knots[k + 1])
    b.use_connect = k > 0
bpy.ops.object.mode_set(mode='OBJECT')


def chain_weights(z):
    head_w = min(max((z - (knots[0] - 0.012)) / 0.02, 0.0), 1.0)
    out = {'mixamorig:Head': head_w}
    u = None
    for k in range(3):
        if z >= knots[k + 1] or k == 2:
            u = k + (knots[k] - z) / (knots[k] - knots[k + 1]); break
    for b in range(3):
        w = max(0.0, 1.0 - abs(u - (b + 0.5)))
        if (u < 0.5 and b == 0) or (u > 2.5 and b == 2):
            w = 1.0
        if w > 0:
            out[f'Braid_{b + 1}'] = out.get(f'Braid_{b + 1}', 0.0) + w * (1 - head_w)
    return out


vgs = {}
for v in new_me.vertices:
    ws = {k: w for k, w in chain_weights(v.co.z).items() if w > 0}
    tot = sum(ws.values())
    for name, w in ws.items():
        if name not in vgs:
            vgs[name] = braid.vertex_groups.new(name=name)
        vgs[name].add([v.index], w / tot, 'REPLACE')

# ---------------------------------------------------------------- replace old braid faces and join
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
pl = bm.faces.layers.int.get('part')
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[pl] == BRAID], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free()
old_tris = sum(len(p.vertices) - 2 for p in me.polygons)
for o in bpy.data.objects:
    o.select_set(o in (mesh, braid))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
for p in mesh.data.polygons:
    p.use_smooth = True
tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
bpy.context.scene['pfem_braid'] = json.dumps({'z_top': Z_TOP, 'z_tie': Z_TIE, 'z_tie_bottom': Z_TIE_BOTTOM, 'z_end': Z_END})
print('BRAID new tris', tris - old_tris, 'total', tris)
bpy.ops.wm.save_mainfile()
