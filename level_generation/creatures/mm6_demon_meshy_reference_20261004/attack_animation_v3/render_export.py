"""Render actual exported glTF geometry/actions without modifying either delivered asset."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

stage = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(stage / 'mm6_demon_attack.blend'))
source = bpy.context.scene
scene = bpy.data.scenes.new('Actual_GLB_Visual_Review')
scene.render.fps = 48
bpy.context.window.scene = scene
bpy.ops.import_scene.gltf(filepath=str(stage / 'mm6_demon_attack.glb'))
rig = next(obj for obj in scene.objects if obj.type == 'ARMATURE')
mesh = next(obj for obj in scene.objects if obj.type == 'MESH')
actions = {track.name: track.strips[0].action for track in rig.animation_data.nla_tracks}
for track in rig.animation_data.nla_tracks:
    track.mute = True
rig.animation_data.action = actions['Attack']
rig.animation_data.action_slot = actions['Attack'].slots[0]
rig.hide_render = True
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1300
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.fps = 48
scene.world = source.world
scene.view_settings.view_transform = source.view_settings.view_transform
shading = scene.display.shading
shading.light = 'STUDIO'
shading.color_type = 'SINGLE'
shading.single_color = (.62, .66, .7)
shading.show_shadows = False
shading.show_cavity = True
shading.cavity_type = 'BOTH'
camera = bpy.data.objects.new('Actual_GLB_Review_Camera', bpy.data.cameras.new('Actual_GLB_Review_Camera'))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = 'ORTHO'
output = stage / 'export_review_frames'
output.mkdir(exist_ok=True)
rendered = []
views = [('front', (0, -6, 0), 2.35, [0, 12, 18, 24, 30, 36]),
         ('side', (-6, 0, 0), 2.35, [12, 24]),
         ('threequarter', (3, -6, .2), 2.75, [0, 6, 12, 18, 24, 30, 36]),
         ('opposite_threequarter', (-3, -6, .2), 2.75, [0, 6, 12, 18, 24, 30, 36])]
for name, direction, scale, times in views:
    center = Vector((0, -.10, .86))
    camera.location = center + Vector(direction)
    camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = scale
    for time in times:
        scene.frame_set(time)
        path = output / f'{name}_{time:02d}.png'
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path.relative_to(stage)))
(stage / 'export_visual_review.json').write_text(json.dumps({
    'actual_glb_reimport': True, 'rendered_images': rendered,
    'texture_scope': 'untextured geometry and skinning review',
    'view_note': 'Three-quarter camera uses a common wider crop to include the entire claw sweep.',
}, indent=2) + '\n')
print('Rendered', len(rendered), 'actual GLB poses; final GLB and Blender files were read only.')
