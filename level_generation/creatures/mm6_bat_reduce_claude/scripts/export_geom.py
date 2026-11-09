"""work/uv_master.blend (fixed holes and fangs, fresh UVs) + rig -> work/geom_export.glb: skinned geometry only
(4 influences, no clips, no images) for swap_lod0.py."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'uv_master.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Bat']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'geom_export.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in body.data.polygons), [m.name for m in body.data.materials])
