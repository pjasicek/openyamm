"""Installed MM6 Demon source GLB -> work/source.blend with the names the ladder expects (Body, Rig); the ash-remains
mesh is kept hidden (the user will replace that effect). glTF splits vertices at every UV/normal seam, so exact
duplicates are welded (UVs stay per face corner); otherwise every seam is an open edge the decimation cannot cross.
Prints size and clip list."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'assets_source/worlds/mm6/models/mm6_demon.glb'))
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Demon_Native_Mesh'))
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body.name = 'Body'; rig.name = 'Rig'
for o in bpy.data.objects:
    if o.type == 'MESH' and o is not body:
        o.hide_render = True; o.hide_viewport = True
import bmesh
bm = bmesh.new(); bm.from_mesh(body.data)
open_before = sum(1 for e in bm.edges if e.is_boundary)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
print('WELD open edges', open_before, '->', sum(1 for e in bm.edges if e.is_boundary), 'verts', len(bm.verts))
bm.to_mesh(body.data); bm.free(); body.data.update()
dims = body.dimensions; bpy.context.view_layer.update()
import mathutils
pts = [body.matrix_world @ mathutils.Vector(c) for c in body.bound_box]
print('SIZE', [round(max(p[k] for p in pts) - min(p[k] for p in pts), 3) for k in range(3)])
print('TRIS', sum(len(p.vertices) - 2 for p in body.data.polygons), 'MATS', [m.name for m in body.data.materials])
print('ACTIONS', [(a.name, tuple(a.frame_range)) for a in bpy.data.actions])
print('UV', [u.name for u in body.data.uv_layers], 'ATTR', [a.name for a in body.data.attributes if not a.name.startswith('.')])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
