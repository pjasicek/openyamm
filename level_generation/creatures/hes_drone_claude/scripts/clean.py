"""Clean the Meshy Smart Topology return into the drone master mesh. Saves work/clean_v1.blend (object 'HDR').

- Forward -Y (the lens), up +Z, the drone's left +X (Meshy's import already faces -Y).
- Deletes Meshy's looped tendon cables (components TENDON_COMPONENTS of work/raw_labels.npy: two U-loops under the
  belly and two side cables; the HD master's tendons came back as closed loops that cannot hang or sway).
- Scales to LENGTH metres nose to tail, centres x, then collapse-decimates to about TARGET triangles (before any UVs,
  so the retexture paints the reduced mesh).
- Adds three procedural cable tendons (6-sided tubes, rings every SEG, a curved bone claw tip) rooted under the
  belly behind the vent ring, hanging down and slightly back; face attribute 'part' (0 body, 1..3 tendon k, 4 lens dome).
- Replaces Meshy's soft lens face with a clean turned dome (16 sides) and keeps more of the lens assembly.
- Grounds the lowest point (the tendon claw tips) at z 0.
Env: TARGET (default 5000), LENGTH (0.8)."""
import bpy, bmesh, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = int(os.environ.get('TARGET', 5000))
LENGTH = float(os.environ.get('LENGTH', 0.8))
TENDON_COMPONENTS = {26, 52, 17, 34}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/geometry_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = mesh.data.name = 'HDR'
mesh.data.materials.clear()
for uv in list(mesh.data.uv_layers):
    mesh.data.uv_layers.remove(uv)

label = np.load(os.path.join(HERE, 'work', 'raw_labels.npy'))
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
gone = [v for v in bm.verts if label[v.index] in TENDON_COMPONENTS]
bmesh.ops.delete(bm, geom=gone, context='VERTS')
co = np.array([tuple(v.co) for v in bm.verts])
length = co[:, 1].max() - co[:, 1].min()
s = LENGTH / length
centre = Vector(((co[:, 0].max() + co[:, 0].min()) / 2, 0, 0))
for v in bm.verts:
    v.co = (v.co - centre) * s
bm.to_mesh(mesh.data); bm.free()
print('BODY scaled', round(s, 4), 'tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons))

# lens face (component LENS) -> a clean turned dome; the lens assembly (centroid y < FRONT_Y before scaling) keeps
# FRONT_RATIO of its triangles; the rest is cut to reach TARGET in all.
LENS = 38
FRONT_Y = -0.25
lab_raw = np.load(os.path.join(HERE, 'work', 'raw_labels.npy'))
raw = json.load(open(os.path.join(HERE, 'work', 'raw_components.json')))
front_set = {o['k'] for o in raw if o['c'][1] < FRONT_Y and o['k'] != LENS}
lens_box = next(o for o in raw if o['k'] == LENS)
keep = [i for i in range(len(lab_raw)) if lab_raw[i] not in TENDON_COMPONENTS]
lab = lab_raw[keep]                       # labels of the remaining vertices, in order (bmesh delete keeps order)
grp_front = mesh.vertex_groups.new(name='front'); grp_lens = mesh.vertex_groups.new(name='lens')
grp_front.add([i for i, k in enumerate(lab) if k in front_set], 1.0, 'REPLACE')
grp_lens.add([i for i, k in enumerate(lab) if k == LENS], 1.0, 'REPLACE')


def split_group(obj, name):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT')
    obj.vertex_groups.active_index = obj.vertex_groups[name].index; bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    return next(o for o in bpy.context.selected_objects if o is not obj)


lens_old = split_group(mesh, 'lens'); bpy.data.objects.remove(lens_old, do_unlink=True)
front = split_group(mesh, 'front')


def decimate(obj, ratio):
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
    mod.ratio = min(1.0, ratio); mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='dec')


ntri = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
FRONT_RATIO = 0.75
decimate(front, FRONT_RATIO)
decimate(mesh, max(0.1, (TARGET - ntri(front) - 300) / ntri(mesh)))
print('BODY front tris', ntri(front), 'rest tris', ntri(mesh))
# the dome: rim radius and depth from the Meshy lens piece (scaled), 16 sides, an 8-sided inner cap
R = (lens_box['max'][0] - lens_box['min'][0] + lens_box['max'][2] - lens_box['min'][2]) / 4 * s
cx = ((lens_box['max'][0] + lens_box['min'][0]) / 2 - centre.x) * s
cz = (lens_box['max'][2] + lens_box['min'][2]) / 2 * s
y_front, y_back = lens_box['min'][1] * s, lens_box['max'][1] * s
depth = (y_back - y_front) * 0.75
lbm = bmesh.new()
rings = []
for rr, yy in ((R, y_back + 0.012), (R, y_back), (0.86 * R, None), (0.62 * R, None), (0.36 * R, None)):
    if yy is None:
        yy = y_back - depth * math.sqrt(max(0.0, 1 - (rr / R) ** 2))
    rings.append([lbm.verts.new((cx + rr * math.cos(2 * math.pi * j / 16), yy, cz + rr * math.sin(2 * math.pi * j / 16)))
                  for j in range(16)])
for a, b in zip(rings[:-1], rings[1:]):
    for j in range(16):
        lbm.faces.new((a[j], a[(j + 1) % 16], b[(j + 1) % 16], b[j]))
inner = [lbm.verts.new((cx + 0.14 * R * math.cos(2 * math.pi * (j + 0.5) / 8),
                        y_back - depth * 0.99, cz + 0.14 * R * math.sin(2 * math.pi * (j + 0.5) / 8))) for j in range(8)]
o = rings[-1]
for j in range(8):
    lbm.faces.new((o[2 * j], o[2 * j + 1], inner[j]))
    lbm.faces.new((o[2 * j + 1], o[(2 * j + 2) % 16], inner[(j + 1) % 8], inner[j]))
apex = lbm.verts.new((cx, y_back - depth, cz))
for j in range(8):
    lbm.faces.new((inner[j], inner[(j + 1) % 8], apex))
bmesh.ops.recalc_face_normals(lbm, faces=lbm.faces)
bmesh.ops.triangulate(lbm, faces=lbm.faces, quad_method='SHORT_EDGE')
lme = bpy.data.meshes.new('lens'); lbm.to_mesh(lme); lbm.free()
lens = bpy.data.objects.new('lens', lme); bpy.context.scene.collection.objects.link(lens)
# outward check: the dome's normals face -Y
lme.calc_loop_triangles() if hasattr(lme, 'calc_loop_triangles') else None
if np.mean([p.normal.y for p in lme.polygons]) > 0:
    for p in lme.polygons:
        p.flip()
for ob, val in ((mesh, 0), (front, 0), (lens, 4)):
    a = ob.data.attributes.new('part', 'INT', 'FACE'); a.data.foreach_set('value', [val] * len(ob.data.polygons))
bpy.ops.object.select_all(action='DESELECT')
for ob in (mesh, front, lens):
    ob.select_set(True)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.join()
for g in list(mesh.vertex_groups):
    mesh.vertex_groups.remove(g)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)
bpy.ops.mesh.quads_convert_to_tris(quad_method='SHORTEST_DIAGONAL', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
print('BODY decimated tris', ntri(mesh), 'lens R', round(R, 4), 'centre', round(cx, 4), round(cz, 4), 'front y', round(y_front, 4))

# ---------------------------------------------------------------- tendons
bvh = BVHTree.FromObject(mesh, bpy.context.evaluated_depsgraph_get())
co = np.array([tuple(v.co) for v in mesh.data.vertices])
# roots under the belly behind the vent ring (Meshy y 0.12-0.22 scaled), outer pair a little forward
ROOTS = [(0.075, 0.095), (0.0, 0.165), (-0.075, 0.095)]
TENDON_LEN, R0, R1, SIDES, SEG = 0.20, 0.021, 0.014, 6, 0.025
info = []
bm = bmesh.new(); bm.from_mesh(mesh.data)
part = bm.faces.layers.int.get('part')
for k, (x, y) in enumerate(ROOTS, start=1):
    hit = bvh.ray_cast(Vector((x, y, 0.0)), Vector((0, 0, -1)))
    z0 = hit[0].z if hit[0] is not None else co[:, 2].min()
    # centreline: down, drifting back (+Y) and outward a little, the last 25 % curling forward (the hook)
    n = int(round(TENDON_LEN / SEG))
    pts = []
    out = math.copysign(1.0, x) if abs(x) > 1e-6 else 0.0
    for i in range(n + 1):
        t = i / n
        pts.append(Vector((x + out * 0.025 * t, y + 0.07 * math.sin(t * math.pi * 0.5),
                           z0 + 0.015 - TENDON_LEN * t)))
    rings = []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, n)] - pts[max(i - 1, 0)]).normalized()
        q = d.to_track_quat('Z', 'Y')
        r = R0 + (R1 - R0) * (i / n)
        ring = []
        for j in range(SIDES):
            a = 2 * math.pi * (j + 0.5 * (i % 2)) / SIDES
            ring.append(bm.verts.new(p + q @ Vector((math.cos(a) * r, math.sin(a) * r, 0))))
        rings.append(ring)
    for i in range(n):
        for j in range(SIDES):
            a, b = rings[i][j], rings[i][(j + 1) % SIDES]
            c, d = rings[i + 1][(j + 1) % SIDES], rings[i + 1][j]
            for tri in ((a, b, d), (b, c, d)) if i % 2 == 0 else ((a, b, c), (a, c, d)):
                f = bm.faces.new(tri); f[part] = k
    # top cap (buried inside the belly) and the claw: a curved cone continuing the tube, hooking forward (-Y)
    top = bm.verts.new(pts[0] + Vector((0, 0, 0.01)))
    for j in range(SIDES):
        f = bm.faces.new((rings[0][(j + 1) % SIDES], rings[0][j], top)); f[part] = k
    base = pts[-1]; prev = rings[-1]
    claw = [base + Vector((0, -0.012, -0.018)), base + Vector((0, -0.03, -0.028)), base + Vector((0, -0.05, -0.026))]
    for ci, c in enumerate(claw[:-1]):
        r = R1 * (1.05 - 0.45 * (ci + 1))
        d = (claw[ci + 1] - c).normalized(); q = d.to_track_quat('Z', 'Y')
        ring = [bm.verts.new(c + q @ Vector((math.cos(2 * math.pi * j / SIDES) * r, math.sin(2 * math.pi * j / SIDES) * r, 0)))
                for j in range(SIDES)]
        for j in range(SIDES):
            a, b = prev[j], prev[(j + 1) % SIDES]
            cc, dd = ring[(j + 1) % SIDES], ring[j]
            f = bm.faces.new((a, b, dd)); f[part] = k
            f = bm.faces.new((b, cc, dd)); f[part] = k
        prev = ring
    tip = bm.verts.new(claw[-1])
    for j in range(SIDES):
        f = bm.faces.new((prev[j], prev[(j + 1) % SIDES], tip)); f[part] = k
    info.append({'tendon': k, 'root': [x, y, round(z0, 4)], 'points': [list(map(float, p)) for p in pts],
                 'claw': [list(map(float, c)) for c in claw]})
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[part] > 0])
bm.to_mesh(mesh.data); bm.free()
for p in mesh.data.polygons:
    p.use_smooth = True
# ground
zmin = min(v.co.z for v in mesh.data.vertices)
for v in mesh.data.vertices:
    v.co.z -= zmin
for t in info:
    for p in t['points'] + t['claw']:
        p[2] -= zmin
    t['root'][2] -= zmin
co = np.array([tuple(v.co) for v in mesh.data.vertices])
json.dump({'scale': s, 'zmin': zmin, 'tendons': info, 'bbox': [co.min(0).tolist(), co.max(0).tolist()]},
          open(os.path.join(HERE, 'work', 'clean_info.json'), 'w'), indent=1)
print('FINAL tris', sum(len(p.vertices) - 2 for p in mesh.data.polygons), 'bbox', co.min(0).round(3), co.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
print('SAVED clean_v1.blend')
