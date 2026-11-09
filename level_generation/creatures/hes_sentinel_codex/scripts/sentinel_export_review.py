"""Render the exported neutral GLB's real clip samples, independent of the authoring scene."""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=str(P / 'review/sentinel_rig_preview.glb'))
rig = next(o for o in scene.objects if o.type == 'ARMATURE')
for track in rig.animation_data.nla_tracks:
    track.mute = True
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.65, 0.65, 0.63); scene.display.shading.show_cavity = True
scene.render.resolution_x = scene.render.resolution_y = 700; scene.render.resolution_percentage = 100
scene.render.film_transparent = True
cam = bpy.data.objects.new('ReviewCam', bpy.data.cameras.new('ReviewCam')); scene.collection.objects.link(cam)
scene.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.35
samples = [('Standing', 0), ('Standing', 1.5), ('Standing', 4.5), ('Attack', 5/30),
           ('Hit', 2/30), ('Death', .8), ('Death', 1.2), ('Dead', 0)]
report = []
for i, (name, time) in enumerate(samples):
    action = next(a for a in bpy.data.actions if a.name == name or a.name.startswith(name + '_'))
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    frame = time * 30; scene.frame_set(int(frame), subframe=frame - int(frame))
    for view, (az, el) in {'q': (-35, 15), 'side': (90, 0)}.items():
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = Vector((0, .1, .8)) + d * 9
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        path = P / 'review/sentinel_geometry' / f'export_{i:02d}_{name}_{view}.png'
        scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)
        assert path.is_file()
        report.append({'clip': name, 'seconds': time, 'view': view, 'path': str(path.relative_to(P))})
(P / 'review/sentinel_geometry/export_stills.json').write_text(json.dumps(report, indent=2) + '\n')
print('EXPORTED_CLIPS_RENDERED', len(report), flush=True)
