"""Clean, reduce and complete the Guardian skull. Reads work/clean_v1.blend (+ work/pieces.npy), writes
work/clean_v2.blend with one mesh 'Skull' and a face attribute 'part':
  0 cranium (Meshy piece 0, the forehead dome cut out), 1 mandible (piece 1), 2 upper teeth, 3 lower teeth,
  4 gem bezel (hand-built lathe), 5 gem (hand-built faceted ruby, flat shaded), 6 left eye core, 7 right eye core
  (hand-built low spheres in the sockets; 'left' = the skull's left = +X).
Dropped: piece 2 (a hidden inner duplicate of the cranium shell), piece 36 (a two-triangle sliver), the Meshy eye
spheres (pieces 3/4, 340 triangles each) and the forehead dome (covered by the bezel and gem).
Reduction: collapse decimation per part (cranium 0.45, mandible 0.47, teeth 0.6), triangulated.
Writes work/gem_info.json (gem centre and axis, eye centres)."""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
mesh = bpy.data.objects['Skull']
label = np.load(os.path.join(HERE, 'work', 'pieces.npy'))
co = np.array([tuple(v.co) for v in mesh.data.vertices])

GEM_C = Vector((0.0, -0.334, 0.555))
GEM_N = Vector((0.0, -1.0, 0.29)).normalized()
EYES = {}
for k, side in ((3, 'L'), (4, 'R')):
    c = co[label == k]
    EYES[side] = ((c.min(0) + c.max(0)) / 2).tolist()
print('EYES', EYES)

LOWER_TEETH = [k for k in range(5, 36) if co[label == k][:, 2].max() < 0.18]
UPPER_TEETH = [k for k in range(5, 36) if k not in LOWER_TEETH]
print('TEETH upper', len(UPPER_TEETH), 'lower', len(LOWER_TEETH))
part_of_piece = {0: 0, 1: 1}
part_of_piece.update({k: 2 for k in UPPER_TEETH}); part_of_piece.update({k: 3 for k in LOWER_TEETH})

bm = bmesh.new(); bm.from_mesh(mesh.data)
part_layer = bm.faces.layers.int.new('part')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
drop_v = [v for v in bm.verts if int(label[v.index]) not in part_of_piece]
drop_f = []
for f in bm.faces:
    if int(label[f.verts[0].index]) != 0:
        continue
    inside = True
    for v in f.verts:
        c = v.co - GEM_C
        along = c.dot(GEM_N); radial = (c - GEM_N * along).length
        inside = inside and radial < 0.049 and along > -0.014
    if inside:
        drop_f.append(f)
for f in bm.faces:
    f[part_layer] = part_of_piece.get(int(label[f.verts[0].index]), -1)
bmesh.ops.delete(bm, geom=drop_f, context='FACES_ONLY')
bmesh.ops.delete(bm, geom=drop_v, context='VERTS')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
# small holes in the Meshy cranium (a 5-edge hole on the brow, one under the right socket, the 8-edge gap the sliver
# piece 36 covered): fill them; the dome hole (far more edges) stays open under the bezel
edges = [e for e in bm.edges if e.is_boundary and e.link_faces[0][part_layer] == 0]
res = bmesh.ops.holes_fill(bm, edges=edges, sides=10)
for f in res['faces']:
    f[part_layer] = 0; f.smooth = True
print('HOLES filled', len(res['faces']))
print('DOME faces removed', len(drop_f))
bm.to_mesh(mesh.data); bm.free()

# reduce per part: split, decimate, join
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects: o.select_set(o == mesh)
tris0 = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
RATIO = {0: 0.45, 1: 0.47, 2: 0.6, 3: 0.6}
objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in objs:
    part = o.data.attributes['part'].data[0].value
    bpy.context.view_layer.objects.active = o
    m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = RATIO[part]
    m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='dec')
for o in bpy.data.objects: o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.join()
mesh = bpy.context.view_layer.objects.active; mesh.name = mesh.data.name = 'Skull'


def add_geometry(build, part, smooth):
    """build(bm) fills a fresh bmesh; it is appended to Skull with face attribute part."""
    bm2 = bmesh.new(); build(bm2)
    me2 = bpy.data.meshes.new('tmp'); bm2.to_mesh(me2); bm2.free()
    o2 = bpy.data.objects.new('tmp', me2); bpy.context.scene.collection.objects.link(o2)
    a = me2.attributes.new('part', 'INT', 'FACE'); a.data.foreach_set('value', [part] * len(me2.polygons))
    for p in me2.polygons: p.use_smooth = smooth
    for o in bpy.data.objects: o.select_set(o in (mesh, o2))
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()


frame = GEM_N.to_track_quat('Z', 'Y').to_matrix().to_4x4()
frame.translation = GEM_C


def lathe(bm, profile, segments, mat, cap_top=None):
    """profile: list of (radius, height) along the local +Z axis, outer to inner; quads between rings."""
    rings = []
    for r, h in profile:
        ring = [bm.verts.new(mat @ Vector((r * math.cos(2 * math.pi * i / segments),
                                              r * math.sin(2 * math.pi * i / segments), h)))
                for i in range(segments)]
        rings.append(ring)
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((a[i], a[j], b[j], b[i]))
    return rings


def bezel(bm):
    # outer skirt sunk into the forehead, rounded lip, inner wall down to the gem's girdle seat
    prof = [(0.052, -0.016), (0.052, -0.004), (0.049, 0.007), (0.043, 0.012), (0.037, 0.010), (0.034, 0.003),
            (0.032, -0.010)]
    lathe(bm, prof, 20, frame)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')


def gem(bm):
    # brilliant-style cut: pavilion point, girdle, star ring, table; 12 sides
    n = 12; r = 0.035
    point = bm.verts.new(frame @ Vector((0, 0, -0.012)))
    gird = [bm.verts.new(frame @ Vector((r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), 0.006)))
            for i in range(n)]
    star = [bm.verts.new(frame @ Vector((0.62 * r * math.cos(2 * math.pi * (i + 0.5) / n),
                                         0.62 * r * math.sin(2 * math.pi * (i + 0.5) / n), 0.020))) for i in range(n)]
    table = bm.verts.new(frame @ Vector((0, 0, 0.024)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((point, gird[j], gird[i]))
        bm.faces.new((gird[i], gird[j], star[i]))
        bm.faces.new((star[i], gird[j], star[j]))
        bm.faces.new((star[i], star[j], table))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def eye(centre, radius):
    def build(bm):
        bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=radius,
                                  matrix=Matrix.Translation(Vector(centre)))
    return build


add_geometry(bezel, 4, True)
add_geometry(gem, 5, False)
add_geometry(eye(EYES['L'] if EYES['L'][0] > 0 else EYES['R'], 0.015), 6, True)
add_geometry(eye(EYES['R'] if EYES['L'][0] > 0 else EYES['L'], 0.015), 7, True)
tri = mesh.modifiers.new('tri', 'TRIANGULATE'); tri.quad_method = 'SHORTEST_DIAGONAL'
bpy.ops.object.modifier_apply(modifier='tri')
mesh.data.update()
parts = np.zeros(len(mesh.data.polygons), np.int32); mesh.data.attributes['part'].data.foreach_get('value', parts)
counts = {int(k): int((parts == k).sum()) for k in np.unique(parts)}
print('TRIS', tris0, '->', len(mesh.data.polygons), 'per part', counts)
left = EYES['L'] if EYES['L'][0] > 0 else EYES['R']; right = EYES['R'] if EYES['L'][0] > 0 else EYES['L']
json.dump({'gem_centre': list(GEM_C), 'gem_axis': list(GEM_N), 'gem_top': list(GEM_C + GEM_N * 0.024),
           'eye_left': left, 'eye_right': right, 'eye_radius': 0.015},
          open(os.path.join(HERE, 'work', 'gem_info.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
