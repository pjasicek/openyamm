"""Make the raw Meshy body exactly mirror-symmetric before the fit (MM9's PEASANTBOY mesh is symmetric; Meshy built the
character's two arms 10 cm apart in length from the three-quarter master, the far arm drooping, with holes in that
forearm and thigh). The torso is centred on x = 0 (mid-height torso slices), the KEEP half (pos: +X, the image-right
arm of a front view) is kept, mirrored and welded on the midline; a narrow band around x = 0 is relaxed so the seam
leaves no crease, then the result is made exactly symmetric again from the kept half.
Args: <meshy glb> <out glb> [keep pos|neg]"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT = a[0], a[1]
KEEP = a[2] if len(a) > 2 else 'pos'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
parts = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in bpy.context.scene.objects:
    if o.type != 'MESH':
        for c in o.children:
            m = c.matrix_world.copy(); c.parent = None; c.matrix_world = m
for o in list(bpy.context.scene.objects):
    if o.type != 'MESH':
        bpy.data.objects.remove(o)
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
if len(parts) > 1:
    bpy.ops.object.join()
ob = parts[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data
co = np.array([v.co for v in me.vertices])
z0, z1 = co[:, 2].min(), co[:, 2].max()
H = z1 - z0
# torso: slices between 45 % and 70 % of the height, central 0.12 H
xs = []
for f in np.linspace(0.45, 0.70, 11):
    m = np.abs(co[:, 2] - (z0 + f * H)) < 0.01 * H
    m &= np.abs(co[:, 0] - np.median(co[m, 0])) < 0.15 * H
    xs.append(0.5 * (co[m, 0].min() + co[m, 0].max()))
xc = float(np.median(xs))
print('SYM centre x', round(xc, 4), 'slices', np.round(np.array(xs) - xc, 4).tolist())
for v in me.vertices:
    v.co.x -= xc
# mm9_sigmund: the head sits off the torso's midline in the three-quarter master (mirroring it about the torso's plane
# narrowed the face into a V); above HEADF of the height the head is centred on its own nose (front-most point, |x| from
# the face's own bbox) with a smooth ramp over the neck, and the midline relax band is narrow there (the face is ~6 % of
# the height: the 1.2 % body band flattened the nose and mouth)
import os
HEADF = float(os.environ.get('HEADF', '0'))
if HEADF:
    co = np.array([v.co for v in me.vertices])
    zh = z0 + HEADF * H
    m = (co[:, 2] > zh) & (co[:, 2] < z0 + 0.95 * H)
    front = co[m][co[m][:, 1] < np.percentile(co[m][:, 1], 3)]
    xh = float(np.median(front[:, 0]))
    zr = 0.03 * H
    for v in me.vertices:
        t = min(1.0, max(0.0, (v.co.z - (zh - zr)) / zr))
        v.co.x -= xh * t
    print('SYM head centre x', round(xh, 4), 'from', len(front), 'front verts above', round(zh, 3))
bm = bmesh.new(); bm.from_mesh(me)
sgn = 1 if KEEP == 'pos' else -1
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, 0),
                       plane_no=(-sgn, 0, 0), clear_inner=False, clear_outer=True, dist=1e-6)
for v in bm.verts:
    if abs(v.co.x) < 1e-5:
        v.co.x = 0
bf = set(bm.faces)
bmesh.ops.mirror(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), axis='X', merge_dist=1e-5)
bmesh.ops.reverse_faces(bm, faces=[f for f in bm.faces if f not in bf])
bm.normal_update()
# relax a band around the midline (positions only, the midline verts stay at x = 0)
band = 0.012
for it in range(4):
    new = {}
    for v in bm.verts:
        d = abs(v.co.x)
        bnd = band if not HEADF or v.co.z < z0 + (HEADF - 0.03) * H else float(os.environ.get('HEADBAND', '0.0025'))
        if d > bnd or not v.link_edges:
            continue
        w = 0.5 * (1 - d / bnd)
        avg = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)
        p = v.co.lerp(avg, w)
        if d < 1e-6:
            p.x = 0
        new[v] = p
    for v, p in new.items():
        v.co = p
# exact symmetry again: each mirrored vertex takes its kept twin's position
bm.verts.ensure_lookup_table()
from mathutils.kdtree import KDTree
kept = [v for v in bm.verts if sgn * v.co.x > 1e-6]
kd = KDTree(len(kept))
for i, v in enumerate(kept):
    kd.insert(v.co, i)
kd.balance()
worst = 0
for v in bm.verts:
    if sgn * v.co.x < -1e-6:
        p = Vector((-v.co.x, v.co.y, v.co.z))
        q, i, d = kd.find(p)
        worst = max(worst, d)
        v.co = Vector((-q.x, q.y, q.z))
print('SYM worst twin distance', round(worst, 5))
bm.to_mesh(me); bm.free()
# loose parts report
bm = bmesh.new(); bm.from_mesh(me)
print('SYM verts', len(me.vertices), 'faces', len(me.polygons))
bm.free()
me.materials.clear()
for uv in list(me.uv_layers):
    me.uv_layers.remove(uv)
for p in me.polygons:
    p.use_smooth = True   # flat faces export as split vertices (a triangle soup after re-import)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True, export_materials='NONE')
print('SYM written', OUT)
