"""Animation-only GLB of one clip of work/rig_textured_fit_attack_v2.blend, with export_runtime.py's 60-fps
scaling and glTF settings, for transplanting into the runtime body: args <action> <out.glb relative to project>."""
import bpy, sys
from pathlib import Path
from mathutils import Matrix
args = sys.argv[sys.argv.index('--') + 1:]
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/rig_textured_fit_attack_v2.blend'))
r = bpy.data.objects['Rig']; r.animation_data.action = None
for pb in r.pose.bones: pb.matrix_basis = Matrix()
keep = bpy.data.actions[args[0]]
for a in list(bpy.data.actions):
    if a is not keep: bpy.data.actions.remove(a)
keep.name = 'Attack'
for layer in keep.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fc in bag.fcurves:
                for k in fc.keyframe_points:
                    k.co.x *= 2; k.handle_left.x *= 2; k.handle_right.x *= 2; k.interpolation = 'LINEAR'
                fc.update()
keep.frame_start *= 2; keep.frame_end *= 2
sc = bpy.context.scene; sc.render.fps = 60; sc.render.fps_base = 1
r.data.bones['Socket_Sword'].use_deform = True
for o in bpy.data.objects: o.select_set(o in (r, bpy.data.objects['Body']))
bpy.context.view_layer.objects.active = r
bpy.ops.export_scene.gltf(filepath=str(P / args[1]), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False, export_attributes=False,
                          export_morph=False, export_materials='NONE', export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True, export_extras=False)
print('EXPORTED', args)
