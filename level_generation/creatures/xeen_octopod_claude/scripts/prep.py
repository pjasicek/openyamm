"""Import the Smart Topology return, turn it so the maw leans toward -Y (the worm's front; the maw direction is the
mean of the fang pieces' centroids about the body axis), scale it to HEIGHT, centre x/y on the lowest ring, ground it
(min z 0). Lists the connected pieces (work/pieces_prep.json) and renders clay views (review/prep_*.png).
Saves work/clean_v1.blend (object Worm)."""
import bpy, os, sys, bmesh, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 1.15
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = mesh.data.name = 'Worm'
mesh.data.materials.clear()
for p in mesh.data.polygons:
    p.use_smooth = True


def pieces_of(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    lab = -np.ones(len(bm.verts), int); out = []
    for v in bm.verts:
        if lab[v.index] >= 0: continue
        st = [v]; lab[v.index] = len(out); idx = []
        while st:
            x = st.pop(); idx.append(x.index)
            for e in x.link_edges:
                w = e.other_vert(x)
                if lab[w.index] < 0: lab[w.index] = len(out); st.append(w)
        out.append(np.array(idx))
    bm.free()
    return out


co = np.array([v.co[:] for v in mesh.data.vertices])
P = pieces_of(mesh.data)
big = [p for p in P if len(p) > 300]
small = [p for p in P if len(p) <= 300]
# body axis: the centroids of the big (ring) pieces; the lowest ring sets x/y
rings = sorted(big, key=lambda p: co[p, 2].mean())
low = co[rings[0]]; cx, cy = (low[:, 0].min() + low[:, 0].max()) / 2, (low[:, 1].min() + low[:, 1].max()) / 2
top_ring = co[rings[-1]]
ztop = top_ring[:, 2].max()
# fangs: small pieces whose centroid is inside the top ring's radius and high up
zmin = co[:, 2].min()
fangs = [p for p in small if co[p, 2].mean() > ztop - 0.20 * (ztop - zmin)]
fc = np.mean([co[p].mean(0) for p in fangs], 0)
d = Vector((fc[0] - cx, fc[1] - cy, 0))
ang = math.atan2(d.x, -d.y)          # angle of the maw direction from -Y (positive toward +X)
print('MAW fangs', len(fangs), 'centre', fc.round(3).tolist(), 'axis', round(cx, 3), round(cy, 3), 'turn deg', round(math.degrees(ang), 1))
k = HEIGHT / (co[:, 2].max() - co[:, 2].min())
M = Matrix.Scale(k, 4) @ Matrix.Rotation(ang, 4, 'Z') @ Matrix.Translation((-cx, -cy, -co[:, 2].min()))
mesh.data.transform(M)
co = np.array([v.co[:] for v in mesh.data.vertices])
P = pieces_of(mesh.data)
rep = []
for i, p in enumerate(sorted(P, key=lambda p: (-len(p), co[p, 2].mean()))):
    c = co[p]
    rep.append({'i': i, 'verts': int(len(p)), 'min': c.min(0).round(3).tolist(), 'max': c.max(0).round(3).tolist(),
                'c': c.mean(0).round(3).tolist()})
    if i < 8: print('PIECE', rep[-1])
json.dump(rep, open(os.path.join(HERE, 'work', 'pieces_prep.json'), 'w'))
print('SIZE', (co.max(0) - co.min(0)).round(3).tolist(), 'factor', round(k, 4), 'pieces', len(P))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
H = HEIGHT
for name, (loc, tgt, s) in {'front': ((0, -4, H / 2), (0, 0, H / 2), 1.4), 'side': ((-4, 0, H / 2), (0, 0, H / 2), 1.4),
                            'back': ((0, 4, H / 2), (0, 0, H / 2), 1.4), 'top': ((0, 0, 4), (0, 0, 0), 0.8),
                            'quarter': ((-2.2, -2.6, 2.0), (0, 0, H / 2), 1.5),
                            'maw': ((0, -1.6, 2.4), (0, -0.05, 1.0), 0.6)}.items():
    C.render(loc, tgt, s, os.path.join(HERE, 'review', f'prep_{name}.png'), res=(500, 600), floor=False)
