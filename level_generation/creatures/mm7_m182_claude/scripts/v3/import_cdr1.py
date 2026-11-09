"""work/v3/cdr1_installed.glb (copy of the installed MM6 cdr1, sha bb4effe1...) -> work/v3/src.blend with Body + Rig,
duplicate seam vertices welded (UVs stay per corner), LOD/shadow meshes removed. Prints sizes, clips, materials."""
import os, bpy, bmesh
P = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(P, 'work/v3/cdr1_installed.glb'))
body = bpy.data.objects['Body']; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); rig.name = 'Rig'
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body:
        bpy.data.objects.remove(o, do_unlink=True)
bm = bmesh.new(); bm.from_mesh(body.data)
ob = sum(1 for e in bm.edges if e.is_boundary)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
print('WELD open edges', ob, '->', sum(1 for e in bm.edges if e.is_boundary), 'verts', len(bm.verts))
bm.to_mesh(body.data); bm.free()
print('TRIS', sum(len(p.vertices) - 2 for p in body.data.polygons), 'MATS', [m.name for m in body.data.materials])
print('ACTIONS', [(a.name, tuple(a.frame_range)) for a in bpy.data.actions])
print('BODY', body.parent.name if body.parent else None, tuple(body.matrix_world.translation), tuple(body.rotation_euler), 'RIG', tuple(rig.rotation_euler), tuple(rig.scale))
print('FPS', bpy.context.scene.render.fps)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, 'work/v3/src.blend'))
