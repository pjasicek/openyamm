"""work/gob_master.blend Body (two materials: Goblin_A body, GoblinHead_A head) + Rig, rest pose, no clips ->
work/master_export.glb, the mesh node named like the installed one (Goblin) for assemble_gob.py."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'gob_master.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
body.name = 'Goblin'
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', 'master_export.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_animations=False, export_skins=True,
                          export_all_influences=False, export_attributes=False, export_morph=False,
                          export_image_format='NONE')
print('EXPORTED', sum(len(p.vertices) - 2 for p in body.data.polygons))
