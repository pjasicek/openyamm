"""Reduced candidate (work/ladder.blend, REA_CAND, default Cand_55) + rig -> work/cand_export.glb: skinned geometry
only (4 influences, 8 with REA_INFLUENCES=8; no clips), the mesh node named like the installed one so swap_lod0.py can check transforms.
REA_DOUBLES=<.npy from find_doubles.py>: faces on those positions get their reversed back copy again (two-sided
sheets; the source weld merged each pair, and the faces themselves are kept exactly by the ladder)."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
rig = bpy.data.objects['Rig']; cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_55')]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
g = cand.vertex_groups.get('ReduceProtect')
if g:
    cand.vertex_groups.remove(g)
if os.environ.get('REA_DOUBLES'):
    import bmesh, numpy as np
    keys = {tuple(map(tuple, k)) for k in np.load(os.environ['REA_DOUBLES'])}
    bm = bmesh.new(); bm.from_mesh(cand.data)
    hit = [f for f in bm.faces if tuple(sorted(tuple(np.round(v.co[:], 5)) for v in f.verts)) in keys]
    new = [g for g in bmesh.ops.duplicate(bm, geom=hit)['geom'] if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.reverse_faces(bm, faces=new)
    bm.to_mesh(cand.data); bm.free(); cand.data.update()
    print('DOUBLED', len(hit), 'of', len(keys))
bpy.data.objects['Body'].name = 'Source_Body'; cand.name = os.environ.get('REA_NODE', 'Demon_Native_Mesh')
bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'cand_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=os.environ.get('REA_INFLUENCES', '4') == '8',
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in cand.data.polygons))
