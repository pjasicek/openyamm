"""Re-key one sea serpent clip with ../mm6_seas_claude/scripts/anim_seas.py on the master (open
../mm6_seas_claude/work/anim_v1.blend, never saved) and export the rig with every action using export_glb.py's
glTF settings: the donor for transplant_clip.py.
Usage: blender -b ../mm6_seas_claude/work/anim_v1.blend -P attack_donor.py -- <out.glb> <clip> <function>"""
import bpy, os, sys
out, clip, fn = sys.argv[sys.argv.index('--') + 1:][:3]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'mm6_seas_claude', 'scripts'))
import anim_seas  # noqa: E402
anim_seas.key_action(clip, 1.125, False, getattr(anim_seas, fn))
rig = bpy.data.objects['Seas_Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
rig.animation_data.action = bpy.data.actions['Standing']; bpy.context.scene.frame_set(0)
for o in bpy.data.objects:
    o.select_set(o is rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), use_selection=True, export_format='GLB', export_yup=True,
                          export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                          export_frame_step=1, export_skins=True, export_all_influences=False,
                          export_attributes=False, export_morph=False, export_reset_pose_bones=True,
                          export_anim_slide_to_zero=True)
print('DONOR', out, clip, fn)
