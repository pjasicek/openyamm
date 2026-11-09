"""Run through Blender MCP after native build: one reimport for automap and focused views."""
from pathlib import Path
import bpy
from mathutils import Vector

project=Path('/home/pjasicek/github/OpenYAMM/level_generation/projects/brackenford_greywatch')
previous_name=bpy.context.window.scene.name
try:
    exec(compile((project/'build_minimap_blender.py').read_text(),str(project/'build_minimap_blender.py'),'exec'))
    scene.render.image_settings.file_format='PNG'
    scene.render.resolution_x=1440;scene.render.resolution_y=1080
    for name,target,position,scale in [
        ('frontage_overview',(-11900,800,750),(-20500,-18500,24000),20700),
        ('frontage_court',(-9100,-800,800),(-4000,-8000,8000),8700),
        ('frontage_west',(-15800,0,700),(-20700,-6200,7300),10500)]:
        camera.location=Vector(position)/128
        camera.rotation_euler=(Vector(target)/128-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale=scale/128
        for obj in billboards:
            obj.hide_render=False
            direction=camera.location-obj.location;direction.z=0
            obj.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
        scene.render.filepath=str(project/'review'/('brackenford_native_'+name+'.png'))
        bpy.ops.render.render(write_still=True)
finally:
    previous_scene=bpy.data.scenes.get(previous_name)
    if previous_scene:bpy.context.window.scene=previous_scene
print('Native frontage overview, court, west street and automap saved.')
