"""Reduced candidate (work/ladder.blend, REA_CAND, default Cand_55) + rig -> work/cand_export.glb: skinned geometry
only (4 influences, 8 with REA_INFLUENCES=8; no clips), the mesh node named like the installed one so swap_lod0.py can check transforms."""
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
bpy.data.objects['Body'].name = 'Source_Body'
node = os.environ.get('REA_NODE', 'Demon_Native_Mesh')
if node in bpy.data.objects:  # m608: the imported node of that name (an empty or a hidden mesh) holds it
    bpy.data.objects[node].name = node + '_taken'
cand.name = node; assert cand.name == node, cand.name
# m608: the installed body shades smooth up to 45 degrees (97.6 % of its hard edges, split_angle.py); the rubble
# shards are flat. REA_SHADE=angle:<deg> | flat
shade = os.environ.get('REA_SHADE', '')
if shade:
    import math
    bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); bpy.context.view_layer.objects.active = cand
    if shade == 'flat':
        bpy.ops.object.shade_flat()
    else:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(float(shade.split(':')[1])), keep_sharp_edges=False)
    for m in [m for m in cand.modifiers if m.type == 'NODES']:
        bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'cand_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=os.environ.get('REA_INFLUENCES', '4') == '8',
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in cand.data.polygons))
