"""Head-only Meshy model -> objects Face (face, beard, neck), Helm (shell), Horns (side horns with their collars, top spike), Eyes, at head scale S, head-local, exactly symmetric (figure's right half mirrored).
S = 0.41 fits MM9's head box: helmet half width 0.114, horn span 0.19-0.205, height 0.385-0.40, depth 0.30. Args: <head glb> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
S = float(os.environ.get('HEAD_S', 0.41))
FACE_T = int(os.environ.get('FACE_T', 1250)); HELM_T = int(os.environ.get('HELM_T', 420)); HORN_T = int(os.environ.get('HORN_T', 300))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=IN)
o = next(x for x in bpy.data.objects if x.type == 'MESH')
Mw = o.matrix_world.copy()
for x in list(bpy.data.objects):
    if x is not o: bpy.data.objects.remove(x)
o.parent = None; o.matrix_world = Mw; o.name = 'Raw'
bpy.context.view_layer.objects.active = o; o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = o.data; me.materials.clear()
b = bmesh.new(); b.from_mesh(me); bmesh.ops.remove_doubles(b, verts=b.verts, dist=1e-6); b.to_mesh(me); b.free()
P = np.array([tuple(v.co) for v in me.vertices]) * S
for v, p in zip(me.vertices, P): v.co = Vector(p)
n = len(P)
nbr = [[] for _ in range(n)]
for e in me.edges:
    a, c = e.vertices; nbr[a].append(c); nbr[c].append(a)
comp = -np.ones(n, int); c_ = 0
for i in range(n):
    if comp[i] >= 0: continue
    st = [i]; comp[i] = c_
    while st:
        x = st.pop()
        for y in nbr[x]:
            if comp[y] < 0: comp[y] = c_; st.append(y)
    c_ += 1
order = np.argsort(-np.bincount(comp))
print('COMPS', [(int((comp == c).sum()), P[comp == c].min(0).round(3).tolist(), P[comp == c].max(0).round(3).tolist()) for c in order])
GROUPS = {'Face': [order[0], order[5]], 'Helm': [order[1]], 'Horns': [order[2], order[3], order[4]], 'Eyes': [order[6], order[7]]}
for k, cs in GROUPS.items():
    d = o.copy(); d.data = me.copy(); d.name = k; bpy.context.scene.collection.objects.link(d)
    b = bmesh.new(); b.from_mesh(d.data); b.verts.ensure_lookup_table()
    keep = np.isin(comp, cs)
    bmesh.ops.delete(b, geom=[v for v in b.verts if not keep[v.index]], context='VERTS')
    b.to_mesh(d.data); b.free()
bpy.data.objects.remove(o)
def select(x):
    for y in bpy.data.objects: y.select_set(y is x)
    bpy.context.view_layer.objects.active = x
def halve(ob):
    b = bmesh.new(); b.from_mesh(ob.data)
    bmesh.ops.bisect_plane(b, geom=b.verts[:] + b.edges[:] + b.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True, dist=1e-5)
    for v in b.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    b.to_mesh(ob.data); b.free()
def mirror(ob):
    b = bmesh.new(); b.from_mesh(ob.data)
    for v in b.verts:
        if abs(v.co.x) < 3e-4: v.co.x = 0
    bmesh.ops.mirror(b, geom=b.verts[:] + b.edges[:] + b.faces[:], axis='X', merge_dist=3e-4)
    bmesh.ops.triangulate(b, faces=[f for f in b.faces if len(f.verts) > 3])
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    b.to_mesh(ob.data); b.free()
def decimate(ob, tris, wf=None, factor=2.5):
    select(ob)
    b = bmesh.new(); b.from_mesh(ob.data); bmesh.ops.triangulate(b, faces=b.faces); b.to_mesh(ob.data); b.free()
    while len(ob.data.polygons) > 40000:
        st = ob.modifiers.new('St', 'DECIMATE'); st.ratio = 0.3; st.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='St')
    g = ob.vertex_groups.new(name='keep')
    for v in ob.data.vertices:
        g.add([v.index], 1.0 if abs(v.co.x) < 1e-5 else (wf(v.co) if wf else 0.0), 'REPLACE')
    d = ob.modifiers.new('D', 'DECIMATE'); d.ratio = min(1.0, tris / max(1, len(ob.data.polygons))); d.use_collapse_triangulate = True
    d.vertex_group = 'keep'; d.invert_vertex_group = True; d.vertex_group_factor = factor
    bpy.ops.object.modifier_apply(modifier='D'); ob.vertex_groups.clear()
# Face: Meshy's shell (open behind, inside the helmet), right half mirrored
Fc = bpy.data.objects['Face']
halve(Fc)
def face_w(c):
    # eyes, nose, mouth corners and the brow keep detail; the beard and the hidden skull go first
    return 0.75 if (-0.17 < c.y < -0.045 and -0.06 < c.z < 0.03 and abs(c.x) < 0.075) else (0.3 if c.y < -0.02 and c.z > -0.2 else 0.0)
decimate(Fc, FACE_T, face_w, 3.0); mirror(Fc)
for nm, tris in (('Helm', HELM_T), ('Horns', HORN_T)):
    ob = bpy.data.objects[nm]
    halve(ob)
    n0 = len(ob.data.polygons)
    decimate(ob, tris, None); mirror(ob)
    print('OBJ reduce', nm, n0, len(ob.data.polygons))
Ey = bpy.data.objects['Eyes']
halve(Ey); decimate(Ey, 40, None); mirror(Ey)
for ob in bpy.data.objects:
    for p in ob.data.polygons: p.use_smooth = True
    b = bmesh.new(); b.from_mesh(ob.data); bd = sum(1 for e in b.edges if e.is_boundary); b.free()
    q = np.array([v.co[:] for v in ob.data.vertices])
    print('OBJ', ob.name, len(q), len(ob.data.polygons), 'boundary', bd, q.min(0).round(3).tolist(), q.max(0).round(3).tolist())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('OBJ saved')
