"""Reduced candidate (work/ladder.blend, REA_CAND, default Cand_55) + rig -> work/cand_export.glb: skinned geometry
only (4 influences, no clips), the mesh node named like the installed one so swap_lod0.py can check transforms."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', os.environ.get('REA_LADDER', 'ladder.blend')))
rig = bpy.data.objects['Rig']; cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_55')]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
g = cand.vertex_groups.get('ReduceProtect')
if g:
    cand.vertex_groups.remove(g)
if os.environ.get('REA_NORMALS', '1') == '1':
    # dru1: the installed hair shell carries outward scalp normals (review 5: black forehead otherwise); transfer the
    # source's custom normals per corner instead of recomputing smooth ones
    src = bpy.data.objects['Body']; tmp = src.copy(); tmp.data = src.data.copy(); bpy.context.scene.collection.objects.link(tmp)
    for m in list(tmp.modifiers):
        tmp.modifiers.remove(m)
    arm = [m for m in cand.modifiers if m.type == 'ARMATURE']
    for m in arm:
        cand.modifiers.remove(m)
    dt = cand.modifiers.new('N', 'DATA_TRANSFER'); dt.object = tmp; dt.use_loop_data = True
    dt.data_types_loops = {'CUSTOM_NORMAL'}; dt.loop_mapping = 'POLYINTERP_NEAREST'; dt.use_object_transform = False
    bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); bpy.context.view_layer.objects.active = cand
    bpy.ops.object.modifier_apply(modifier=dt.name)
    bpy.data.objects.remove(tmp, do_unlink=True)
    a = cand.modifiers.new('Armature', 'ARMATURE'); a.object = rig
    print('NORMALS transferred', cand.data.has_custom_normals)
bpy.data.objects['Body'].name = 'Source_Body'; cand.name = os.environ.get('REA_NODE', 'Demon_Native_Mesh')
for o in (cand, rig):
    o.hide_set(False); o.hide_viewport = False  # head_uv.blend saved them hidden
bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'cand_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in cand.data.polygons))
