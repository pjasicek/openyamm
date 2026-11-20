"""Export the source (100 %) and the picked reduction step from work/ladder.blend with the project's export settings
(export_lizard.py): Body + Rig, all clips -> work/mm6_drag_<tag>_full.glb."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEPS = [x.split(':') for x in os.environ.get('REA_STEPS', 'r100:,r55:Cand_55').split(',')]
for tag, cand in STEPS:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
    rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
    if cand:
        bpy.data.objects.remove(body, do_unlink=True)
        body = bpy.data.objects[cand]; body.name = 'Body'
    g = body.vertex_groups.get('ReduceProtect')
    if g: body.vertex_groups.remove(g)
    body.hide_render = False
    rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.render.fps = 24; bpy.context.scene.frame_set(0)
    for ob in bpy.data.objects: ob.select_set(ob in [body, rig])
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', f'mm6_drag_{tag}_full.glb'), use_selection=True,
        export_format='GLB', export_yup=True, export_animations=True, export_animation_mode='ACTIONS',
        export_force_sampling=True, export_frame_step=1, export_skins=True, export_all_influences=False,
        export_attributes=False, export_morph=False, export_image_format='AUTO', export_reset_pose_bones=True,
        export_anim_slide_to_zero=True)
    print('EXPORTED', tag, sum(len(p.vertices) - 2 for p in body.data.polygons))
