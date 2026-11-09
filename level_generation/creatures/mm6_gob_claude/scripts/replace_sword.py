"""Replace the 120-triangle placeholder sword with a Corsair-style scimitar (MM6 goblin / MM7 'Corsair' artifact).

Built in the sword's rest frame stored in scene['pfem_sword'] (grip centre, blade axis, flat normal):
  blade: kilij/shamshir profile curving back toward the spine, edge widening toward the tip, two notches on the
         back near the tip, diamond-bevel cross-section (edge bevel reads as a highlight), clipped point,
  hilt:  hexagonal leather grip, gold crossguard, D-shaped knuckle bow from the edge-side quillon to the pommel,
         scrolled spine-side quillon, red jewels at the guard and pommel.
UVs point into small swatches found in free atlas space (steel gradient strip with a fuller line, gold, leather,
jewel); scripts/paint_sword_swatches.py paints them into the texture sets. Swatch rectangles are stored in
scene['gob_sword_swatches']. Args: [preview_png] renders the sword alone instead of editing the blend.
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
preview = args[0] if args else None
mesh = bpy.data.objects['Peasant']; me = mesh.data; rig = bpy.data.objects['Peasant_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
prop = json.loads(bpy.context.scene['pfem_sword'])
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
SW = PARTS.index('Sword')

# ---------------------------------------------------------------- sword frame from the current geometry
g = Vector(prop['grip']); b_ax = Vector(prop['blade_dir']).normalized()
sword_v = sorted({v for p in me.polygons if part[p.index] == SW for v in p.vertices})
co = [mesh.matrix_world @ me.vertices[i].co for i in sword_v]
tip = max(co, key=lambda x: (x - g).dot(b_ax))
off = (tip - g) - b_ax * (tip - g).dot(b_ax)
e_ax = (-off).normalized()                     # edge side (the blade curves toward its spine, away from the edge)
f_ax = b_ax.cross(e_ax).normalized()


def P(a, e, f):
    return g + b_ax * a + e_ax * e + f_ax * f


# ---------------------------------------------------------------- geometry
verts, faces, cls = [], [], []
CLS = ['steel', 'edge', 'gold', 'leather', 'jewel']


def add(points):
    verts.extend(points); return len(verts) - len(points)


def quad(a, b, c, d, k):
    faces.append((a, b, c, d)); cls.append(k)


def tri(a, b, c, k):
    faces.append((a, b, c)); cls.append(k)


def smooth01(x, a, b):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)


L, ROOT = 0.60, 0.072
ts = [0.0, 0.08, 0.18, 0.28, 0.38, 0.47, 0.54, 0.555, 0.575, 0.595, 0.61, 0.625, 0.645, 0.665, 0.68, 0.73, 0.79,
      0.85, 0.90, 0.95]
NOTCHES = ((0.575, 0.018), (0.645, 0.018))


def profile(t):
    edge = 0.024 + 0.050 * smooth01(t, 0.20, 0.82)
    spine = 0.016
    for c, r in NOTCHES:
        if abs(t - c) < r:
            spine = 0.016 - 0.014 * math.sqrt(max(0.0, 1 - ((t - c) / r) ** 2))
    if t > 0.84:                                # clipped point: the edge sweeps up into a point on the back line
        u = (t - 0.84) / 0.16
        edge *= max(0.0, 1 - u ** 1.35)
        spine *= max(0.0, 1 - u ** 3)
    centre = -0.17 * t ** 1.6
    thick = 0.0042 - 0.0026 * t
    return centre, edge, spine, thick


rings = []
for t in ts:
    c, we, ws, th = profile(t)
    a = ROOT + L * t
    rings.append(add([P(a, c + we, 0), P(a, c + we * 0.40, th), P(a, c - ws, th * 0.75),
                      P(a, c - ws, -th * 0.75), P(a, c + we * 0.40, -th)]))
tip_c, *_ = profile(1.0)
tip_i = add([P(ROOT + L, tip_c - 0.004, 0)])
EDGE_K = {0: 'edge', 1: 'steel', 2: 'steel', 3: 'steel', 4: 'edge'}
for r0, r1 in zip(rings[:-1], rings[1:]):
    for k in range(5):
        quad(r0 + k, r1 + k, r1 + (k + 1) % 5, r0 + (k + 1) % 5, EDGE_K[k])
for k in range(5):
    tri(rings[-1] + k, tip_i, rings[-1] + (k + 1) % 5, EDGE_K[k])
faces.append(tuple(rings[0] + k for k in range(5))[::-1]); cls.append('steel')


def tube(points, radius, k, sides=4, caps=True):
    """Square-ish tube along a polyline (e/a plane), flat normal f for the side vectors."""
    idx = []
    for i, p in enumerate(points):
        d = (points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]).normalized()
        u = f_ax - d * f_ax.dot(d); u.normalize(); v = d.cross(u)
        idx.append(add([p + (u * math.cos(2 * math.pi * s / sides + math.pi / 4) +
                             v * math.sin(2 * math.pi * s / sides + math.pi / 4)) * radius for s in range(sides)]))
    for a0, a1 in zip(idx[:-1], idx[1:]):
        for s in range(sides):
            quad(a0 + s, a1 + s, a1 + (s + 1) % sides, a0 + (s + 1) % sides, k)
    if caps:
        faces.append(tuple(idx[0] + s for s in range(sides))[::-1]); cls.append(k)
        faces.append(tuple(idx[-1] + s for s in range(sides))); cls.append(k)


def box(a0, a1, e0, e1, f0, f1, k):
    i = add([P(a, e, f) for a in (a0, a1) for e in (e0, e1) for f in (f0, f1)])
    for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        quad(*(i + x for x in q), k)


def octa(centre, ra, re, rf, k):
    i = add([centre + b_ax * ra, centre - b_ax * ra, centre + e_ax * re, centre - e_ax * re,
             centre + f_ax * rf, centre - f_ax * rf])
    for a in (0, 1):
        for e in (2, 3):
            for f in (4, 5):
                tri(i + a, i + e, i + f, k) if (a + e + f) % 2 else tri(i + a, i + f, i + e, k)


def gem(centre, r, k):
    """Round-cut jewel: octahedron subdivided once and pushed onto a sphere (32 triangles)."""
    base = [b_ax, -b_ax, e_ax, -e_ax, f_ax, -f_ax]
    tris_ = []
    for a in (0, 1):
        for e in (2, 3):
            for f in (4, 5):
                tris_.append((a, e, f) if (a + e + f) % 2 else (a, f, e))
    for t in tris_:
        p = [base[i] for i in t]
        m = [(p[0] + p[1]).normalized(), (p[1] + p[2]).normalized(), (p[2] + p[0]).normalized()]
        for q in ((p[0], m[0], m[2]), (m[0], p[1], m[1]), (m[2], m[1], p[2]), (m[0], m[1], m[2])):
            i = add([centre + v * r for v in q]); tri(i, i + 1, i + 2, k)


# grip (octagonal leather), round crossguard bar with knob ends, knuckle bow, scroll quillon, jewels, pommel
tube([P(a, 0, 0) for a in (-0.058, -0.02, 0.02, 0.058)], 0.0135, 'leather', sides=8)
tube([P(0.065, e, 0) for e in (-0.040, -0.020, 0.0, 0.020, 0.036)], 0.0075, 'gold', sides=6)
bow = []
for k in range(13):
    s = k / 12
    a = 0.065 - 0.130 * s
    e = 0.036 + 0.026 * math.sin(math.pi * s) - 0.022 * s
    bow.append(P(a, e, 0))
tube(bow, 0.0065, 'gold', sides=6)
scroll = [P(0.065, -0.040, 0), P(0.074, -0.050, 0), P(0.087, -0.054, 0), P(0.098, -0.047, 0), P(0.100, -0.036, 0),
          P(0.093, -0.031, 0)]
tube(scroll, 0.0058, 'gold', sides=6)
gem(P(0.066, 0.004, 0.0), 0.0115, 'jewel')
tube([P(-0.058, 0.0, 0), P(-0.064, 0.004, 0), P(-0.070, 0.008, 0)], 0.0155, 'gold', sides=8)
gem(P(-0.078, 0.010, 0), 0.0105, 'jewel')
print('SWORD tris', sum(len(f) - 2 for f in faces))

# ---------------------------------------------------------------- swatches in free atlas space
def free_rects():
    uv = me.uv_layers.active.data
    S = 1024
    occ = np.zeros((S, S), bool)
    for p in me.polygons:
        if part[p.index] == SW:
            continue
        pts = np.array([tuple(uv[l].uv) for l in p.loop_indices]) * S
        x0, y0 = np.floor(pts.min(0)).astype(int); x1, y1 = np.ceil(pts.max(0)).astype(int)
        occ[max(y0 - 3, 0):min(y1 + 3, S), max(x0 - 3, 0):min(x1 + 3, S)] = True
    return occ, S


occ, S = free_rects()
NEED = {'steel': (36, 8), 'gold': (8, 8), 'leather': (8, 8), 'jewel': (8, 8)}
swatches = {}
for name, (w, h) in NEED.items():
    found = None
    for y in range(4, S - h - 4, 2):
        for x in range(4, S - w - 4, 2):
            if not occ[y:y + h, x:x + w].any():
                found = (x, y); break
        if found:
            break
    x, y = found
    occ[y - 3:y + h + 3, x - 3:x + w + 3] = True
    swatches[name] = [x / S, y / S, (x + w) / S, (y + h) / S]   # u0, v0, u1, v1 in 0..1 (v from the bottom)
print('SWATCHES', json.dumps(swatches))


def uv_for(k, point):
    u0, v0, u1, v1 = swatches['steel' if k in ('steel', 'edge') else k]
    inset_u = (u1 - u0) * 0.2; inset_v = (v1 - v0) * 0.3
    if k in ('steel', 'edge'):
        # steel strip: u runs spine -> edge (fuller line painted at 0.35), edge bevels use the bright end
        e = (point - g).dot(e_ax)
        t = (point - g).dot(b_ax) - ROOT
        c, we, ws, _ = profile(min(1.0, max(0.0, t / L)))
        s = 0.95 if k == 'edge' else min(0.9, max(0.0, (e - (c - ws)) / max(we + ws, 1e-4)))
        return (u0 + inset_u * 0.25 + (u1 - u0 - inset_u * 0.5) * s, (v0 + v1) / 2)
    return ((u0 + u1) / 2, (v0 + v1) / 2)


# ---------------------------------------------------------------- build the object
bm = bmesh.new()
bv = [bm.verts.new(v) for v in verts]
bm.verts.ensure_lookup_table()
uvl = bm.loops.layers.uv.new('UVMap')
partl = bm.faces.layers.int.new('part')
for f, k in zip(faces, cls):
    face = bm.faces.new([bv[i] for i in f])
    face[partl] = SW
    face.smooth = True
    for loop in face.loops:
        loop[uvl].uv = uv_for(k, loop.vert.co)
bm.normal_update()
for e in bm.edges:
    if len(e.link_faces) == 2 and e.link_faces[0].normal.angle(e.link_faces[1].normal) > math.radians(35):
        e.smooth = False
newme = bpy.data.meshes.new('ScimitarMesh'); bm.to_mesh(newme); bm.free()
sword_obj = bpy.data.objects.new('Scimitar', newme)
bpy.context.scene.collection.objects.link(sword_obj)
sword_obj.matrix_world = mesh.matrix_world
newme.transform(mesh.matrix_world.inverted())

if preview:
    import sys as _s
    _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import common
    col = {'steel': (0.72, 0.74, 0.78), 'edge': (0.92, 0.93, 0.95), 'gold': (0.85, 0.62, 0.18), 'leather': (0.32, 0.17, 0.08),
           'jewel': (0.75, 0.05, 0.06)}
    ca = newme.color_attributes.new('c', 'FLOAT_COLOR', 'CORNER')
    for p, k in zip(newme.polygons, cls):
        for li in p.loop_indices:
            ca.data[li].color = (*col[k], 1)
    for o in bpy.data.objects:
        if o.type == 'MESH': o.hide_render = o is not sword_obj
    scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'VERTEX'
    scene.render.resolution_x, scene.render.resolution_y = 700, 300
    centre = mesh.matrix_world @ P(0.30, -0.03, 0)
    for name, d in (('flat', f_ax), ('edge', e_ax)):
        cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = 0.80
        cam = bpy.data.objects.new('c', cd); scene.collection.objects.link(cam)
        up = (mesh.matrix_world.to_3x3() @ (e_ax if name == 'flat' else f_ax)).normalized()
        dv = (mesh.matrix_world.to_3x3() @ d).normalized()
        bw = (mesh.matrix_world.to_3x3() @ b_ax).normalized()
        xa = (bw - dv * bw.dot(dv)).normalized(); ya = dv.cross(xa)
        rot = Matrix((xa, ya, dv)).transposed()
        cam.matrix_world = Matrix.Translation(centre + dv * 1.0) @ rot.to_4x4()
        scene.camera = cam; scene.render.filepath = f'{preview}_{name}.png'
        bpy.ops.render.render(write_still=True)
    sys.exit(0)

# replace the old sword faces in the body mesh with the scimitar
bm = bmesh.new(); bm.from_mesh(me)
pl = bm.faces.layers.int.get('part')
old = [f for f in bm.faces if f[pl] == SW]
old_v = {v for f in old for v in f.verts}
bmesh.ops.delete(bm, geom=old, context='FACES_ONLY')
bmesh.ops.delete(bm, geom=[v for v in old_v if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free()
sg = sword_obj.vertex_groups.new(name='Sword'); sg.add(list(range(len(newme.vertices))), 1.0, 'REPLACE')
sword_obj.data.materials.clear()
for m in me.materials:
    sword_obj.data.materials.append(m)
for o in bpy.data.objects:
    o.select_set(o in (mesh, sword_obj))
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
bpy.context.scene['gob_sword_swatches'] = json.dumps(swatches)
bpy.ops.wm.save_mainfile()
print('REPLACED sword', len(newme.polygons), 'faces')
