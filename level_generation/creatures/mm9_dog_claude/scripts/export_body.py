"""Export the 'Body' of a blend (bind pose, no skin, no materials) as a GLB for the next fit_quad.py pass.
Args: <blend> <out glb>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if arm is not None:
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
body = bpy.data.objects['Body']
body.modifiers.clear()
mw = body.matrix_world.copy()
body.parent = None
body.matrix_world = mw
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.gltf(filepath=argv[1], use_selection=True, export_format='GLB', export_yup=True,
                          export_materials='NONE', export_skins=False, export_animations=False, export_attributes=False)
print('EXPORTED', argv[1], len(body.data.vertices))
