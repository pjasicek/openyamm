"""Reduced candidate (work/ladder.blend, REA_CAND, default Cand_55) + rig -> work/cand_export.glb: skinned geometry
only (4 influences, 8 with REA_INFLUENCES=8; no clips), the mesh node named like the installed one so swap_lod0.py can check transforms.
Shading: smooth (default; the reduced faces share vertices, about a quarter of the flat vertex data), or flat
like the Batch E export (every triangle its own face normal) with REA_FLAT=1."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_BLEND', 'ladder.blend')))
rig = bpy.data.objects['Rig']; cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_55')]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
g = cand.vertex_groups.get('ReduceProtect')
if g:
    cand.vertex_groups.remove(g)
# soles: the collapse placed a few new sole vertices up to 1.8 mm under the rest floor (source soles sit at z = 0 and
# the Standing/Walking sole gate is 0.0 cm); keeping the sole faces exactly took budget from the torso and failed the
# ladder, so new vertices below the floor are lifted onto it (rest pose = bind pose)
low = 0  # giant: soles kept exactly; the floor lift of the source scripts assumed a mesh-space floor at z = 0
for poly in cand.data.polygons:
    poly.use_smooth = os.environ.get('REA_FLAT', '0') != '1'
# giant: the mallet's hard-surface head keeps sharp edges by angle as its own export did (export_giant.py: edges
# between two mallet faces over 0.75 rad); body and head stay smooth as the source
import bmesh
mi = [i for i, m in enumerate(cand.data.materials) if 'Mallet' in m.name]
if mi:
    bm = bmesh.new(); bm.from_mesh(cand.data); nsh = 0
    for e in bm.edges:
        if len(e.link_faces) == 2 and all(f.material_index == mi[0] for f in e.link_faces) and e.calc_face_angle(0) > 0.75:
            e.smooth = False; nsh += 1
    bm.to_mesh(cand.data); bm.free(); print('SHARP mallet edges', nsh)
bpy.data.objects['Body'].name = 'Source_Body'; cand.name = os.environ.get('REA_NODE', 'Demon_Native_Mesh')
bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'cand_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=os.environ.get('REA_INFLUENCES', '4') == '8',
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in cand.data.polygons))
