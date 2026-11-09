"""Gate scene from a runtime GLB (source or reduced, the same path for both): LOD0 mesh node 'Golem' -> 'Body', armature
-> 'Rig', exact duplicates with identical weights welded (glTF splits vertices at UV seams; the gates need connected
edges and a closed skin), point attribute 'garment' = connected piece rank (0 = the largest piece: the closed skin, as
in the source project's garment labels; every other piece is an open shell or ornament for the contact probes).
Usage: blender -b -P gate_blend.py -- <glb> <out.blend>"""
import os, sys, bpy, bmesh
glb, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'Golem')
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o is not body]:
    bpy.data.objects.remove(o)
body.name = 'Body'; rig.name = 'Rig'
bm = bmesh.new(); bm.from_mesh(body.data); dl = bm.verts.layers.deform.active
sig = lambda v: tuple(sorted((g, round(w, 4)) for g, w in v[dl].items())) if dl else ()
classes = {}
for v in bm.verts:
    classes.setdefault(sig(v), []).append(v)
for vs in classes.values():
    bmesh.ops.remove_doubles(bm, verts=vs, dist=1e-6)
bm.verts.ensure_lookup_table()
# connected pieces by size
lab = [-1] * len(bm.verts); pieces = []
for v in bm.verts:
    if lab[v.index] >= 0:
        continue
    stack = [v]; lab[v.index] = len(pieces); n = 0
    while stack:
        x = stack.pop(); n += 1
        for e in x.link_edges:
            y = e.other_vert(x)
            if lab[y.index] < 0:
                lab[y.index] = len(pieces); stack.append(y)
    pieces.append(n)
rank = {p: r for r, p in enumerate(sorted(range(len(pieces)), key=lambda p: -pieces[p]))}
bm.to_mesh(body.data); bm.free()
a = body.data.attributes.new('garment', 'INT', 'POINT'); a.data.foreach_set('value', [rank[x] for x in lab])
print('GATEBLEND', glb, 'verts', len(body.data.vertices), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons),
      'pieces', len(pieces), 'skin verts', max(pieces), 'open edges', sum(1 for e in body.data.edges if False))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
