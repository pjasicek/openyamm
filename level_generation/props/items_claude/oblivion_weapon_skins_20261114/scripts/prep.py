"""Step 1 of the Oblivion weapon skins (README.md): one new UV layout per template, shared by all its tier skins.

Usage: blender --background --python prep.py -- <template> [max_aspect] [min_faces]

Reads assets_dev/engine/view_model/<template>.glb (Oblivion's mesh; never changed: positions, triangles, node name and
transform stay, only vertex sharing at the new seams and the UVs change) and writes into work/<template>/:
  layout.blend        the mesh with the new UVs and the template's split normals (locked once an upload went to Meshy)
  uv_report.json      uv_atlas report plus the segmentation cuts
  layout_measure.glb  glTF space, new UVs, grey 2048 placeholder (texture_quality.py, gutter_fill.py and the packer)
  upload.glb          the mesh in the Meshy frame (head up, the flat toward Meshy's front), no material
  guide_{front,back,left,right}.png  plain grey orthographic renders of upload.glb, 1024 x 1536, transparent
  orient.json         the rotation from Blender's import frame to the upload frame

Layout: uv_atlas.unwrap() defaults (PartUV charts, seam pass, sparrow), then islands longer than max_aspect times their
width (the blade faces) are cut into equal pieces and everything is repacked with sparrow (the held-sword pilot's
segment step: one blade face as one island caps a square atlas at 10-50 %).
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
NAME = argv[0]
MAX_ASPECT = float(argv[1]) if len(argv) > 1 else 4.0
MIN_FACES = int(argv[2]) if len(argv) > 2 else 0
SRC = os.path.join(REPO, 'assets_dev', 'engine', 'view_model', f'{NAME}.glb')
OUT = os.path.join(PROJECT, 'work', NAME)
os.makedirs(OUT, exist_ok=True)

# Upload frames (Blender axes after the glTF import: glTF x, y, z -> Blender x, -z, y). Weapons point along glTF +Y
# (Blender +Z, already up) with their flat along glTF Z (Blender -Y: Meshy's front). The shield faces glTF -Y (Blender
# +Z) with its top along glTF -Z (Blender +Y): turned so its face looks at the front camera and its top is up.
ORIENT = {'s_steelshield': [[1, 0, 0], [0, 0, -1], [0, 1, 0]]}



def save_template_uvs(me, name, out):
    """uv_template.npy: the new UV of every template triangle corner (template order, glTF v down)."""
    import glb_io
    doc, binary = glb_io.read(SRC)
    _, prim = glb_io.mesh_primitive(doc, 'Bow' if name == 'w_bow' else None)
    tp = glb_io.accessor(doc, binary, prim['attributes']['POSITION']).astype(np.float64)
    tt = glb_io.accessor(doc, binary, prim['indices']).astype(np.int64).reshape(-1, 3)
    # The mesh was laid out in world space (its node's transform applied); the staff's node turns it about 76 degrees.
    mesh_index = doc['meshes'].index(next(m for m in doc['meshes'] if prim in m['primitives']))
    node = next(n for n in doc['nodes'] if n.get('mesh') == mesh_index)
    qx, qy, qz, qw = node.get('rotation', [0, 0, 0, 1])
    rot = np.array([[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
                    [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
                    [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]])
    tp = (tp * np.array(node.get('scale', [1, 1, 1]))) @ rot.T + np.array(node.get('translation', [0, 0, 0]))
    bpos = np.array([v.co for v in me.vertices])
    gpos = np.stack([bpos[:, 0], bpos[:, 2], -bpos[:, 1]], 1)            # Blender -> glTF
    layer = me.uv_layers['UVMap'].data
    uv = np.zeros((len(tt), 3, 2))
    if name == 'w_bow':
        for f, t in enumerate(tt):
            p = me.polygons[f]
            assert np.allclose(gpos[list(p.vertices)], tp[t], atol=1e-4), f
            for c, l in enumerate(p.loop_indices):
                u, v = layer[l].uv[:]
                uv[f, c] = (u, 1.0 - v)
    else:
        # Faces matched by their corner sets with a tolerance (the import's near-identity node transform moves
        # positions by about 1e-6, so a rounded key misses where a coordinate sits on a rounding boundary).
        bverts = np.array([list(p.vertices) for p in me.polygons])
        bloops = np.array([list(p.loop_indices) for p in me.polygons])
        bcorner = gpos[bverts]                                         # (F, 3, 3)
        bcentre = bcorner.mean(1)
        used = np.zeros(len(bverts), bool)
        for f, t in enumerate(tt):
            corners = tp[t]
            near = np.argsort(np.linalg.norm(bcentre - corners.mean(0), axis=1))[:8]
            # Every corner order of each nearby face; an unused face first (stacked duplicate faces), then the
            # smallest error (a sliver's welded corners coincide, so the corners need not match distinct ones).
            best, best_key, best_map = None, (True, 1e9), None
            for g in near:
                for order in ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)):
                    err = np.linalg.norm(bcorner[g][list(order)] - corners, axis=1).max()
                    key = (bool(used[g]), float(err))
                    if err < 1e-3 and key < best_key:
                        best, best_key, best_map = g, key, np.array(order)
            assert best is not None, (f, 'no face within 1e-3')
            used[best] = True
            for c in range(3):
                u, v = layer[int(bloops[best][best_map[c]])].uv[:]
                uv[f, c] = (u, 1.0 - v)
    np.save(os.path.join(out, 'uv_template.npy'), uv)
    print('PREP template uvs', uv.shape, flush=True)


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
# The bow (w_bow) also carries its arrow: only the bow mesh is laid out (the arrow keeps Oblivion's texture). Its
# string morph is dropped here and carried over by write_skin.py from the template, vertex by vertex.
meshes = [o for o in bpy.data.objects if o.type == 'MESH' and (NAME != 'w_bow' or o.data.name.startswith('Bow'))]
assert len(meshes) == 1, [o.name for o in meshes]
obj = meshes[0]
if obj.data.shape_keys is not None:
    obj.shape_key_clear()
obj.data.transform(obj.matrix_world)
obj.matrix_world = Matrix.Identity(4)
for o in list(bpy.data.objects):
    if o is not obj:
        bpy.data.objects.remove(o)
src_pos = np.array([v.co for v in obj.data.vertices])
src_tris = len(obj.data.polygons)

# Source shading by corner position (restored after the weld and the unwrap).
me = obj.data
key = lambda p: tuple(np.round(p, 4))
src_normals = {}
for p in me.polygons:
    pts = tuple(sorted(key(src_pos[v]) for v in p.vertices))
    src_normals[pts] = {key(src_pos[v]): tuple(me.loops[l].normal) for l, v in zip(p.loop_indices, p.vertices)}

# The template's own triangles in their order (Blender axes): the skin's UVs are written per template corner.
sys.path.insert(0, HERE)
import glb_io
tdoc, tbin = glb_io.read(SRC)
_, tprim = glb_io.mesh_primitive(tdoc, 'Bow' if NAME == 'w_bow' else None)
tpos = glb_io.accessor(tdoc, tbin, tprim['attributes']['POSITION']).astype(np.float64)
ttri = glb_io.accessor(tdoc, tbin, tprim['indices']).astype(np.int64).reshape(-1, 3)
to_blender = lambda a: np.stack([a[:, 0], -a[:, 2], a[:, 1]], 1)
if NAME == 'w_bow':
    # The bow's string stacks faces at one place that its morph pulls apart (16 triangles on 4 position triples): a
    # weld by position alone merges them. Weld by position and morph delta, built straight from the template, so
    # the faces keep the template's order.
    delta = glb_io.accessor(tdoc, tbin, tprim['targets'][0]['POSITION']).astype(np.float64)
    keys = np.round(np.c_[tpos, delta], 5)
    _, first, remap = np.unique(keys, axis=0, return_index=True, return_inverse=True)
    remap = remap.ravel()
    newme = bpy.data.meshes.new('Bow:0')
    newme.from_pydata(to_blender(tpos[first]).tolist(), [], remap[ttri].tolist())
    newme.update()
    obj.data = newme
    me = newme
    print('PREP bow weld', len(tpos), '->', len(first), 'vertices,', len(me.polygons), 'tris', flush=True)
    weld = 0
else:
    bm = bmesh.new(); bm.from_mesh(me)
    n0 = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
    bm.to_mesh(me); bm.free()
    print('PREP weld', n0, '->', len(me.vertices), 'vertices,', len(me.polygons), 'tris (source', src_tris, ')',
          flush=True)
    weld = 1e-5
assert len(me.polygons) == len(ttri), 'the weld collapsed faces'

report = uv_atlas.unwrap(obj, weld=weld)
print('UV_REPORT', json.dumps({k: report[k] for k in report if k in ('atlas', 'charts_used', 'packer_used',
                                                                    'fallbacks', 'islands')}), flush=True)

# Segment long islands and repack.
tri = np.array([p.vertices[:] for p in me.polygons], np.int32)
loops = np.array([p.loop_indices[:] for p in me.polygons], np.int64)
uvl = np.array([d.uv[:] for d in me.uv_layers['UVMap'].data], np.float64)
uv = uvl[loops]
island = uv_atlas._islands(uv, tri)
new_island = island.copy()
next_id = island.max() + 1
cuts = []
for i in np.unique(island):
    faces = np.nonzero(island == i)[0]
    pts = uv[faces].reshape(-1, 2)
    ctr = pts.mean(0)
    w, v = np.linalg.eigh(np.cov((pts - ctr).T))
    axis, side = v[:, 1], v[:, 0]
    along = (pts - ctr) @ axis
    length, width = np.ptp(along), max(np.ptp((pts - ctr) @ side), 1e-9)
    k = int(math.ceil(length / width / MAX_ASPECT))
    if k <= 1 or len(faces) < MIN_FACES:
        continue
    cen = (uv[faces].mean(1) - ctr) @ axis
    edges = np.linspace(along.min(), along.max(), k + 1)
    piece = np.clip(np.searchsorted(edges, cen, side='right') - 1, 0, k - 1)
    for p in range(1, k):
        new_island[faces[piece == p]] = next_id
        next_id += 1
    cuts.append({'island': int(i), 'faces': int(len(faces)), 'aspect': round(float(length / width), 2), 'pieces': k})
print('SEGMENT cuts', json.dumps(cuts), flush=True)
if cuts:
    new_island = np.unique(new_island, return_inverse=True)[1].ravel()
    packed, kk = uv_atlas._sparrow(uv, new_island, 2048, 1.0, 4, 60, 5, 0.66)
    packed = np.asarray(packed, np.float64).reshape(-1, 3, 2)
    layer = me.uv_layers['UVMap']
    for f in range(len(tri)):
        for c in range(3):
            layer.data[int(loops[f, c])].uv = packed[f, c]
    me.update()
    uv = packed
use = float(np.abs(np.cross(np.c_[uv[:, 1] - uv[:, 0], np.zeros(len(uv))],
                            np.c_[uv[:, 2] - uv[:, 0], np.zeros(len(uv))])[:, 2]).sum() / 2)
report['segment'] = {'max_aspect': MAX_ASPECT, 'min_faces': MIN_FACES, 'cuts': cuts,
                     'islands': int(new_island.max() + 1), 'uv_sum': round(use, 4)}
json.dump(report, open(os.path.join(OUT, 'uv_report.json'), 'w'), indent=1, default=str)
print('SEGMENT islands', int(new_island.max() + 1), 'uv sum', round(use, 4), flush=True)

# The template's shading back, corner by corner (matched by position; the weld keeps every position).
pos = np.array([v.co for v in me.vertices])
normals, missing = [], 0
for p in me.polygons:
    found = src_normals.get(tuple(sorted(key(pos[v]) for v in p.vertices)))
    missing += found is None
    for v in p.vertices:
        normals.append(found[key(pos[v])] if found is not None else tuple(p.normal))
me.normals_split_custom_set(normals)
me.update()
print('PREP normals: faces unmatched', missing, 'of', len(me.polygons), flush=True)
save_template_uvs(me, NAME, OUT)

img = bpy.data.images.new(f'{NAME}_placeholder', 2048, 2048)
img.pixels[:] = np.full(2048 * 2048 * 4, 0.5, np.float32)
img.filepath_raw = os.path.join(OUT, 'placeholder.png'); img.file_format = 'PNG'; img.save()
mat = bpy.data.materials.new('placeholder'); mat.use_nodes = True
tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img
mat.node_tree.links.new(tex.outputs['Color'], mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
me.materials.clear(); me.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'layout.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'layout_measure.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False)

R = ORIENT.get(NAME, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
json.dump({'rotation_blender': R}, open(os.path.join(OUT, 'orient.json'), 'w'), indent=1)
me.materials.clear()
me.transform(Matrix(R).to_4x4())
me.update()
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'upload.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_materials='NONE')

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.6, 0.6, 0.6)
scene.render.film_transparent = True
scene.render.resolution_x, scene.render.resolution_y = 1024, 1536
scene.view_settings.view_transform = 'Standard'
co = np.array([v.co for v in me.vertices])
ctr = Vector(((co.max(0) + co.min(0)) / 2).tolist())
ext = np.ptp(co, 0)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
# ortho_scale spans the frame's larger (vertical) side; the width is 2/3 of it.
cam.data.ortho_scale = max(ext[2] / 0.88, max(ext[0], ext[1]) * 1.5 / 0.88)
cam.data.clip_end = 1000
scene.camera = cam
views = {'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0)), 'left': Vector((1, 0, 0)), 'right': Vector((-1, 0, 0))}
for name, d in views.items():
    cam.location = ctr + d * 200
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(OUT, f'guide_{name}.png')
    bpy.ops.render.render(write_still=True)
print('PREP done', NAME, len(me.polygons), 'tris')
