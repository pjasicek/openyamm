"""Reduced candidate (work/ladder.blend, REA_CAND, default Cand_55) + rig -> work/cand_export.glb: skinned geometry
only (4 influences, 8 with REA_INFLUENCES=8; no clips), the mesh node named like the installed one so swap_lod0.py can check transforms.
MM7 Griffin: the project export shades 93 % of its faces flat (Meshy's facets, carried by uv_export.py). Default:
smooth shading (batch decision, as the Rat reduction: about a quarter of the vertex data, textured nearly the same).
REA_FLAT=1: each candidate face takes the smooth/flat flag of the nearest source face (rest pose, by centroid) so the
reduced model shades like the accepted one. Output: work/cand_export.glb (REA_OUT overrides)."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
rig = bpy.data.objects['Rig']; cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_55')]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
import numpy as np
from mathutils.kdtree import KDTree
src = bpy.data.objects['Body']; t = KDTree(len(src.data.polygons))
for p in src.data.polygons:
    t.insert(p.center, p.index)
t.balance()
FLAT = os.environ.get('REA_FLAT') == '1'
for p in cand.data.polygons:
    p.use_smooth = src.data.polygons[t.find(p.center)[1]].use_smooth if FLAT else True
print('SHADE flat faces', sum(not p.use_smooth for p in cand.data.polygons), 'of', len(cand.data.polygons))
g = cand.vertex_groups.get('ReduceProtect')
if g:
    cand.vertex_groups.remove(g)
bpy.data.objects['Body'].name = 'Source_Body'; cand.name = os.environ.get('REA_NODE', 'Demon_Native_Mesh')
bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', os.environ.get('REA_OUT', 'cand_export.glb')), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=os.environ.get('REA_INFLUENCES', '4') == '8',
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in cand.data.polygons))
