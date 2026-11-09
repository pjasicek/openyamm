"""Run in a fresh background Blender to turn the isolated scene library into a normal editable project."""
import bpy
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack')
with bpy.data.libraries.load('/tmp/openyamm_goblin_sword_scene.blend',link=False) as (data_from,data_to):
    data_to.scenes=['Meshy Goblin Sword and Native Attack']
scene=data_to.scenes[0]
for window in bpy.context.window_manager.windows:window.scene=scene
for other in list(bpy.data.scenes):
    if other!=scene:bpy.data.scenes.remove(other)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'goblin_sword.blend'))
