"""Meshy Smart Topology body -> runtime-scale crystal mesh: one object, native height 1.877637 m (the installed
binding's scale stays valid), soles at z = 0, facing -Y (glTF +Z), centred between the feet; welded, loose
specks removed, decimated to TARGET triangles with X symmetry, flat shaded.
Usage: blender -b -P prep_mesh.py -- <in.glb> <out.blend> <target tris>"""
import os, sys, bpy, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]; src, dst, target = a[0], a[1], int(a[2])
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEIGHT = 1.877637
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.join(P, src))
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in list(bpy.data.objects):
    if o != body:
        bpy.data.objects.remove(o)
body.name = 'CrystalWalker'; body.data.name = 'CrystalWalker'
me = body.data
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
# loose specks
seen = set(); comps = []
for f in bm.faces:
    if f in seen:
        continue
    stack = [f]; comp = []; seen.add(f)
    while stack:
        g = stack.pop(); comp.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h not in seen:
                    seen.add(h); stack.append(h)
    comps.append(comp)
comps.sort(key=len, reverse=True)
small = [f for c in comps[1:] if len(c) < 30 for f in c]
print('COMPONENTS', [len(c) for c in comps[:8]], 'removed faces', len(small))
bmesh.ops.delete(bm, geom=small, context='FACES')
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
# scale and place
co = [v.co.copy() for v in me.vertices]
zmin = min(c.z for c in co); zmax = max(c.z for c in co); s = HEIGHT / (zmax - zmin)
feet = [c for c in co if c.z < zmin + 0.05 * (zmax - zmin)]
cx = (min(c.x for c in co) + max(c.x for c in co)) / 2; cy = sum(c.y for c in feet) / len(feet)
me.transform(Matrix.Translation((-cx * s, -cy * s, -zmin * s)) @ Matrix.Scale(s, 4))
me.update()
before = sum(len(p.vertices) - 2 for p in me.polygons)
mod = body.modifiers.new('dec', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
mod.ratio = target / before; mod.use_symmetry = True; mod.symmetry_axis = 'X'; mod.use_collapse_triangulate = True
bpy.context.view_layer.objects.active = body; bpy.ops.object.modifier_apply(modifier='dec')
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges)
bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = False
co = [v.co for v in me.vertices]
print('PREP tris', before, '->', sum(len(p.vertices) - 2 for p in me.polygons), 'scale', round(s, 4),
      'bounds', tuple(round(min(getattr(c, k) for c in co), 3) for k in 'xyz'),
      tuple(round(max(getattr(c, k) for c in co), 3) for k in 'xyz'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, dst))
bpy.ops.export_scene.gltf(filepath=os.path.join(P, dst.replace('.blend', '.glb')), export_format='GLB',
                          export_materials='NONE', export_yup=True)
