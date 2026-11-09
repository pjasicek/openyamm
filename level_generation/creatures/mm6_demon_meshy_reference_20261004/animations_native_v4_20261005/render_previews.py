"""Render the actual delivered GLB, including morphs and visibility, for visual review."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

stage = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(stage/'mm6_demon_native_animations.blend'))
source = bpy.context.scene
scene = bpy.data.scenes.new('Native_Actual_GLB_Review')
scene.render.fps = 48
bpy.context.window.scene = scene
bpy.ops.import_scene.gltf(filepath=str(stage/'mm6_demon_native_animations.glb'))
for obj in scene.objects:
    if obj.type == 'ARMATURE':
        obj.hide_render = True
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 760
scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 92
scene.world = source.world
scene.view_settings.view_transform = source.view_settings.view_transform
shading = scene.display.shading
shading.light = 'STUDIO'
shading.color_type = 'MATERIAL'
shading.show_shadows = False
shading.show_cavity = True
shading.cavity_type = 'BOTH'
shading.background_type = 'WORLD'
camera = bpy.data.objects.new('Preview_Camera', bpy.data.cameras.new('Preview_Camera'))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.55
study = json.loads((stage.parent/'animation_study/animation_motion_spec.json').read_text())
clips = {'Standing': ('standing', 6), 'Walk_Native': ('walk', 54), 'Hit': ('hit', 36),
         'Fidget': ('fidget', 30), 'Death': ('death', 60), 'Ash_Remains': ('corpse', 6), 'Attack': ('attack', 36)}
output = stage/'preview_frames'
output.mkdir(exist_ok=True)
rendered = []


def select(clip, frame, selected_scene=None):
    selected_scene = scene if selected_scene is None else selected_scene
    bpy.context.window.scene = selected_scene
    for obj in selected_scene.objects:
        for owner in (obj, obj.data.shape_keys if obj.type == 'MESH' else None):
            if owner is not None and owner.animation_data:
                matching = [t.strips[0] for t in owner.animation_data.nla_tracks if t.name == clip]
                for track in owner.animation_data.nla_tracks:
                    track.mute = True
                # glTF actions start at sample zero; Blender places imported NLA strips at frame one.
                owner.animation_data.action = matching[0].action if matching else None
                if matching:
                    owner.animation_data.action_slot = matching[0].action_slot
    selected_scene.frame_set(frame)


for clip, (native, end) in clips.items():
    anchors = list(range(0, 36, 6)) if clip == 'Attack' else [a['sample'] for a in study['clips'][native]['anchors']]
    frames = list(range(end+1)) if end > 6 else [0]
    for view, direction in [('front', (0, -6, 0)), ('profile', (-6, 0, 0))]:
        center = Vector((0, 0, .91))
        camera.location = center+Vector(direction)
        camera.rotation_euler = (-Vector(direction)).to_track_quat('-Z', 'Y').to_euler()
        for frame in frames:
            select(clip, frame)
            name = f'{clip}_{view}_{frame:02d}.jpg'
            scene.render.filepath = str(output/name)
            bpy.ops.render.render(write_still=True)
            rendered.append(name)
        print('Rendered actual GLB', clip, view, len(frames), flush=True)
    # The opposite oblique view catches palm/claw order and depth occlusion at source extrema.
    center = Vector((0, 0, .91))
    direction = Vector((-3, -6, .3))
    camera.location = center+direction
    camera.rotation_euler = (-direction).to_track_quat('-Z', 'Y').to_euler()
    for frame in anchors:
        select(clip, frame)
        name = f'{clip}_oblique_{frame:02d}.jpg'
        scene.render.filepath = str(output/name)
        bpy.ops.render.render(write_still=True)
        rendered.append(name)
with bpy.data.libraries.load(str(stage.parent/'animations_native_v3_20261005/mm6_demon_native_animations.blend')) as (available, loaded):
    loaded.scenes = ['MM6_Demon_Native_Animations']
previous = loaded.scenes[0]
previous.collection.objects.link(camera)
previous.camera = camera
head_output = stage/'head_review_frames'
head_output.mkdir(exist_ok=True)
head_rendered = []
for selected_scene, prefix in [(scene, 'after'), (previous, 'before')]:
    selected_scene.render.engine = 'BLENDER_WORKBENCH'
    selected_scene.render.resolution_x = selected_scene.render.resolution_y = 1000
    selected_scene.render.resolution_percentage = 100
    selected_scene.render.image_settings.file_format = 'JPEG'
    selected_scene.render.image_settings.quality = 94
    selected_scene.world = scene.world
    selected_scene.view_settings.view_transform = scene.view_settings.view_transform
    selected_scene.display.shading.light = 'STUDIO'
    selected_scene.display.shading.color_type = 'MATERIAL'
    selected_scene.display.shading.show_shadows = False
    selected_scene.display.shading.show_cavity = True
    selected_scene.display.shading.cavity_type = 'BOTH'
    selected_scene.display.shading.background_type = 'WORLD'
    for clip, frame in [('Standing',0), ('Walk_Native',15), ('Attack',12), ('Hit',18), ('Fidget',18)]:
        directions = [('front',(0,-6,0)), ('profile',(-6,0,0)), ('oblique',(-3,-6,.15))]
        if clip == 'Standing':
            directions.append(('back',(0,6,0)))
        for view, direction in directions:
            center = Vector((0,-.25,1.62))
            direction = Vector(direction)
            camera.location = center+direction
            camera.rotation_euler = (-direction).to_track_quat('-Z','Y').to_euler()
            camera.data.ortho_scale = .50
            select(clip, frame, selected_scene)
            name = f'{prefix}_{clip}_{view}.jpg'
            selected_scene.render.filepath = str(head_output/name)
            bpy.ops.render.render(write_still=True)
            head_rendered.append(name)
(stage/'visual_render_manifest.json').write_text(json.dumps(dict(
    actual_glb_reimport=True, rendered=rendered, source_anchors_and_48fps_inbetweens=True,
    head_renders=head_rendered, head_before_source='Previous revision 3 Blender project',
    head_after_source='Actual exported revision 4 GLB', identical_head_cameras=True,
    shading='Untextured clay body; native-inspired pink/dark effect material colours'), indent=2)+'\n')
print('Rendered', len(rendered), 'actual exported poses.', flush=True)
