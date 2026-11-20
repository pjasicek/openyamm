"""Normalize the isolated animation library into an ordinary inspectable WIP .blend in background Blender."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'animations/manifest.json').read_text())
scene=bpy.data.scenes[manifest['scene']]
for window in bpy.context.window_manager.windows:window.scene=scene
rig=next(o for o in scene.objects if o.type=='ARMATURE')
for obj in scene.objects:obj.select_set(False)
rig.select_set(True);scene.view_layers[0].objects.active=rig
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.shading.type='MATERIAL'
            space.region_3d.view_location=(0,0,.98);space.region_3d.view_distance=3.1
            space.region_3d.view_rotation=Vector((.5,1,-.10)).to_track_quat('-Z','Y')
            space.overlay.show_extras=False
note=bpy.data.texts.new('READ ME - working goblin')
note.write('MM6 goblin reconstruction WORK IN PROGRESS.\n'
    'Seven draft clips are available in the Action Editor: Standing, Walk, Attack, Hit, Death, Corpse, Fidget.\n'
    'Select Goblin RIG for posing. To pose manually, unlink its active Action and reset pose transforms.\n'
    'Materials, joints and motion are still under review; this is not the final portable asset or sprite delivery.\n'
    'Source scripts, references and calibration history are in level_generation/creatures/mm6_goblin/.\n')
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'review/mm6_goblin_working.blend'))
print('Saved ordinary working project with',len(rig.data.bones),'bones and seven draft clips')
