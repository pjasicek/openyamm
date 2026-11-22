"""Import the Smart Topology return, scale it to a 1.10 m standing height (antenna knobs included), ground it (min z
0), centre x/y, forward -Y. Labels the connected pieces (0 = most vertices) and saves work/clean_v1.blend (object
Mantis, face attribute 'piece') and work/pieces.npz (co, label). Renders the pieces in colours with their numbers
(review/pieces_<view>.png via work/pieces_labels.json + label_pieces.py)."""
import bpy, os, sys, bmesh, json, random
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 1.10
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([v.co[:] for v in mesh.data.vertices])
mn, mx = co.min(0), co.max(0)
k = HEIGHT / (mx[2] - mn[2])
off = np.array([(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, mn[2]])
for v in mesh.data.vertices:
    v.co = Vector((np.array(v.co[:]) - off) * k)
mesh.name = mesh.data.name = 'Mantis'
for p in mesh.data.polygons:
    p.use_smooth = True
mesh.data.materials.clear()
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
label = np.full(len(bm.verts), -1); pieces = []
for v in bm.verts:
    if label[v.index] >= 0: continue
    st = [v]; label[v.index] = len(pieces); idx = []
    while st:
        x = st.pop(); idx.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0: label[w.index] = label[v.index]; st.append(w)
    pieces.append(idx)
order = sorted(range(len(pieces)), key=lambda i: -len(pieces[i]))
rank = np.zeros(len(pieces), int)
for r, p in enumerate(order): rank[p] = r
lab = rank[label]
co = np.array([v.co[:] for v in mesh.data.vertices])
np.savez(os.path.join(HERE, 'work', 'pieces.npz'), co=co, label=lab)
attr = mesh.data.attributes.new('piece', 'INT', 'FACE')
for p in mesh.data.polygons:
    attr.data[p.index].value = int(lab[p.vertices[0]])
rep = []
for r in range(len(pieces)):
    c = co[lab == r]
    tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons if lab[p.vertices[0]] == r)
    rep.append({'i': r, 'verts': int(len(c)), 'tris': tris, 'c': c.mean(0).round(3).tolist(),
                'min': c.min(0).round(3).tolist(), 'max': c.max(0).round(3).tolist()})
    print(f"PIECE {r} v {len(c)} t {tris} c {c.mean(0).round(3).tolist()} min {c.min(0).round(3).tolist()} max {c.max(0).round(3).tolist()}")
json.dump(rep, open(os.path.join(HERE, 'work', 'pieces_prep.json'), 'w'), indent=0)
print('SIZE', (co.max(0) - co.min(0)).round(3).tolist(), 'factor', round(k, 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
# coloured piece renders with labels
random.seed(3)
mats = []
for r in range(len(pieces)):
    m = bpy.data.materials.new(f'p{r}'); m.diffuse_color = (random.random(), random.random(), random.random(), 1)
    mesh.data.materials.append(m)
for p in mesh.data.polygons:
    p.material_index = int(lab[p.vertices[0]])
labels = {}
sc = bpy.context.scene
for view, (loc, tgt, s) in {'front': ((0, -4, 0.55), (0, 0, 0.55), 1.4), 'side': ((-4, 0, 0.55), (0, 0, 0.55), 1.4),
                            'top': ((0, 0, 4), (0, 0, 0), 1.4), 'back': ((0, 4, 0.55), (0, 0, 0.55), 1.4),
                            'headfront': ((0, -4, 0.85), (0, 0, 0.85), 0.55)}.items():
    path = os.path.join(HERE, 'review', f'pieces_{view}.png')
    C.render(loc, tgt, s, path, res=(1000, 1000), floor=False, color='MATERIAL')
    cd = bpy.data.cameras.new('c2'); cd.type = 'ORTHO'; cd.ortho_scale = s
    cam = bpy.data.objects.new('c2', cd); sc.collection.objects.link(cam); cam.matrix_world = C.look(loc, tgt)
    bpy.context.view_layer.update()
    lst = []
    for r in range(len(pieces)):
        c = co[lab == r]
        # label at the piece vertex nearest the camera among those near the centroid's projection
        pv = world_to_camera_view(sc, cam, Vector(c.mean(0)))
        lst.append([r, pv.x, 1 - pv.y, pv.z])
    labels[path] = lst
    bpy.data.objects.remove(cam, do_unlink=True)
json.dump(labels, open(os.path.join(HERE, 'work', 'pieces_labels.json'), 'w'))
