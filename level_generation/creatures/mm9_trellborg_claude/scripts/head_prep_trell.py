"""Head-only Meshy return -> symmetric parts in Meshy's frame: x > 0 half of every piece mirrored. Pieces: Face (skin, hair locks, lip bands), Teeth (the four tusks), Eyes. Args: <meshy glb> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
GLB, OUT = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
Mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = Mw
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x)
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
o.data.materials.clear()
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
seen = set(); comps = []
for v in bm.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cc = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y); cc.append(y)
    comps.append(cc)
def group(cc):
    q = np.array([v.co[:] for v in cc]); c = q.mean(0); e = np.ptp(q, 0)
    if len(cc) < 120 and e.max() < 0.14 and c[1] < -0.3 and c[2] > 0: return 'Eyes'
    if len(cc) < 60 and c[1] < -0.38 and c[2] < 0: return 'Teeth'
    if len(cc) < 1000 and not (c[1] < -0.3 and c[2] < 0): return 'Hair'
    return 'Face'
G = {'Face': [], 'Hair': [], 'Teeth': [], 'Eyes': []}
for cc in comps: G[group(cc)].extend(cc)
print('GROUPS', {k: len(v) for k, v in G.items()})
bm.verts.ensure_lookup_table(); bm.verts.index_update()
for name, vs in G.items():
    keep = {v.index for v in vs}
    t = bm.copy(); t.verts.ensure_lookup_table()
    bmesh.ops.delete(t, geom=[v for v in t.verts if v.index not in keep], context='VERTS')
    g = list(t.verts) + list(t.edges) + list(t.faces)
    bmesh.ops.bisect_plane(t, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=True, dist=1e-5)
    for v in t.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    bmesh.ops.mirror(t, geom=list(t.verts) + list(t.edges) + list(t.faces), axis='X', merge_dist=1e-4)
    bmesh.ops.reverse_faces(t, faces=[f for f in t.faces if f.calc_center_median().x < 0])
    m = bpy.data.meshes.new(name); t.to_mesh(m); t.free()
    ob = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(ob)
    for p in m.polygons: p.use_smooth = True
    print('PART', name, len(m.vertices), len(m.polygons))
bm.free(); bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HEADPREP', OUT)
