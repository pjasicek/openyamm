"""Gate copy (REA_OUT, default work/source.blend; adds a per-vertex int attribute `piece`, 0 = the largest connected
part, for the original project's outliers.py / g6_claws.py). Installed creature source GLB (REA_GLB, default the MM8 Dragon; mesh node REA_NODE) -> work/source.blend with the names the ladder expects (Body, Rig); the ash-remains
mesh is kept hidden (the user will replace that effect). glTF splits vertices at every UV/normal seam, so exact
duplicates are welded (UVs stay per face corner); otherwise every seam is an open edge the decimation cannot cross.
Prints size and clip list."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = int(os.environ.get('REA_FPS', '30'))   # m438 clips were authored and gated at 30 fps
NODE = os.environ.get('REA_NODE', 'Demon_Native_Mesh')
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, os.environ.get('REA_GLB', 'assets_source/worlds/mm6/models/mm6_demon.glb')))
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == NODE)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body.name = 'Body'; rig.name = 'Rig'
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body:
        o.hide_render = True; o.hide_viewport = True
import bmesh
# weld only duplicates with the same weights: a coincident vertex of another armour piece (knight: fauld and
# cuirass) has other weights, and merging it gave the fauld a pelvis-weighted corner that folded in every pose
bm = bmesh.new(); bm.from_mesh(body.data)
open_before = sum(1 for e in bm.edges if e.is_boundary)
dl = bm.verts.layers.deform.active
sig = lambda v: tuple(sorted((g, round(w, 4)) for g, w in v[dl].items())) if dl else ()
classes = {}
for v in bm.verts:
    classes.setdefault(sig(v), []).append(v)
for vs in classes.values():
    bmesh.ops.remove_doubles(bm, verts=vs, dist=1e-6)
bm.verts.ensure_lookup_table()
from mathutils import kdtree
tree = kdtree.KDTree(len(bm.verts))
for v in bm.verts:
    tree.insert(v.co, v.index)
tree.balance()
kept_apart = sum(1 for v in bm.verts if any(j != v.index for _, j, _ in tree.find_range(v.co, 1e-6)))
print('WELD open edges', open_before, '->', sum(1 for e in bm.edges if e.is_boundary), 'verts', len(bm.verts),
      'coincident with other weights', kept_apart)
bm.to_mesh(body.data); bm.free(); body.data.update()
dims = body.dimensions; bpy.context.view_layer.update()
import mathutils
pts = [body.matrix_world @ mathutils.Vector(c) for c in body.bound_box]
print('SIZE', [round(max(p[k] for p in pts) - min(p[k] for p in pts), 3) for k in range(3)])
print('TRIS', sum(len(p.vertices) - 2 for p in body.data.polygons), 'MATS', [m.name for m in body.data.materials])
print('ACTIONS', [(a.name, tuple(a.frame_range)) for a in bpy.data.actions])
print('UV', [u.name for u in body.data.uv_layers], 'ATTR', [a.name for a in body.data.attributes if not a.name.startswith('.')])
import numpy as np
par = list(range(len(body.data.vertices)))
def find(i):
    while par[i] != i:
        par[i] = par[par[i]]; i = par[i]
    return i
for e in body.data.edges:
    a, b = find(e.vertices[0]), find(e.vertices[1])
    if a != b:
        par[a] = b
root = np.array([find(i) for i in range(len(par))]); u, inv, cnt = np.unique(root, return_inverse=True, return_counts=True)
order = np.argsort(-cnt); rank = np.empty_like(order); rank[order] = np.arange(len(order))
att = body.data.attributes.new('piece', 'INT', 'POINT'); att.data.foreach_set('value', rank[inv].astype(np.int32))
print('PIECES', len(u), 'largest', int(cnt.max()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, os.environ.get('REA_OUT', 'work/source.blend')))
