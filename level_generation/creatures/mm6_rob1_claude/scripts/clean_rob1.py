"""Clean the Meshy Smart Topology mesh of the Patrol Unit. Saves work/clean_v1.blend (object 'Robot').

Meshy made the sphere front/back symmetric, but the native robot is plain at the back. Kept from Meshy: the core
sphere with the belt (component 1), the front eye lens (2) and the sensor head pieces (5, 8, 9, 10). Deleted: the
back eye (7), both rings with their lips (4, 0 upper; 3, 6 lower) and two hidden discs inside the belt (11, 12).
The rings are rebuilt as surfaces of revolution with the section measured from Meshy's rings at the sides
(scripts/ring_section.py: elevation 6.5..30 degrees, 0.400..0.423 m from the sphere centre) and V notches at the
front only (upper ring's top edge dips to 15 degrees, lower ring's bottom edge rises to -13.5, both over +-15 degrees
azimuth), as in the native sprites. Ground (min z = 0), forward -Y (sensor head and eye point -Y).
Face attribute 'part' (int): 0 core, 1 upper ring, 2 lower ring, 3 eye, 4 sensor."""
import bpy, bmesh, os, math
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = mesh.data.name = 'Robot'
label = np.load(os.path.join(HERE, 'work', 'component_labels.npy'))
zmin = min(v.co.z for v in mesh.data.vertices)
for v in mesh.data.vertices:
    v.co.z -= zmin
core = np.array([tuple(v.co) for i, v in enumerate(mesh.data.vertices) if label[i] == 1])
CENTRE = np.array([0.0, 0.0, (core[:, 2].min() + core[:, 2].max()) / 2])
PART = {1: 0, 2: 3, 5: 4, 8: 4, 9: 4, 10: 4}

bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
part_layer = bm.faces.layers.int.new('part')
for f in bm.faces:
    f[part_layer] = PART.get(int(label[f.verts[0].index]), -1)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if int(label[v.index]) not in PART], context='VERTS')

R_IN, R_OUT, BEVEL = 0.400, 0.423, 0.006   # metres; BEVEL rounds the four section corners
SEGMENTS = 120                            # 3 degree steps, so 0 and +-15 degrees fall on vertices
NOTCH_HALF = 15.0


def ring(part, e_far, e_edge, e_apex):
    """One ring. e_far: the plain edge; e_edge: the notched edge (elevations, degrees); the notched edge moves to
    e_apex at the front (azimuth 0 = -Y) along a V of half width NOTCH_HALF."""
    sign = 1.0 if e_edge > e_far else -1.0
    loops = []
    for s in range(SEGMENTS):
        az = 360.0 * s / SEGMENTS
        a = (az + 180.0) % 360.0 - 180.0
        edge = e_edge + (e_apex - e_edge) * max(0.0, 1.0 - abs(a) / NOTCH_HALF)
        lo, hi = sorted((e_far, edge))
        # Section loop (elevation, distance): outer face up, top corner, inner face down, bottom corner.
        b = math.degrees(BEVEL / R_OUT)
        pts = [(lo + b, R_OUT)] + [(lo + b + (hi - lo - 2 * b) * t / 5, R_OUT) for t in range(1, 5)]
        pts += [(hi - b, R_OUT), (hi - b * 0.3, R_OUT - BEVEL * 0.3), (hi, R_OUT - BEVEL), (hi, R_IN + BEVEL * 0.5),
                (hi - b * 0.5, R_IN), (lo + b * 0.5, R_IN), (lo, R_IN + BEVEL * 0.5), (lo, R_OUT - BEVEL),
                (lo + b * 0.3, R_OUT - BEVEL * 0.3)]
        # Direction from the sphere centre: azimuth measured from -Y toward +X.
        ar = math.radians(az)
        h = np.array([math.sin(ar), -math.cos(ar)])
        loop = []
        for el, dist in pts:
            er = math.radians(el)
            p = CENTRE + dist * np.array([h[0] * math.cos(er), h[1] * math.cos(er), math.sin(er)])
            loop.append(bm.verts.new(tuple(p)))
        loops.append(loop)
    n = len(loops[0])
    for s in range(SEGMENTS):
        A, B = loops[s], loops[(s + 1) % SEGMENTS]
        for i in range(n):
            j = (i + 1) % n
            f = bm.faces.new((A[i], A[j], B[j], B[i]) if sign > 0 else (A[i], B[i], B[j], A[j]))
            f[part_layer] = part


ring(1, 6.5, 30.0, 15.0)
ring(2, -6.5, -30.0, -13.5)
bm.normal_update()
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[part_layer] in (1, 2)])
bm.to_mesh(mesh.data); bm.free()
mesh.data.shade_smooth()
mesh.data.update()
# Hard-surface shading: sharp edges above 40 degrees (the ring lips and the sensor box).
try:
    bpy.ops.object.shade_auto_smooth(angle=math.radians(40))
except (AttributeError, RuntimeError, TypeError):
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
counts = {}
for p in mesh.data.polygons:
    k = mesh.data.attributes['part'].data[p.index].value
    counts[k] = counts.get(k, 0) + len(p.vertices) - 2
print('CLEANED tris', sum(counts.values()), 'per part', dict(sorted(counts.items())),
      'centre z', round(float(CENTRE[2]), 4), 'height', round(max(v.co.z for v in mesh.data.vertices), 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
